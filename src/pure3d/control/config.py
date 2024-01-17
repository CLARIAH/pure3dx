from textwrap import dedent
from subprocess import check_output

from control.generic import AttrDict, getVersionKeyFunc
from control.files import dirMake, dirExists, fileExists, readYaml, listDirs
from control.environment import var
from control.html import HtmlElements


class Config:
    def __init__(self, Messages):
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
        """
        self.Messages = Messages
        Messages.debugAdd(self)
        Messages.info(logmsg="CONFIG INIT")
        self.good = True
        Settings = AttrDict()
        Settings.H = HtmlElements(Settings, Messages)
        self.Settings = Settings
        """The actual configuration settings are stored here.
        """

        self.checkEnv()

        if not self.good:
            Messages.error(logmsg="Check environment")
            quit()

    def checkEnv(self):
        """Collect the relevant information.

        If essential information is missing, processing stops.
        This is done by setting the `good` member of Config to False.
        """

        for method in (
            self.checkRepo,
            self.checkWebdav,
            self.checkVersion,
            self.checkSecret,
            self.checkModes,
            self.checkData,
            self.checkMongo,
            self.checkSettings,
            self.checkDatamodel,
            self.checkAuth,
            self.checkViewers,
            self.checkBanner,
        ):
            if self.good:
                method()

    def checkRepo(self):
        """Get the location of the pure3dx repository on the file system."""
        Messages = self.Messages
        Settings = self.Settings

        repoDir = var("repodir")
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
        yamlDir = f"{repoDir}/src/pure3d/control/yaml"
        Settings.yamlDir = yamlDir

    def checkWebdav(self):
        """Read the WEBDav methods from the webdav.yaml file.

        The methods are associated with the `read` or `update` keyword,
        depending on whether they are `GET` like or `PUT` like.
        """
        Settings = self.Settings
        yamlDir = Settings.yamlDir
        webdavFile = "webdav.yml"
        webdavInfo = readYaml(f"{yamlDir}/{webdavFile}")
        Settings.webdavMethods = webdavInfo.methods

    def checkVersion(self):
        """Get the current version of the pure3d app.

        We represent the version as the short hash of the current commit
        of the git repo that the running code is in.
        """
        Settings = self.Settings
        H = Settings.H
        repoDir = Settings.repoDir
        versionFile = f"{repoDir}/VERSION.txt"

        try:
            actual = True
            (long, short) = tuple(
                check_output(["git", "rev-parse", *args, "HEAD"], cwd=repoDir)
                .decode("ascii")
                .strip()
                for args in ([], ["--short"])
            )
            with open(versionFile, "w") as fh:
                fh.write(f"{long}\t{short}\n")
        except Exception as e:
            print(e.stderr)
            print(f"Could not get version from git, reading it from file {versionFile}")
            actual = False
            if not fileExists(versionFile):
                known = False
                (long, short) = ("", "")
            else:
                known = True
                with open(versionFile) as fh:
                    try:
                        (long, short) = fh.read().strip().split("\t")
                    except Exception:
                        known = False
                        (long, short) = ("", "")

        Settings = self.Settings
        repoDir = Settings.repoDir

        if actual:
            label1 = "this version"
            text = f"this version is {short}"
        else:
            if known:
                label1 = "previous version"
                text = f"previous version was {short}"
            else:
                label1 = "latest version"
                text = "unknown version, go to latest version"

        title = f"visit {label1} of the code on GitHub"
        gitLocation = var("gitlocation").removesuffix(".git")
        href = f"{gitLocation}/tree/{long}" if long else gitLocation
        Settings.versionInfo = H.a(text, href, target="_blank", title=title)

    def checkSecret(self):
        """Obtain a secret.

        This is secret information used for encrypting sessions.
        It resides somewhere on the file system, outside the pure3d repository.
        """
        Messages = self.Messages
        Settings = self.Settings

        secret = var("flasksecret")

        if secret is None:
            Messages.error(
                logmsg="No secret given for flask: variable `flasksecret` not defined"
            )
            self.good = False
            return

        Settings.secret_key = secret

    def checkModes(self):
        """Determine whether flask is running in test/pilot/custom/prod mode."""
        Messages = self.Messages
        Settings = self.Settings

        runMode = var("runmode")
        if runMode is None:
            Messages.error(logmsg="Environment variable `runmode` not defined")
            self.good = False
            return

        if runMode in {"test", "pilot", "custom"}:
            runMode = runMode
        else:
            runMode = "prod"

        Settings.runMode = runMode
        """In which mode the app runs.

        Values are:

        *   `test`:
            The app works with the example data.
            There is a row of test users on the interface,
            and that you can log in as one of these users with a single click,
            without any kind of authentication.
        *   `pilot`:
            The app works with the pilot data.
            There is a row of pilot users on the interface,
            and that you can log in as one of these users with a single click,
            without any kind of authentication.
        *   `custom`
            The app works with custom data.
            Initially, there is only one admin user, you can log in with a single click.
        *   All other run modes count as production mode, `prod`.
        """

        debugMode = var("flaskdebug")
        if debugMode is None:
            Messages.error(logmsg="Environment variable `flaskdebug` not defined")
            self.good = False
            return

        Settings.debugMode = debugMode == "v"
        """With debug mode enabled.

        This means that the unminified, development versions of the javascript libraries
        of the 3D viewers are loaded, instead of the production versions.
        """

    def checkData(self):
        """Get the location of the project data on the file system."""
        Messages = self.Messages
        Settings = self.Settings
        runMode = Settings.runMode

        dataDir = var("DATA_DIR")

        if dataDir is None:
            Messages.error(logmsg="Environment variable `DATA_DIR` not defined")
            self.good = False
            return

        dataDir = dataDir.rstrip("/")
        sep = "/" if dataDir else ""
        workingDir = f"{dataDir}{sep}working/{runMode}"

        if not dirExists(dataDir):
            Messages.error(logmsg=f"Working data directory does not exist: {dataDir}")
            self.good = False
            return

        dirMake(workingDir)
        Settings.dataDir = dataDir
        Settings.workingDir = workingDir

        if runMode in {"pilot", "test", "custom", "prod"}:
            importSubdir = (
                "exampledata"
                if runMode == "test"
                else "pilotdata"
                if runMode == "pilot"
                else "customdata"
                if runMode == "custom"
                else "proddata"
            )
            Settings.importDir = f"{dataDir}/{importSubdir}"

    def checkMongo(self):
        """Obtain the connection details for MongDB.

        It is not checked whether connection with MongoDb actually works
        with these credentials.
        """
        Messages = self.Messages
        Settings = self.Settings

        mongoUser = var("mongouser")
        mongoPassword = var("mongopassword")

        if mongoUser is None:
            Messages.error(logmsg="Environment variable `mongouser` not defined")
            self.good = False

        if mongoPassword is None:
            Messages.error(logmsg="Environment variable `mongopassword` not defined")
            self.good = False

        Settings.mongoUser = mongoUser
        Settings.mongoPassword = mongoPassword

    def checkSettings(self):
        """Read the yaml file with application settings."""
        Messages = self.Messages
        Settings = self.Settings
        yamlDir = Settings.yamlDir

        settingsFile = "settings.yml"
        settings = readYaml(f"{yamlDir}/{settingsFile}")
        if settings is None:
            Messages.error(logmsg=f"Cannot read {settingsFile} in {yamlDir}")
            self.good = False
            return

        for k, v in settings.items():
            Settings[k] = v

    def checkDatamodel(self):
        """Read the yaml file with table and field settings.

        It contains model `master` that contains the master tables
        with the information which tables are details of it.

        It also contains ``link` that contains the link tables
        with the information which tables are being linked.

        Both elements are needed when we delete records.

        If a user deletes a master record, its detail records become invalid.
        So either we must enforce that the user deletes the details first,
        or the system must delete those records automatically.

        When a user deletes a record that is linked to another record by means
        of a coupling record, the coupling record must be deleted automatically.

        Fields are bits of data that are stored in parts of records
        in MongoDb tables.

        Fields have several properties which we summarize under a key.
        So if we know the key of a field, we have access to all of its
        properties.

        The properties `nameSpave` and `fieldPath` determine how to drill
        down in a record in order to find the value of that field.

        The property `tp` is the data type of the field, default `string`.

        The property `caption` is a label that may accompany a field value
        on the interface.
        """
        Messages = self.Messages
        Settings = self.Settings

        yamlDir = Settings.yamlDir

        datamodelFile = "datamodel.yml"
        datamodel = readYaml(f"{yamlDir}/{datamodelFile}")
        if datamodel is None:
            Messages.error(logmsg=f"Cannot read {datamodelFile} in {yamlDir}")
            self.good = False
            return

        masterDetail = AttrDict()
        for detail, master in datamodel.detailMaster.items():
            masterDetail[master] = detail
        datamodel.masterDetail = masterDetail

        mainLink = AttrDict()
        for link, mains in datamodel.linkMain.items():
            for main in mains:
                mainLink.setdefault(main, []).append(link)
        datamodel.mainLink = mainLink

        Settings.datamodel = datamodel

    def checkAuth(self):
        """Read the yaml file with the authorisation rules."""
        Messages = self.Messages
        Settings = self.Settings

        yamlDir = Settings.yamlDir

        authFile = "authorise.yml"
        authData = readYaml(f"{yamlDir}/{authFile}")
        if authData is None:
            Messages.error(logmsg="Cannot read {authFile} in {yamlDir}")
            self.good = False
            return

        Settings.auth = authData

        tableFromRole = AttrDict()
        for table, roles in authData.roles.items():
            for role in roles:
                tableFromRole[role] = table

        Settings.auth.tableFromRole = tableFromRole

        rank = {role: i for (i, role) in enumerate(authData.rolesOrder)}
        Settings.auth.roleRank = lambda role: rank[role]

    def checkViewers(self):
        """Make an inventory of the supported 3D viewers."""
        Messages = self.Messages
        Settings = self.Settings

        yamlDir = Settings.yamlDir
        dataDir = Settings.dataDir

        viewerDir = f"{dataDir}/viewers"

        Settings.viewerDir = viewerDir
        Settings.viewerUrlBase = "/data/viewers"

        versionKey = getVersionKeyFunc()
        Settings.versionKey = versionKey

        viewersFile = "viewers.yml"
        viewerSettingsFile = f"{yamlDir}/{viewersFile}"
        viewerSettings = readYaml(viewerSettingsFile)
        if viewerSettings is None:
            Messages.error(logmsg="Cannot read {viewersFile} in {yamlDir}")
            self.good = False
            return

        if not dirExists(viewerDir):
            Messages.error(logmsg=f"No viewer software directory: {viewerDir}")
            self.good = False
            return

        viewerNames = listDirs(viewerDir)

        for viewerName in viewerNames:
            if viewerName not in viewerSettings.viewers:
                Messages.warning(
                    logmsg=(
                        f"Skipping viewer {viewerName}"
                        "because not defined in {viewersFile}"
                    )
                )
                continue
            viewerConfig = viewerSettings.viewers[viewerName]
            viewerPath = f"{viewerDir}/{viewerName}"

            versions = list(reversed(sorted(listDirs(viewerPath), key=versionKey)))

            viewerConfig.versions = versions

        Settings.viewers = viewerSettings.viewers
        Settings.viewerActions = viewerSettings.actions
        Settings.viewerDefault = viewerSettings.default

    def checkBanner(self):
        """Sets a banner for all pages.

        This banner may include warnings that the site is still work
        in progress.

        Returns
        -------
        void
            The banner is stored in the `banner` member of the
            `Settings` object.
        """
        Settings = self.Settings
        H = Settings.H
        Messages = self.Messages
        wip = var("devstatus")
        runMode = Settings.runMode

        banner = ""

        if wip == "wip":
            content = H.span(
                dedent(
                    """
                    This site runs in Test Mode.
                    Data you enter can be erased without warning.
                    """
                )
                if runMode == "test"
                else dedent(
                    """
                    This site runs in Pilot Mode.
                    Data you enter will be saved, but might be inaccessible during
                    periods of further development.
                    """
                )
                if runMode == "pilot"
                else dedent(
                    """
                    This site runs in Custom Mode.
                    Modifications may be overwritten if other custom data is imported.
                    """
                )
                if runMode == "custom"
                else dedent(
                    """
                    This site is Work in Progress.
                    """
                )
            )
            dataLink = "«backups»" + H.br()
            if runMode in {"test", "custom"}:
                dataLink += H.a(
                    "reset data",
                    "/collect",
                    title="reset data to initial state",
                    cls="small",
                    **Messages.client(
                        "info",
                        "wait for data reset to complete ...",
                        replace=True,
                    ),
                )
            issueLink = H.a(
                "issues",
                "https://github.com/CLARIAH/pure3dx/issues",
                title="go to the issues on GitHub",
                cls="large",
                target="_blank",
            )
            banner = H.div(
                [content, issueLink, dataLink], id="statusbanner", cls=runMode
            )

        Settings.banner = banner
