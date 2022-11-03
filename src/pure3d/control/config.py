import os
import sys
from textwrap import dedent

from control.helpers.files import dirExists, fileExists, readYaml, readPath
from control.helpers.generic import AttrDict


VERSION_FILE = "version.txt"


class Config:
    def __init__(self, Messages, flask=True):
        """All configuration details of the app.

        It is instantiated by a singleton object.

        Settings will be collected from the environment:

        * yaml files
        * environment variables
        * files and directories (for supported viewer software)

        !!! note "Missing information"
            If essential information is missing, the flask app will not be started,
            and no webserving will take place.

        Parameters
        ----------
        Messages: object
            Singleton instance of `control.messages.Messages`.
        flask: boolean, optional True
            If False, only those settings are fetched that do not have relevance
            for the actual web serving by flask application.
            This is used for code that runs prior to web serving, e.g.
            data collection in `control.collect.Collect`.
        """
        self.Messages = Messages
        Messages.debugAdd(self)
        self.debug("CONFIG INIT")
        self.good = True
        self.Settings = AttrDict()
        """The actual configuration settings are stored here.
        """

        self.checkEnv(flask)

        if not self.good:
            Messages.error(logmsg="Check environment ...")
            sys.exit(1)

    def checkEnv(self, flask):
        """Collect the relevant information.

        If essential information is missing, processing stops.
        This is done by setting the `good` member of Config to False.

        Parameters
        ----------
        flask: boolean
            Whether to collect all, or a subset of variables that are not
            used for actually serving pages.
        """
        if not flask:
            self.checkRepo(),
            self.checkData()
            self.checkMongo(),
            self.checkSettings(),
            return

        for method in (
            self.checkRepo,
            self.checkVersion,
            self.checkSecret,
            self.checkData,
            self.checkModes,
            self.checkMongo,
            self.checkSettings,
            self.checkAuth,
            self.checkViewers,
        ):
            if self.good:
                method()

    def checkRepo(self):
        """Get the location of the pure3dx repository on the file system.
        """
        Messages = self.Messages
        Settings = self.Settings

        repoDir = os.environ.get("repodir", None)
        if repoDir is None:
            Messages.error(
                logmsg=dedent(
                    """
                    Environment variable `repodir` not defined
                    Don't know where I must be running
                    """
                )
            )
            self.good = False
            return

        if not dirExists(repoDir):
            Messages.error(
                logmsg=f"Cannot run because repo dir does not exist: {repoDir}"
            )
            self.good = False
            return

        Settings.repoDir = repoDir

        # what is the version of the pure3d app?

    def checkVersion(self):
        """Get the current version of the pure3d app.
        """
        Messages = self.Messages
        Settings = self.Settings
        repoDir = Settings.repoDir

        versionPath = f"{repoDir}/src/{VERSION_FILE}"
        versionInfo = readPath(versionPath)

        if not versionInfo:
            Messages.error(logmsg=f"Cannot find version info in {versionPath}")
            self.good = False
            return

        Settings.versionInfo = versionInfo

    def checkSecret(self):
        """Obtain a secret.

        This is secret information used for encrypting sessions.
        It resides somewhere on the file system, outside the pure3d repository.
        """
        Messages = self.Messages
        Settings = self.Settings

        secretFileLoc = os.environ.get("SECRET_FILE", None)

        if secretFileLoc is None:
            Messages.error(logmsg="Environment variable `SECRET_FILE` not defined")
            self.good = False
            return

        if not fileExists(secretFileLoc):
            Messages.error(
                logmsg=dedent(
                    f"""
                    Missing secret file for sessions: {secretFileLoc}
                    Create that file with contents a random string like this:
                    fjOL901Mc3XZy8dcbBnOxNwZsOIBlul")
                    But do not choose this one.")
                    Use your password manager to create a random one.
                    """
                )
            )
            self.good = False
            return

        with open(secretFileLoc) as fh:
            Settings.secret_key = fh.read()

    def checkData(self):
        """Get the location of the project data on the file system.
        """
        Messages = self.Messages
        Settings = self.Settings

        dataDir = os.environ.get("DATA_DIR", None)

        if dataDir is None:
            Messages.error(logmsg="Environment variable `DATA_DIR` not defined")
            self.good = False
            return

        if not dirExists(dataDir):
            Messages.error(logmsg=f"Data directory does not exist: {dataDir}")
            self.good = False
            return

        Settings.dataDir = dataDir.rstrip("/")

        # are we in test mode?

    def checkModes(self):
        """Determine whether flask is running in test/debug or production mode.
        """
        Messages = self.Messages
        Settings = self.Settings

        testMode = os.environ.get("flasktest", None)
        if testMode is None:
            Messages.error(logmsg="Environment variable `flasktest` not defined")
            self.good = False
            return

        Settings.testMode = testMode == "test"
        """With test mode enabled.

        This means that there is a row of test users on the interface,
        and that you can log in as one of these users with a single click,
        without any kind of authentication.
        """

        debugMode = os.environ.get("flaskdebug", None)
        if debugMode is None:
            Messages.error(logmsg="Environment variable `flaskdebug` not defined")
            self.good = False
            return

        Settings.debugMode = debugMode == "--debug"
        """With debug mode enabled.

        This means that the unminified, development versions of the javascript libraries
        of the 3D viewers are loaded, instead of the production versions.
        """

    def checkMongo(self):
        """Obtain the connection details for MongDB.

        It is not checked whether connection with MongoDb actually works
        with these credentials.
        """
        Messages = self.Messages
        Settings = self.Settings

        mongoUser = os.environ.get("mongouser", None)
        mongoPassword = os.environ.get("mongopassword", None)

        if mongoUser is None:
            Messages.error(logmsg="Environment variable `mongouser` not defined")
            self.good = False

        if mongoPassword is None:
            Messages.error(logmsg="Environment variable `mongopassword` not defined")
            self.good = False

        Settings.mongoUser = os.environ["mongouser"]
        Settings.mongoPassword = os.environ["mongopassword"]

    def checkSettings(self):
        """Read the yaml file with application settings.
        """
        Messages = self.Messages
        Settings = self.Settings

        repoDir = Settings.repoDir
        yamlDir = f"{repoDir}/src/pure3d/control/yaml"
        Settings.yamlDir = yamlDir

        settings = readYaml(f"{yamlDir}/settings.yaml")
        if settings is None:
            Messages.error(logmsg=f"Cannot read settings.yaml in {yamlDir}")
            self.good = False
            return

        for (k, v) in settings.items():
            Settings[k] = v

    def checkAuth(self):
        """Read gthe yaml file with the authorisation rules.
        """
        Messages = self.Messages
        Settings = self.Settings

        yamlDir = Settings.yamlDir

        authData = readYaml(f"{yamlDir}/authorise.yaml")
        if authData is None:
            Messages.error(logmsg="Cannot read authorise.yaml in {yamlDir}")
            self.good = False
            return

        auth = AttrDict()
        Settings.auth = auth

        for (k, v) in authData.items():
            auth[k] = v

    def checkViewers(self):
        """Make an inventory of the supported 3D viewers.
        """
        Messages = self.Messages
        Settings = self.Settings

        yamlDir = Settings.yamlDir
        dataDir = Settings.dataDir

        viewerDir = f"{dataDir}/viewers"

        Settings.viewerDir = viewerDir
        Settings.viewerUrlBase = "/data/viewers"

        viewerSettingsFile = f"{yamlDir}/viewers.yaml"
        viewerSettings = readYaml(viewerSettingsFile)
        if viewerSettings is None:
            Messages.error(logmsg="Cannot read viewers.yaml in {yamlDir}")
            self.good = False
            return

        if not dirExists(viewerDir):
            Messages.error(logmsg=f"No viewer software directory: {viewerDir}")
            self.good = False
            return

        viewers = AttrDict()
        viewerDefault = None

        with os.scandir(viewerDir) as vd:
            for entry in vd:
                if entry.is_dir():
                    viewerName = entry.name
                    if viewerName not in viewerSettings:
                        Messages.warning(
                            logmsg=(
                                f"Skipping viewer {viewerName}"
                                "because not defined in viewers.yaml"
                            )
                        )
                        continue
                    viewerConfig = AttrDict(viewerSettings[viewerName])
                    viewerPath = f"{viewerDir}/{viewerName}"
                    versions = []

                    with os.scandir(viewerPath) as sd:
                        for entry in sd:
                            if entry.is_dir():
                                version = entry.name
                                versions.append(version)

                    default = viewerConfig.default

                    if default:
                        if viewerDefault is not None:
                            Messages.warning(
                                logmsg=(
                                    f"default viewer declaration {viewerName} overrides"
                                    f" previously declared default {viewerDefault}"
                                )
                            )
                        viewerDefault = viewerName

                    viewers[viewerName] = AttrDict(
                        versions=versions, modes=viewerConfig.modes
                    )
        if viewerDefault is None:
            Messages.error(
                logmsg=(
                    f"None of the viewers is declared as default viewer"
                    f" in {viewerSettingsFile}"
                )
            )
            self.good = False
            return

        Settings.viewerDefault = viewerDefault
        Settings.viewers = viewers
