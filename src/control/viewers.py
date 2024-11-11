from textwrap import dedent

from .generic import AttrDict, attResolve


class Viewers:
    def __init__(self, Settings, Messages):
        """Knowledge of the installed 3D viewers.

        This class knows which (versions of) viewers are installed,
        and has the methods to invoke them.

        It is instantiated by a singleton object.

        Parameters
        ----------
        Settings: AttrDict
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        """
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)
        self.viewers = Settings.viewers
        self.viewerActions = Settings.viewerActions
        self.viewerDefault = Settings.viewerDefault

    def addAuth(self, Auth):
        """Give this object a handle to the Auth object.

        The Viewers and Auth objects need each other, so one of them must
        be given the handle to the other after initialization.
        """
        self.Auth = Auth

    def check(self, viewer, version):
        """Checks whether a viewer version exists.

        Given a viewer and a version, it is looked up whether the code
        is present.
        If not, reasonable defaults returned instead by default.

        Parameters
        ----------
        viewer: string
            The viewer in question.
        version: string
            The version of the viewer in question.

        Returns
        -------
        string | void
            The version is returned unmodified if that viewer
            version is supported.
            If the viewer is supported, but not the version, the default version
            of that viewer is taken, if there is a default version,
            otherwise the latest supported version.
            If the viewer is not supported, None is returned.
        """
        viewers = self.viewers

        if viewer not in viewers:
            return None

        viewerInfo = viewers[viewer]
        versions = viewerInfo.versions
        defaultVersion = viewerInfo.defaultVersion
        if version not in versions:
            version = defaultVersion
        return version

    def getViewInfo(self, edition):
        """Gets viewer-related info that an edition is made with.

        Parameters
        ----------
        edition: AttrDict
            The edition record.

        Returns
        -------
        tuple of string
            * The name of the viewer
            * The name of the scene

        """
        viewerDefault = self.viewerDefault

        editionId = edition._id
        if editionId is None:
            return (viewerDefault, None)

        editionSettings = edition.settings or AttrDict()
        authorTool = editionSettings.authorTool or AttrDict()
        viewer = authorTool.name or viewerDefault
        sceneFile = authorTool.sceneFile

        return (viewer, sceneFile)

    def getFrame(
        self, edition, actions, viewer, versionActive, actionActive, sceneExists
    ):
        """Produces a set of buttons to launch 3D viewers for a scene.

        Make sure that if there is no scene file present, no viewer will be opened.

        Parameters
        ----------
        edition: AttrDict
            The edition in question.
        actions: iterable of string
            The actions for which we have to create buttons.
            Typically `read` and possibly also `update`.
            Actions that are not recognized as viewer actions
            will be filtered out, such as `create` and `delete`.
        viewer: string
            The viewer in which the scene is currently loaded.
        versionActive: string | void
            The version of the viewer in which the scene is currently loaded,
            if any, otherwise None
        actionActive: string | void
            The mode in which the scene is currently loaded in the viewer
            (`read` or `update`),
            if any, otherwise None
        sceneExists: boolean
            Whether the scene file exists.

        Returns
        -------
        string
            The HTML that represents the buttons.
        """
        Settings = self.Settings
        H = Settings.H
        actionInfo = self.viewerActions
        viewers = self.viewers

        filteredActions = {a for a in actions if a in actionInfo and a != "create"}
        versionActive = self.check(viewer, versionActive)

        editionId = edition._id
        if editionId is None:
            return ("", "")

        create = "/update" if sceneExists else "/create"

        src = f"/viewer/{versionActive}/{actionActive}/{editionId}{create}"
        frame = H.div(
            H.div(H.iframe(src, cls="previewer"), cls="surround"), cls="model"
        )

        def getViewerButtons(vw):
            """Internal function.

            Returns
            -------
            string
                HTML for the buttons to launch a viewer.
            """
            openAtt = vw == viewer

            versions = viewers[vw].versions
            if len(versions) == 1:
                version = versions[0]
                return H.table(
                    [
                        getVersionButtons(
                            version,
                            version == versionActive,
                            versionAmount=len(versions),
                            withViewer=True,
                            withVersion=True,
                            # withViewer=not pilotMode,
                            # withVersion=not pilotMode,
                        )
                    ],
                    [],
                    cls="vwv",
                )

            (latest, previous) = (versions[0:1], versions[1:])

            openAtt = vw == viewer and len(previous) and versionActive in previous

            return H.details(
                H.table(
                    [
                        getVersionButtons(
                            version,
                            version == versionActive,
                            versionAmount=len(versions),
                            withViewer=True,
                        )
                        for version in latest
                    ],
                    [],
                    cls="vwv",
                ),
                H.table(
                    [],
                    [
                        getVersionButtons(
                            version, version == versionActive, withViewer=False
                        )
                        for version in previous
                    ],
                    cls="vwv",
                ),
                f"vwbuttons-{editionId}",
                cls="vw",
                open=openAtt,
            )

        def getVersionButtons(
            version, active, versionAmount=None, withViewer=False, withVersion=True
        ):
            """Internal function.

            Parameters
            ----------
            version: string
                The version of the viewer.
            active: boolean
                Whether that version of that viewer is currently active.
            versionAmount: int, optional None
                If passed, contains the number of versions and displays it.
            withViewer: boolean, optional False
                Whether to show the viewer name in the first column.
            withVersion: boolean, optional True
                Whether to show the version in the second column.

            Returns
            -------
            string
                HTML for the buttons to launch a specific version of a viewer.
            """
            activeRowCls = "activer" if active else ""

            plural = "" if versionAmount == 2 else "s"
            title = (
                f"click to show previous {versionAmount - 1} {viewer} version{plural}"
                if versionAmount and versionAmount > 1
                else f"no previous {viewer} versions"
            )

            return (
                [
                    (viewer if withViewer else H.nbsp, dict(cls="vwc", title=title)),
                    (
                        version if withVersion else H.nbsp,
                        dict(cls="vvl vwc", title=title),
                    ),
                ]
                + [
                    getActionButton(
                        version, action, disabled=active and action == actionActive
                    )
                    for action in sorted(filteredActions)
                ],
                dict(cls=activeRowCls),
            )

        def getActionButton(version, action, disabled=False):
            """Internal function.

            Parameters
            ----------
            version: string
                The version of the viewer.
            action: string
                Whether to launch the viewer for `read` or for `update`.
            disabled: boolean, optional Fasle
                Whether to show the button as disabled

            Returns
            -------
            string
                HTML for the buttons to launch a specific version of a viewer
                for a specific action.
            """
            atts = {}

            href = None if disabled else f"/edition/{editionId}/{version}/{action}"

            if action == "update":
                viewerHref = f"/viewer/{version}/{action}/{editionId}{create}"
                atts["onclick"] = dedent(
                    f"""
                    window.open(
                        '{viewerHref}',
                        'newwindow',
                        width=window.innerWidth,
                        height=window.innerHeight
                    );
                    return false;
                    """
                )

            titleFragment = "a new window" if action == "update" else "place"

            createMode = action == "update" and not sceneExists
            action = "create" if createMode else action
            thisActionInfo = actionInfo.get(action, AttrDict())
            name = thisActionInfo.name
            atts["title"] = f"{name} scene in {titleFragment}"

            disabledCls = "disabled" if disabled else ""
            activeCellCls = "activec" if disabled else ""
            cls = f"button vwb {disabledCls}"

            return (
                H.iconx(action, text=name, href=href, cls=cls, **atts),
                dict(cls=f"vwc {activeCellCls}"),
            )

        allButtons = H.div([getViewerButtons(vw) for vw in viewers])

        return (frame if sceneExists else "", allButtons)

    def genHtml(self, urlBase, sceneFile, viewer, version, action, subMode):
        """Generates the HTML for the viewer page that is loaded in an iframe.

        When a scene is loaded in a viewer, it happens in an iframe.
        Here we generate the complete HTML for such an iframe.

        Parameters
        ----------
        urlBase: string
            The first part of the root url that is given to the viewer.
            The viewer code uses this to retrieve additional information.
            The root url will be completed with the `action` and the `viewer`.
        sceneFile: string
            The name of the scene file in the file system.
        viewer: string
            The chosen viewer.
        version: string
            The chosen version of the viewer.
        action: string
            The chosen mode in which the viewer is launched (`read` or `update`).
        subMode: string | None
            The sub mode in which the viewer is to be used (`update` or `create`).

        Returns
        -------
        string
            The HTML for the iframe.
        """
        Settings = self.Settings
        H = Settings.H
        debugMode = Settings.debugMode
        viewerUrlBase = Settings.viewerUrlBase
        viewers = self.viewers

        ext = "dev" if debugMode else "min"

        viewerStaticRoot = self.getStaticRoot(viewerUrlBase, action, viewer, version)

        viewerRoot = self.getRoot(urlBase, action, viewer)

        if viewer == "voyager":
            modes = viewers[viewer].modes
            modeProps = modes[action]
            element = modeProps.element
            fileBase = modeProps.fileBase
            subModes = modeProps.subModes or AttrDict()
            atts = attResolve(subModes[subMode] or AttrDict(), version)
            if subMode != "create":
                atts["document"] = sceneFile

            return H.content(
                H.head(
                    [
                        H.meta(charset="utf-8"),
                        H.link(
                            "shortcut icon",
                            f"{viewerStaticRoot}/favicon.png",
                            tp="image/png",
                        ),
                        H.link("stylesheet", f"{viewerStaticRoot}/fonts/fonts.css"),
                        H.script(
                            "",
                            defer=True,
                            src=f"{viewerStaticRoot}/js/{fileBase}.{ext}.js",
                        ),
                    ]
                ),
                H.body(
                    H.elem(
                        element,
                        "",
                        root=viewerRoot,
                        resourceroot=f"{viewerStaticRoot}/",
                        **atts,
                    )
                ),
            )
        else:
            return H.content(
                H.head(H.meta(charset="utf-8")),
                H.body(H.p(f"Unsupported viewer: {viewer}")),
            )

    def getRoot(self, urlBase, action, viewer):
        """Composes the root url for a viewer.

        The root url is passed to a viewer instance as the url that
        the viewer can use to fetch its data.
        It is not meant for the static data that is part of the viewer software,
        but for the model related data that the viewer is going to display.

        See `getStaticRoot()` for the url meant for getting parts of the
        viewer software.

        Parameters
        ----------
        urlBase: string
            The first part of the root url, depending
            on the project and edition.
        action: string
            The mode in which the viewer is opened.
            Depending on the mode, the viewer code may communicate with the server
            with different urls.
            For example, for the voyager,
            the `read` mode (voyager-explorer) uses ordinary HTTP requests,
            but the `update` mode (voyager-story) uses WebDAV requests.

            So this app points voyager-explorer to a root url starting with `/data`,
            and voyager-story to a root url starting with `/webdav`.

            These prefixes of the urls can be configured per viewer
            in the viewer configuration in `yaml/viewers.yml`.
        """
        viewers = self.viewers

        if viewer not in viewers:
            return None

        modes = viewers[viewer].modes

        thisMode = modes[action] or modes.read
        prefix = thisMode.prefix

        return f"{prefix}/{urlBase}"

    def getStaticRoot(self, viewerUrlBase, action, viewer, version):
        """Composes the static root url for a viewer.

        The static root url is passed to a viewer instance as the url that the
        viewer can use to fetch its assets.
        It is not meant for the model related data, but for the parts of the
        viewer software that it needs to get from the server.

        See `getRoot()` for the url meant for getting model-related data.

        Parameters
        ----------
        viewerUrlBase: string
            The first part of the root url, depending
            on the project and edition.
        action: string
            The mode in which the viewer is opened.
            Depending on the mode, the viewer code may communicate with the server
            with different urls.
            For example, for the voyager,
            the `read` mode (voyager-explorer) uses ordinary HTTP requests,
            but the `update` mode (voyager-story) uses WebDAV requests.

            So this app points voyager-explorer to a root url starting with `/data`,
            and voyager-story to a root url starting with `/webdav`.

            These prefixes of the urls can be configured per viewer
            in the viewer configuration in `yaml/viewers.yml`.
        """
        if not self.check(viewer, version):
            return None

        return f"{viewerUrlBase}/{viewer}/{version}"
