from control.files import (
    listDirs,
    listFiles,
    get3d,
    readYaml,
    dirMake,
    dirRemove,
    dirCopy,
    fileCopy,
)
from control.environment import var
from control.flask import initializing

ICON_FILE = "icon.png"
FAVICON_FILE = "favicon.ico"


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
        Settings: `control.generic.AttrDict`
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

        importSubdir = var("initdata") or "exampledata"
        dataDir = Settings.dataDir
        self.workingDir = Settings.workingDir
        self.importDir = f"{dataDir}/{importSubdir}"

    def trigger(self):
        """Determines whether data collection should be done.

        We only do data collection if the environment variable `docollect` is `v`
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

        return initializing() and doCollect

    def fetch(self):
        """Performs a data collection."""
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
        Messages = self.Messages
        Mongo = self.Mongo

        importDir = self.importDir
        workingDir = self.workingDir

        Messages.plain(logmsg=f"Import metadata from {importDir} to {workingDir}")

        dirMake(workingDir)

        metaDir = f"{importDir}/meta"
        metaFiles = listFiles(metaDir, ".yml")
        meta = {}

        for metaFile in metaFiles:
            meta[metaFile] = readYaml(f"{metaDir}/{metaFile}.yml", defaultEmpty=True)

        Mongo.insertRecord("meta", name="site", icon=ICON_FILE, **meta)

        fileCopy(f"{importDir}/{ICON_FILE}", f"{workingDir}/{ICON_FILE}")
        fileCopy(f"{importDir}/{FAVICON_FILE}", f"{workingDir}/{FAVICON_FILE}")

    def doProjects(self):
        """Collects data belonging to projects."""
        importDir = self.importDir
        workingDir = self.workingDir

        projectsInPath = f"{importDir}/projects"
        projectsOutPath = f"{workingDir}/projects"
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

        projectInfo = dict(title=title, icon=ICON_FILE, **meta)

        projectId = Mongo.insertRecord("projects", **projectInfo)
        projectIdByName[projectName] = projectId

        Messages.plain(logmsg=f"PROJECT {projectName} => {projectId}")

        projectOutPath = f"{projectsOutPath}/{projectId}"
        dirMake(projectOutPath)
        fileCopy(f"{projectInPath}/{ICON_FILE}", f"{projectOutPath}/{ICON_FILE}")

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
        editionsInPath = f"{projectInPath}/editions"
        editionsOutPath = f"{projectOutPath}/editions"

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

        modelFile = None

        modelFiles = get3d(editionInPath, "model")

        if len(modelFiles) == 0:
            Messages.plain(logmsg="\t\tNo model")
        else:
            extensions = modelFiles["model"]
            if len(extensions) > 1:
                Messages.plain(
                    logmsg=f"\t\tMultiple extensions for model: {', '.join(extensions)}"
                )
            else:
                modelExt = extensions[0]
                modelFile = f"model.{modelExt.lower()}"

        editionInfo = dict(
            title=title, projectId=projectId, model=modelFile, icon=ICON_FILE, **meta
        )
        editionId = Mongo.insertRecord("editions", **editionInfo)

        Messages.plain(logmsg=f"\tEDITION {editionName} => {editionId}")

        editionOutPath = f"{editionsOutPath}/{editionId}"
        dirMake(editionOutPath)
        fileCopy(f"{editionInPath}/{ICON_FILE}", f"{editionOutPath}/{ICON_FILE}")

        if modelFile is not None:
            modelFileIn = f"{editionInPath}/model.{modelExt}"
            modelFileOut = f"{editionOutPath}/{modelFile}"
            fileCopy(modelFileIn, modelFileOut)

        self.doScenes(editionInPath, editionOutPath, projectId, editionId)

    def doScenes(self, editionInPath, editionOutPath, projectId, editionId):
        """Collects data belonging to the scenes of an edition.

        Parameters
        ----------
        editionInPath: string
            Path on the filesystem to the input directory of this edition
        editionOutPath: string
            Path on the filesystem to the destination directory of this edition
        projectId: ObjectId
            MongoId of the project to collect.
        editionId: ObjectId
            MongoId of the edition to collect.
        """
        Messages = self.Messages
        Mongo = self.Mongo

        scenes = listFiles(editionInPath, ".json")

        sceneDefault = None

        for scene in scenes:
            Messages.plain(logmsg=f"\t\tSCENE {scene}")

            default = sceneDefault is None and scene == "intro"
            if default:
                sceneDefault = scene

            sceneFile = f"{scene}.json"
            sceneIcon = f"{scene}.png"

            sceneInfo = dict(
                name=scene,
                scene=sceneFile,
                icon=sceneIcon,
                editionId=editionId,
                projectId=projectId,
                default=default,
            )
            Mongo.insertRecord("scenes", **sceneInfo)
            sceneInPath = f"{editionInPath}/{sceneFile}"
            sceneOutPath = f"{editionOutPath}/{sceneFile}"
            fileCopy(sceneInPath, sceneOutPath)
            iconInPath = f"{editionInPath}/{sceneIcon}"
            iconOutPath = f"{editionOutPath}/{sceneIcon}"
            fileCopy(iconInPath, iconOutPath)

        articlesInPath = f"{editionInPath}/articles"
        articlesOutPath = f"{editionOutPath}/articles"
        Messages.plain(logmsg="\t\tARTICLES")
        dirCopy(articlesInPath, articlesOutPath)

    def doWorkflow(self):
        """Collects workflow information from yaml files.

        !!! note "Test users"
            This includes test users when in test mode.
        """
        Messages = self.Messages
        Mongo = self.Mongo
        importDir = self.importDir

        projectIdByName = self.projectIdByName

        workflowDir = f"{importDir}/workflow"
        workflowPath = f"{workflowDir}/init.yml"
        workflow = readYaml(workflowPath, defaultEmpty=True)
        users = workflow["users"]
        projectUsers = workflow["projectUsers"]
        projectStatus = workflow["projectStatus"]

        userByName = {}

        for (userName, role) in users.items():
            sub = f"{userName:0>16}"
            userInfo = dict(
                nickname=userName,
                sub=sub,
                role=role,
                isTest=True,
            )
            Mongo.insertRecord("users", **userInfo)
            userByName[userName] = sub

        for (projectName, isPublished) in projectStatus.items():
            Messages.plain(logmsg=f"PROJECT {projectName} published: {isPublished}")
            Mongo.updateRecord(
                "projects",
                dict(isPublished=isPublished),
                _id=projectIdByName[projectName],
            )

        for (projectName, projectUsrs) in projectUsers.items():
            for (userName, role) in projectUsrs.items():
                xInfo = dict(
                    user=userByName[userName],
                    projectId=projectIdByName[projectName],
                    role=role,
                )
                Mongo.insertRecord("projectUsers", **xInfo)
