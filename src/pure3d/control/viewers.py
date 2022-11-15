from textwrap import dedent


class Viewers:
    def __init__(self, Settings, Messages):
        """Knowledge of the installed 3D viewers.

        This class knows which (versions of) viewers are installed,
        and has the methods to invoke them.

        It is instantiated by a singleton object.

        Parameters
        ----------
        Settings: `control.helpers.generic.AttrDict`
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        """
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)
        self.viewers = Settings.viewers
        self.viewerDefault = Settings.viewerDefault

    def addAuth(self, Auth):
        """Give this object a handle to the Auth object.

        The Viewers and Auth objects need each other, so one of them must
        be given the handle to the other after initialization.
        """
        self.Auth = Auth

    def check(self, viewer, version, fail=False):
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
        fail: boolean, optional False
            If true, returns True or False, depending on whther the
            given viewer-version combination is supported.

        Returns
        -------
        tuple or boolean
            The viewer and version are returned unmodified if that viewer
            version is supported.
            If the viewer is supported, but not the version, the latest
            supported version of that viewer is taken.
            If the viewer is not supported, the default viewer is taken.
            See the `fail` parameter above.
        """
        viewers = self.viewers
        if viewer not in viewers:
            viewer = self.viewerDefault
        versions = viewers[viewer].versions
        if version not in versions:
            version = versions[-1]
        return (viewer, version)

    def getFrame(self, sceneId, actions, viewerActive, versionActive, actionActive):
        """Produces a set of buttons to launch 3D viewers for a scene.

        Parameters
        ----------
        sceneId: ObjectId
            The scene in question.
        actions: iterable of string
            The actions for which we have to create buttons.
            Typically `view` and possibly also `edit`.
        viewerActive: string or None
            The viewer in which the scene is currently loaded,
            if any, otherwise None
        versionActive: string or None
            The version of the viewer in which the scene is currently loaded,
            if any, otherwise None
        actionActive: string or None
            The mode in which the scene is currently loaded in the viewer
            (`view` or `edit`),
            if any, otherwise None

        Returns
        -------
        string
            The HTML that represents the buttons.
        """
        viewers = self.viewers

        frame = dedent(
            f"""
            <div class="model">
                <div class="surround">
                <iframe
                  class="previewer"
                  src="/viewer/{viewerActive}/{versionActive}/{actionActive}/{sceneId}"/></iframe>
                </div>
            </div>
            """
        )

        buttons = []

        def getViewerButtons(viewer, active):
            activeCls = "active" if active else ""
            buttons = []
            buttons.append(
                dedent(
                    f"""<span class="vw"><span class="vwl {activeCls}">{viewer}</span>
                        <span class="vwv">
                    """
                )
            )
            for version in viewers[viewer].versions:
                isVersionActive = active and version == versionActive
                buttons.append(getVersionButtons(viewer, version, isVersionActive))

            buttons.append("""</span></span> """)
            return "\n".join(buttons)

        def getVersionButtons(viewer, version, active):
            nonlocal activeButtons

            activeCls = "active" if active else ""
            buttons = []
            buttons.append(
                f"""<span class="vv"><span class="vvl {activeCls}">{version}</span>"""
            )
            for action in actions:
                isActionActive = active and action == actionActive
                buttons.append(getActionButton(viewer, version, action, isActionActive))

            buttons.append("""</span> """)
            versionButtons = "\n".join(buttons)
            if active:
                activeButtons = versionButtons
            return versionButtons

        def getActionButton(viewer, version, action, active):
            activeCls = "active" if active else ""

            if activeCls:
                attStr = ""
                elem = "span"
            else:
                elem = "a"
                attStr = f' href="/scenes/{sceneId}/{viewer}/{version}/{action}" '

            cls = f"button {activeCls} vwb"
            begin = f"""<{elem} class="{cls}" {attStr}>"""
            end = f"</{elem}>"
            return f"{begin}{action}{end}"

        for viewer in viewers:
            isViewerActive = viewer == viewerActive
            buttons.append(getViewerButtons(viewer, isViewerActive))

        allButtons = "\n".join(buttons)

        activeButtons = []
        for action in actions:
            activeButtons.append(
                getActionButton(
                    viewerActive, versionActive, action, action == actionActive
                )
            )
        activeButtons = "\n".join(activeButtons)

        activeButtons = dedent(
            f"""
            <span class="vwla">{viewerActive}</span>
            <span class="vvla">{versionActive}</span>
            {activeButtons}
            """
        )

        buttonsHtml = dedent(
            f"""
            <details>
                <summary>{activeButtons}</summary>
                {allButtons}
            </details>
            """
        )

        return (frame, buttonsHtml)

    def genHtml(self, urlBase, sceneName, viewer, version, action):
        """Generates the HTML for the viewer page that is loaded in an iframe.

        When a scene is loaded in a viewer, it happens in an iframe.
        Here we generate the complete HTML for such an iframe.

        Parameters
        ----------
        urlBase: string
            The first part of the root url that is given to the viewer.
            The viewer code uses this to retrieve additional information.
            The root url will be completed with the `action` and the `viewer`.
        sceneName: string
            The name of the scene in the file system. The viewer will find the
            scene json file by this name.
        viewer: string
            The chosen viewer.
        version: string
            The chosen version of the viewer.
        action: string
            The chosen mode in which the viewer is launched (`view` or `edit`).

        Returns
        -------
        string
            The HTML for the iframe.
        """
        Settings = self.Settings
        debugMode = Settings.debugMode
        viewerUrlBase = Settings.viewerUrlBase

        ext = "dev" if debugMode else "min"

        viewerStaticRoot = self.getStaticRoot(viewerUrlBase, action, viewer, version)

        viewerRoot = self.getRoot(urlBase, action, viewer)

        if viewer == "voyager":
            element = "explorer" if action == "view" else "story"
            return dedent(
                f"""
                <head>
                <meta charset="utf-8">
                <!--<link
                  rel="stylesheet"
                  href="{viewerStaticRoot}/fonts/fonts.css"
                >
                <link
                  rel="shortcut icon"
                  type="image/png"
                  href="{viewerStaticRoot}/favicon.png"
                >-->
                <link
                  rel="stylesheet"
                  href="{viewerStaticRoot}/css/voyager-{element}.{ext}.css"
                >
                <script
                  defer
                  src="{viewerStaticRoot}/js/voyager-{element}.{ext}.js"></script>
                </head>
                <body>
                <voyager-{element}
                  root="{viewerRoot}"
                  document="{sceneName}.json"
                  resourceroot="{viewerStaticRoot}/">
                </voyager-{element}>
                </body>
                """
            )
        else:
            return dedent(
                f"""
                <head>
                <meta charset="utf-8">
                </head>
                <body>
                <p>Unsupported viewer: {viewer}</p>
                </body>
                """.strip()
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
            the `view` mode (voyager-explorer) uses ordinary HTTP requests,
            but the `edit` mode (voyager-story) uses WebDAV requests.

            So this app points voyager-explorer to a root url starting with `/data`,
            and voyager-story to a root url starting with `/webdav`.

            These prefixes of the urls can be configured per viewer
            in the viewer configuration in `yaml/viewers.yml`.
        """
        viewers = self.viewers

        if viewer not in viewers:
            return None

        modes = viewers[viewer].modes

        prefix = modes[action] or modes.view

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
        urlBase: string
            The first part of the root url, depending
            on the project and edition.
        action: string
            The mode in which the viewer is opened.
            Depending on the mode, the viewer code may communicate with the server
            with different urls.
            For example, for the voyager,
            the `view` mode (voyager-explorer) uses ordinary HTTP requests,
            but the `edit` mode (voyager-story) uses WebDAV requests.

            So this app points voyager-explorer to a root url starting with `/data`,
            and voyager-story to a root url starting with `/webdav`.

            These prefixes of the urls can be configured per viewer
            in the viewer configuration in `yaml/viewers.yml`.
        """
        if not self.check(viewer, version):
            return None

        return f"{viewerUrlBase}/{viewer}/{version}"
