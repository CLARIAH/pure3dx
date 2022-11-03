import os

from control.helpers.files import listFiles, listImages, readYaml


META = "meta"
PROJECTS = "projects"
EDITIONS = "editions"
WORKFLOW = "workflow"

SCENE_DEFAULT = "intro"


class Collect:
    def __init__(self, Settings, Messages, Mongo):
        """Provides initial content for the MongoDb.

        Normally, this does not have to run, since the MongoDb is persistent.
        Only when the MongoDb of the Pure3D app is fresh,
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
        `data` directory of this repo (`pure3dz`).

        Parameters
        ----------
        Settings: AttrDict
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
        doCollect = os.environ.get("docollect", "x") == "v"
        beforeFlask = os.environ.get('WERKZEUG_RUN_MAIN', None) is None

        return beforeFlask and doCollect

    def fetch(self):
        if not self.trigger():
            return

        Messages = self.Messages
        Messages.info(logmsg="Collecting data before starting the app")

        self.clearDb()
        self.doOuter()
        self.doProjects()
        self.doWorkflow()

    def clearDb(self):
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

    def doOuter(self):
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

        Mongo.execute("meta", "insert_one", dict(meta=meta))

    def doProjects(self):
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

        result = Mongo.execute("projects", "insert_one", projectInfo)
        projectId = result.inserted_id if result is not None else None
        projectIdByName[projectName] = projectId

        self.doEditions(projectPath, projectId)

    def doEditions(self, projectPath, projectId):
        Messages = self.Messages

        editionsPath = f"{projectPath}/{EDITIONS}"

        with os.scandir(editionsPath) as ed:
            for entry in ed:
                if entry.is_dir():
                    editionName = entry.name
                    Messages.plain(logmsg=f"\tEDITION {editionName}")
                    self.doEdition(projectId, editionsPath, editionName)

    def doEdition(self, projectId, editionsPath, editionName):
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
        result = Mongo.execute("editions", "insert_one", editionInfo)
        editionId = result.inserted_id if result is not None else None

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
            result = Mongo.execute("scenes", "insert_one", sceneInfo)

    def doWorkflow(self):
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
            result = Mongo.execute("users", "insert_one", userInfo)
            userId = result.inserted_id if result is not None else None
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
                Mongo.execute("projectUsers", "insert_one", xInfo)
