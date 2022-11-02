import os
import sys
from textwrap import dedent

from control.helpers.files import readYaml, readPath
from control.helpers.generic import AttrDict


VERSION_FILE = "version.txt"


class Config:
    def __init__(self, Messages, dataDirOnly=False):
        """All configuration details of the app.

        It is instantiated by a singleton object.

        Parameters
        ----------
        Messages: object
            Singleton instance of `control.messages.Messages`.
        """
        self.Messages = Messages
        Messages.debugAdd(self)
        self.good = True
        self.config = AttrDict()
        """The actual configuration settings are stored here.
        """

        self.checkEnv(dataDirOnly)

        if not self.good:
            Messages.error(logmsg="Check environment ...")
            sys.exit(1)

    def checkEnv(self, dataDirOnly):
        if dataDirOnly:
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
        Messages = self.Messages
        config = self.config

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

        if not os.path.exists(repoDir):
            Messages.error(
                logmsg=f"Cannot run because repo dir does not exist: {repoDir}"
            )
            self.good = False
            return

        config.repoDir = repoDir

        # what is the version of the pure3d app?

    def checkVersion(self):
        Messages = self.Messages
        config = self.config
        repoDir = config.repoDir

        versionPath = f"{repoDir}/src/{VERSION_FILE}"
        versionInfo = readPath(versionPath)

        if not versionInfo:
            Messages.error(logmsg=f"Cannot find version info in {versionPath}")
            self.good = False
            return

        config.versionInfo = versionInfo

    def checkSecret(self):
        Messages = self.Messages
        config = self.config

        secretFileLoc = os.environ.get("SECRET_FILE", None)

        if secretFileLoc is None:
            Messages.error(logmsg="Environment variable `SECRET_FILE` not defined")
            self.good = False
            return

        if not os.path.exists(secretFileLoc):
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
            config.secret_key = fh.read()

    def checkData(self):
        Messages = self.Messages
        config = self.config

        dataDir = os.environ.get("DATA_DIR", None)

        if dataDir is None:
            Messages.error(logmsg="Environment variable `DATA_DIR` not defined")
            self.good = False
            return

        if not os.path.exists(dataDir):
            Messages.error(logmsg=f"Data directory does not exist: {dataDir}")
            self.good = False
            return

        config.dataDir = dataDir.rstrip("/")

        # are we in test mode?

    def checkModes(self):
        Messages = self.Messages
        config = self.config

        testMode = os.environ.get("flasktest", None)
        if testMode is None:
            Messages.error(logmsg="Environment variable `flasktest` not defined")
            self.good = False
            return

        config.testMode = testMode == "test"
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

        config.debugMode = debugMode == "--debug"
        """With debug mode enabled.

        This means that the unminified, development versions of the javascript libraries
        of the 3D viewers are loaded, instead of the production versions.
        """

    def checkMongo(self):
        Messages = self.Messages
        config = self.config

        mongoUser = os.environ.get("mongouser", None)
        mongoPassword = os.environ.get("mongopassword", None)

        if mongoUser is None:
            Messages.error(logmsg="Environment variable `mongouser` not defined")
            self.good = False

        if mongoPassword is None:
            Messages.error(logmsg="Environment variable `mongopassword` not defined")
            self.good = False

        config.mongoUser = os.environ["mongouser"]
        config.mongoPassword = os.environ["mongopassword"]

    def checkSettings(self):
        Messages = self.Messages
        config = self.config

        repoDir = config.repoDir
        yamlDir = f"{repoDir}/src/pure3d/control/yaml"
        config.yamlDir = yamlDir

        settings = readYaml(f"{yamlDir}/settings.yaml")
        if settings is None:
            Messages.error(logmsg=f"Cannot read settings.yaml in {yamlDir}")
            self.good = False
            return

        for (k, v) in settings.items():
            config[k] = v

    def checkAuth(self):
        Messages = self.Messages
        config = self.config

        yamlDir = config.yamlDir

        authData = readYaml(f"{yamlDir}/authorise.yaml")
        if authData is None:
            Messages.error(logmsg="Cannot read authorise.yaml in {yamlDir}")
            self.good = False
            return

        auth = AttrDict()
        config.auth = auth

        for (k, v) in authData.items():
            auth[k] = v

    def checkViewers(self):
        Messages = self.Messages
        config = self.config

        yamlDir = config.yamlDir
        dataDir = config.dataDir

        viewerDir = f"{dataDir}/viewers"

        config.viewerDir = viewerDir
        config.viewerUrlBase = "/data/viewers"

        viewerSettingsFile = f"{yamlDir}/viewers.yaml"
        viewerSettings = readYaml(viewerSettingsFile)
        if viewerSettings is None:
            Messages.error(logmsg="Cannot read viewers.yaml in {yamlDir}")
            self.good = False
            return

        if not os.path.exists(viewerDir):
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

        config.viewerDefault = viewerDefault
        config.viewers = viewers
