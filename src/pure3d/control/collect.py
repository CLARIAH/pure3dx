from control.files import (
    listDirs,
    listFiles,
    listImages,
    list3d,
    readYaml,
    dirMake,
    dirRemove,
    dirCopy,
    fileCopy,
)
from control.environment import var


META = "meta"
PROJECTS = "projects"
EDITIONS = "editions"
WORKFLOW = "workflow"

SCENE_DEFAULT = "intro"


class Collect:
    def __init__(self, Settings, Messages, Mongo):
        """Provides initial data collection into MongoDb.

        Normally, this does not have to run, since the MongoDb is persistent.
        Only when the MongoDb of the Pure3D app is fresh,
        or when the MongoDb is out of sync with the data on the filesystem
        it must be initialized.

        It reads:

        * configuration data of the app,
        * project data on the file system
        * workflow data on the file system
        * 3D-viewer code on file system

        The project-, workflow, and viewer data should be placed on the same share
        in the file system, by a provision step that is done on the host.

        The data for the supported viewers is in repo `pure3d-data`, under `viewers`.

        For testing, there is `exampledata` in the same `pure3d-data` repo.
        The provision step should copy the contents of `exampledata` to the
        `data` directory of this repo (`pure3dx`).

        If data collection is triggered in test mode, the user table will be wiped,
        and the test users present in the example data will be imported.

        Otherwise the user table will be left unchanged.

        Parameters
        ----------
        Settings: `control.helpers.generic.AttrDict`
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        Mongo: object
            Singleton instance of `control.mongo.Mongo`.
        """
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)
        self.Mongo = Mongo

    def trigger(self):
        """Determines whether data collection should be done.

        We only do data collection if the environment variable `docollect` is "v"
        If so, the value of the environment variable `initdata`
        is the name of a subdirectory of the data directory.
        This subdirectory contains example data that will be imported into the system.

        We also prevent this from happening twice, which occurs when Flask runs
        in debug mode, since then the code is loaded twice.
        We guard against this by inspecting the environment variable
        `WERKZEUG_RUN_MAIN`. If it is set, we are already running the app,
        and data collection should be inhibited, because it has been done
        just before Flask started running.
        """
        doCollect = var("docollect") == "v"
        beforeFlask = var("WERKZEUG_RUN_MAIN") is None

        return beforeFlask and doCollect

    def fetch(self):
        """Performs a data collection, but only if triggered by the right conditions.

        See also `Collect.trigger()`
        """

        if not self.trigger():
            return

        importSubdir = var("initdata") or "exampledata"
        self.importSubdir = importSubdir

        Messages = self.Messages
        Messages.info(logmsg="Collecting data before starting the app")

        self.clearDb()
        self.doOuter()
        self.doProjects()
        self.doWorkflow()

    def clearDb(self):
        """Clears selected collections in the MongoDb.

        All collections that will be filled with data from the filesystem
        will be wiped.

        !!! "Users collection will be wiped in test mode"
            If in test mode, the `users` collection will be wiped,
            and then filled from the example data.
        """
        Settings = self.Settings
        Mongo = self.Mongo

        for table in (
            "meta",
            "projects",
            "editions",
            "scenes",
            "users",
            "projectUsers",
        ):
            Mongo.checkCollection(table, reset=True)

        if Settings.testMode:
            Mongo.checkCollection("users", reset=True)

    def doOuter(self):
        """Collects data not belonging to specific projects."""
        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo

        importSubdir = self.importSubdir
        dataDir = Settings.dataDir
        Messages.plain(logmsg=f"Import metadata from {importSubdir}")

        metaDir = f"{dataDir}/{importSubdir}/{META}"
        metaFiles = listFiles(metaDir, ".yml")
        meta = {}

        for metaFile in metaFiles:
            meta[metaFile] = readYaml(f"{metaDir}/{metaFile}.yml", defaultEmpty=True)

        Mongo.insertItem("meta", name="project", meta=dict(**meta))

    def doProjects(self):
        """Collects data belonging to projects."""
        Settings = self.Settings
        importSubdir = self.importSubdir

        dataDir = Settings.dataDir
        projectsInPath = f"{dataDir}/{importSubdir}/{PROJECTS}"
        projectsOutPath = f"{dataDir}/{PROJECTS}"
        dirRemove(projectsOutPath)

        self.projectIdByName = {}

        projectNames = listDirs(projectsInPath)
        for projectName in projectNames:
            self.doProject(projectsInPath, projectsOutPath, projectName)

    def doProject(self, projectsInPath, projectsOutPath, projectName):
        """Collects data belonging to a specific project.

        Parameters
        ----------
        projectsInPath: string
            Path on the filesystem to the projects input directory
        projectsOutPath: string
            Path on the filesystem to the projects destination directory
        projectName: string
            Directory name of the project to collect.
        """
        Messages = self.Messages
        Mongo = self.Mongo
        projectIdByName = self.projectIdByName

        projectInPath = f"{projectsInPath}/{projectName}"

        meta = {}
        metaDir = f"{projectInPath}/meta"
        metaFiles = listFiles(metaDir, ".yml")

        for metaFile in metaFiles:
            meta[metaFile] = readYaml(f"{metaDir}/{metaFile}.yml", defaultEmpty=True)

        title = meta.get("dc", {}).get("title", projectName)

        candy = {}
        candyInPath = f"{projectInPath}/candy"

        for image in listImages(candyInPath):
            candy[image] = True if image.lower() == "icon.png" else False

        projectInfo = dict(
            title=title,
            meta=meta,
            candy=candy,
        )

        projectId = Mongo.insertItem("projects", **projectInfo)
        projectIdByName[projectName] = projectId
        Messages.plain(logmsg=f"PROJECT {projectName} => {projectId}")
        projectOutPath = f"{projectsOutPath}/{projectId}"
        dirMake(projectOutPath)
        candyOutPath = f"{projectOutPath}/candy"
        dirCopy(candyInPath, candyOutPath)

        self.doEditions(projectInPath, projectOutPath, projectId)

    def doEditions(self, projectInPath, projectOutPath, projectId):
        """Collects data belonging to the editions of a project.

        Parameters
        ----------
        projectInPath: string
            Path on the filesystem to the input directory of this project
        projectOutPath: string
            Path on the filesystem to the destination directory of this project
        projectId: ObjectId
            MongoId of the project to collect.
        """
        editionsInPath = f"{projectInPath}/{EDITIONS}"
        editionsOutPath = f"{projectOutPath}/{EDITIONS}"

        editionNames = listDirs(editionsInPath)

        for editionName in editionNames:
            self.doEdition(projectId, editionsInPath, editionsOutPath, editionName)

    def doEdition(self, projectId, editionsInPath, editionsOutPath, editionName):
        """Collects data belonging to a specific edition.

        Parameters
        ----------
        projectId: ObjectId
            MongoId of the project to which the edition belongs.
        editionsInPath: string
            Path on the filesystem to the editions input directory
            within this project.
        editionsOutPath: string
            Path on the filesystem to the editions working directory
            within this project.
        editionName: string
            Directory name of the edition to collect.
        """
        Messages = self.Messages
        Mongo = self.Mongo

        editionInPath = f"{editionsInPath}/{editionName}"

        meta = {}
        metaDir = f"{editionInPath}/meta"
        metaFiles = listFiles(metaDir, ".yml")

        for metaFile in metaFiles:
            meta[metaFile] = readYaml(f"{metaDir}/{metaFile}.yml", defaultEmpty=True)

        title = meta.get("dc", {}).get("title", editionName)

        scenes = listFiles(editionInPath, ".json")
        sceneSet = set(scenes)
        sceneCandy = {scene: {} for scene in scenes}

        candy = {}
        candyInPath = f"{editionInPath}/candy"
        candyFiles = []

        for image in listImages(candyInPath):
            candyFiles.append(image)
            (baseName, extension) = image.rsplit(".", 1)
            if baseName in sceneSet:
                sceneCandy[baseName][image] = extension.lower() == "png"
            else:
                candy[image] = True if image.lower() == "icon.png" else False

        editionInfo = dict(
            title=title,
            projectId=projectId,
            meta=meta,
            candy=candy,
        )
        editionId = Mongo.insertItem("editions", **editionInfo)
        Messages.plain(logmsg=f"\tEDITION {editionName} => {editionId}")
        editionOutPath = f"{editionsOutPath}/{editionId}"
        candyOutPath = f"{editionOutPath}/candy"
        dirMake(editionOutPath)
        dirCopy(candyInPath, candyOutPath)

        sceneDefault = None

        for scene in scenes:
            Messages.plain(logmsg=f"\t\tSCENE {scene}")
            default = sceneDefault is None and scene == SCENE_DEFAULT
            if default:
                sceneDefault = scene
            sceneInfo = dict(
                name=scene,
                editionId=editionId,
                projectId=projectId,
                candy=sceneCandy[scene],
                default=default,
            )
            Mongo.insertItem("scenes", **sceneInfo)
            sceneInPath = f"{editionInPath}/{scene}.json"
            sceneOutPath = f"{editionOutPath}/{scene}.json"
            fileCopy(sceneInPath, sceneOutPath)

        articlesInPath = f"{editionInPath}/articles"
        articlesOutPath = f"{editionOutPath}/articles"
        Messages.plain(logmsg="\t\tARTICLES")
        dirCopy(articlesInPath, articlesOutPath)

        for threed in list3d(editionInPath):
            threedInPath = f"{editionInPath}/{threed}"
            threedOutPath = f"{editionOutPath}/{threed}"
            Messages.plain(logmsg=f"\t\t3D {threed}")
            fileCopy(threedInPath, threedOutPath)

    def doWorkflow(self):
        """Collects workflow information from yaml files.

        !!! note "Test users"
            This includes test users when in test mode.
        """
        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo
        importSubdir = self.importSubdir

        dataDir = Settings.dataDir
        projectIdByName = self.projectIdByName

        workflowDir = f"{dataDir}/{importSubdir}/{WORKFLOW}"
        workflowPath = f"{workflowDir}/init.yml"
        workflow = readYaml(workflowPath, defaultEmpty=True)
        users = workflow["users"]
        projectUsers = workflow["projectUsers"]
        projectStatus = workflow["projectStatus"]

        userIdByName = {}

        for (userName, role) in users.items():
            userInfo = dict(
                name=userName,
                role=role,
            )
            userId = Mongo.insertItem("users", **userInfo)
            userIdByName[userName] = userId

        for (projectName, isPublished) in projectStatus.items():
            Messages.plain(logmsg=f"PROJECT {projectName} published: {isPublished}")
            Mongo.execute(
                "projects",
                "update_one",
                dict(_id=projectIdByName[projectName]),
                {"$set": dict(isPublished=isPublished)},
            )

        for (projectName, projectUsrs) in projectUsers.items():
            for (userName, role) in projectUsrs.items():
                xInfo = dict(
                    userId=userIdByName[userName],
                    projectId=projectIdByName[projectName],
                    role=role,
                )
                Mongo.insertItem("projectUsers", **xInfo)
