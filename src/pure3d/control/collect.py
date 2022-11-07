import os

from control.helpers.files import listFiles, listImages, readYaml


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

        We only do data collection if the environment variable `docollect` has
        the value `v`.

        We also prevent this from happening twice, which occurs when Flask runs
        in debug mode, since then the code is loaded twice.
        We guard against this by inspecting the environment variable
        `WERKZEUG_RUN_MAIN`. If it is set, we are already running the app,
        and data collection should be inhibited, because it has been done
        just before Flask started running.
        """
        doCollect = os.environ.get("docollect", "x") == "v"
        beforeFlask = os.environ.get('WERKZEUG_RUN_MAIN', None) is None

        return beforeFlask and doCollect

    def fetch(self):
        """Performs a data collection, but only if triggered by the right conditions.

        See also `Collect.trigger()`
        """
        if not self.trigger():
            return

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
        """Collects data not belonging to specific projects.
        """
        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo

        dataDir = Settings.dataDir
        Messages.plain(logmsg=f"Data directory = {dataDir}")

        metaDir = f"{dataDir}/{META}"
        metaFiles = listFiles(metaDir, ".yml")
        meta = {}

        for metaFile in metaFiles:
            meta[metaFile] = readYaml(f"{metaDir}/{metaFile}.yml", defaultEmpty=True)

        Mongo.insertItem("meta", **meta)

    def doProjects(self):
        """Collects data belonging to projects.
        """
        Settings = self.Settings
        Messages = self.Messages

        dataDir = Settings.dataDir
        projectsPath = f"{dataDir}/{PROJECTS}"

        self.projectIdByName = {}

        with os.scandir(projectsPath) as pd:
            for entry in pd:
                if entry.is_dir():
                    projectName = entry.name
                    Messages.plain(logmsg=f"PROJECT {projectName}")
                    self.doProject(projectsPath, projectName)

    def doProject(self, projectsPath, projectName):
        """Collects data belonging to a specific project.

        Parameters
        ----------
        projectsPath: string
            Path on the filesystem to the projects directory
        projectName: string
            Directory name of the project to collect.
        """
        Mongo = self.Mongo
        projectIdByName = self.projectIdByName

        projectPath = f"{projectsPath}/{projectName}"

        meta = {}
        metaDir = f"{projectPath}/meta"
        metaFiles = listFiles(metaDir, ".yml")

        for metaFile in metaFiles:
            meta[metaFile] = readYaml(f"{metaDir}/{metaFile}.yml", defaultEmpty=True)

        title = meta.get("dc", {}).get("title", projectName)

        candy = {}
        candyPath = f"{projectPath}/candy"

        for image in listImages(candyPath):
            candy[image] = True if image.lower() == "icon.png" else False

        projectInfo = dict(
            title=title,
            name=projectName,
            meta=meta,
            candy=candy,
        )

        projectId = Mongo.insertItem("projects", **projectInfo)
        projectIdByName[projectName] = projectId

        self.doEditions(projectId, projectPath)

    def doEditions(self, projectId, projectPath):
        """Collects data belonging to the editions of a project.

        Parameters
        ----------
        projectId: ObjectId
            MongoId of the project to collect.
        projectPath: string
            Path on the filesystem to the directory of this project
        """
        Messages = self.Messages

        editionsPath = f"{projectPath}/{EDITIONS}"

        with os.scandir(editionsPath) as ed:
            for entry in ed:
                if entry.is_dir():
                    editionName = entry.name
                    Messages.plain(logmsg=f"\tEDITION {editionName}")
                    self.doEdition(projectId, editionsPath, editionName)

    def doEdition(self, projectId, editionsPath, editionName):
        """Collects data belonging to a specific edition.

        Parameters
        ----------
        projectId: ObjectId
            MongoId of the project to which the edition belongs.
        editionsPath: string
            Path on the filesystem to the editions directory within this project.
        editionName: string
            Directory name of the edition to collect.
        """
        Messages = self.Messages
        Mongo = self.Mongo

        editionPath = f"{editionsPath}/{editionName}"

        meta = {}
        metaDir = f"{editionPath}/meta"
        metaFiles = listFiles(metaDir, ".yml")

        for metaFile in metaFiles:
            meta[metaFile] = readYaml(f"{metaDir}/{metaFile}.yml", defaultEmpty=True)

        title = meta.get("dc", {}).get("title", editionName)

        scenes = listFiles(editionPath, ".json")
        sceneSet = set(scenes)
        sceneCandy = {scene: {} for scene in scenes}

        candy = {}
        candyPath = f"{editionPath}/candy"

        for image in listImages(candyPath):
            (baseName, extension) = image.rsplit(".", 1)
            if baseName in sceneSet:
                sceneCandy[baseName][image] = extension.lower() == "png"
            else:
                candy[image] = True if image.lower() == "icon.png" else False

        editionInfo = dict(
            title=title,
            name=editionName,
            projectId=projectId,
            meta=meta,
            candy=candy,
        )
        editionId = Mongo.insertItem("editions", **editionInfo)

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

    def doWorkflow(self):
        """Collects workflow information from yaml files.

        !!! note "Test users"
            This includes test users when in test mode.
        """
        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo

        dataDir = Settings.dataDir
        projectIdByName = self.projectIdByName

        workflowPath = f"{dataDir}/{WORKFLOW}/init.yml"
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
