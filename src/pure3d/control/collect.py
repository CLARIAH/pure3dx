from control.files import (
    listDirs,
    listFiles,
    list3d,
    readYaml,
    fileExists,
    dirMake,
    dirRemove,
    dirCopy,
    fileCopy,
)
from control.environment import var
from control.flask import initializing


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

        tables = Settings.datamodel.tables

        collections = set(Mongo.collections())

        for table in collections:
            if table not in tables:
                Mongo.clearCollection(table, delete=True)

        for table in tables:
            Mongo.clearCollection(table, delete=False)

    def doOuter(self):
        """Collects data not belonging to specific projects."""
        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo

        iconFile = Settings.iconFile
        faviconFile = Settings.faviconFile
        siteCrit = Settings.siteCrit
        importDir = self.importDir
        workingDir = self.workingDir

        Messages.plain(logmsg=f"Import metadata from {importDir} to {workingDir}")

        dirMake(workingDir)

        metaDir = f"{importDir}/meta"
        metaFiles = listFiles(metaDir, ".yml")
        meta = {}

        for metaFile in metaFiles:
            meta[metaFile] = readYaml(f"{metaDir}/{metaFile}.yml", defaultEmpty=True)

        siteId = Mongo.insertRecord("site", **siteCrit, **meta)
        self.siteId = siteId

        fileCopy(f"{importDir}/{iconFile}", f"{workingDir}/{iconFile}")
        fileCopy(f"{importDir}/{faviconFile}", f"{workingDir}/{faviconFile}")

    def doProjects(self):
        """Collects data belonging to projects."""
        importDir = self.importDir
        workingDir = self.workingDir

        projectsInPath = f"{importDir}/project"
        projectsOutPath = f"{workingDir}/project"
        dirRemove(projectsOutPath)

        self.projectIdByName = {}
        self.editionIdByName = {}

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
        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo
        siteId = self.siteId
        projectIdByName = self.projectIdByName

        iconFile = Settings.iconFile
        projectInPath = f"{projectsInPath}/{projectName}"

        meta = {}
        metaDir = f"{projectInPath}/meta"
        metaFiles = listFiles(metaDir, ".yml")

        for metaFile in metaFiles:
            meta[metaFile] = readYaml(f"{metaDir}/{metaFile}.yml", defaultEmpty=True)

        title = meta.get("dc", {}).get("title", projectName)

        projectInfo = dict(title=title, siteId=siteId, **meta)

        projectId = Mongo.insertRecord("project", **projectInfo)
        projectIdByName[projectName] = projectId

        Messages.plain(logmsg=f"PROJECT {projectName} => {projectId}")

        projectOutPath = f"{projectsOutPath}/{projectId}"
        dirMake(projectOutPath)
        fileCopy(f"{projectInPath}/{iconFile}", f"{projectOutPath}/{iconFile}")

        self.doEditions(projectInPath, projectOutPath, projectName)

    def doEditions(self, projectInPath, projectOutPath, projectName):
        """Collects data belonging to the editions of a project.

        Parameters
        ----------
        projectInPath: string
            Path on the filesystem to the input directory of this project
        projectOutPath: string
            Path on the filesystem to the destination directory of this project
        projectName: String
            Name of the project to collect.
        """
        editionsInPath = f"{projectInPath}/edition"
        editionsOutPath = f"{projectOutPath}/edition"

        editionNames = listDirs(editionsInPath)

        for editionName in editionNames:
            self.doEdition(projectName, editionsInPath, editionsOutPath, editionName)

    def doEdition(self, projectName, editionsInPath, editionsOutPath, editionName):
        """Collects data belonging to a specific edition.

        Parameters
        ----------
        projectName: String
            Name of the project to which the edition belongs.
        editionsInPath: string
            Path on the filesystem to the editions input directory
            within this project.
        editionsOutPath: string
            Path on the filesystem to the editions working directory
            within this project.
        editionName: string
            Directory name of the edition to collect.
        """
        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo
        iconFile = Settings.iconFile
        projectIdByName = self.projectIdByName
        editionIdByName = self.editionIdByName

        projectId = projectIdByName[projectName]
        editionInPath = f"{editionsInPath}/{editionName}"

        meta = {}
        metaDir = f"{editionInPath}/meta"
        metaFiles = listFiles(metaDir, ".yml")

        for metaFile in metaFiles:
            meta[metaFile] = readYaml(f"{metaDir}/{metaFile}.yml", defaultEmpty=True)

        title = meta.get("dc", {}).get("title", editionName)
        authorTool = meta.get("settings", {}).get("authorTool", {})
        sceneFile = authorTool.sceneFile

        sceneInFile = f"{editionInPath}/{sceneFile}"

        if not fileExists(sceneInFile):
            Messages.plain(logmsg="\t\tNo scene file")

        modelFiles = list3d(editionInPath)
        nFiles = len(modelFiles)

        if nFiles == 0:
            Messages.plain(logmsg="\t\tNo models")

        editionRecord = dict(title=title, projectId=projectId, **meta)
        editionId = Mongo.insertRecord("edition", **editionRecord)
        editionIdByName.setdefault(projectName, {})[editionName] = editionId

        Messages.plain(logmsg=f"\tEDITION {editionName} => {editionId}")

        editionOutPath = f"{editionsOutPath}/{editionId}"
        dirMake(editionOutPath)

        for (label, files) in (
            ("scene", [sceneFile]),
            ("model", modelFiles),
            ("icon", [iconFile]),
        ):
            Messages.plain(logmsg=f"\t\t\t{label}:")
            for file in files:
                Messages.plain(logmsg=f"\t\t\t\t{file}")
                fileIn = f"{editionInPath}/{file}"
                fileOut = f"{editionOutPath}/{file}"
                fileCopy(fileIn, fileOut)

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
        editionIdByName = self.editionIdByName

        workflowDir = f"{importDir}/workflow"
        workflowPath = f"{workflowDir}/init.yml"
        workflow = readYaml(workflowPath, defaultEmpty=True)
        userRole = workflow["userRole"]
        status = workflow["status"]

        userByName = {}

        for (table, statusInfo) in status.items():
            field = statusInfo["field"]
            values = statusInfo["values"]
            tableRep = table.upper()

            for (outerName, outerValue) in values.items():
                if table == "project":
                    Messages.plain(
                        logmsg=(f"{tableRep} {outerName} {field}: {outerValue}")
                    )
                    Mongo.updateRecord(
                        table,
                        {field: outerValue},
                        _id=projectIdByName[outerName],
                    )
                elif table == "edition":
                    for (innerName, innerValue) in outerValue.items():
                        Messages.plain(
                            logmsg=(
                                f"{tableRep} {outerName}-{innerName}"
                                f" {field}: {innerValue}"
                            )
                        )
                        Mongo.updateRecord(
                            table,
                            {field: innerValue},
                            _id=editionIdByName[outerName][innerName],
                        )

        for (table, tableUsers) in userRole.items():
            if table != "site":
                continue
            for (userName, role) in tableUsers.items():
                user = f"{userName:0>16}"
                userInfo = dict(
                    nickname=userName,
                    user=user,
                    role=role,
                    isTest=True,
                )
                Mongo.insertRecord("user", **userInfo)
                userByName[userName] = user

        for (table, tableUsers) in userRole.items():
            if table == "site":
                continue
            elif table == "project":
                for (projectName, userInfo) in tableUsers.items():
                    for (userName, role) in userInfo.items():
                        xInfo = dict(
                            user=userByName[userName],
                            projectId=projectIdByName[projectName],
                            role=role,
                        )
                        Mongo.insertRecord("projectUser", **xInfo)
            elif table == "edition":
                for (projectName, editionInfo) in tableUsers.items():
                    for (editionName, userInfo) in editionInfo.items():
                        for (userName, role) in userInfo.items():
                            xInfo = dict(
                                user=userByName[userName],
                                editionId=editionIdByName[projectName][editionName],
                                role=role,
                            )
                            Mongo.insertRecord("editionUser", **xInfo)
