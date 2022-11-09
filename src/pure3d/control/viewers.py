from textwrap import dedent


class Viewers:
    def __init__(self, Settings):
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
        self.viewers = Settings.viewers
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
        If not, reasonable defaults are returned instead.

        Parameters
        ----------
        viewer: string
            The viewer in question.
        version: string
            The version of the viewer in question.

        Returns
        -------
        tuple
            The viewer and version are returned unmodified if that viewer
            version is supported.
            If the viewer is supported, but not the version, the latest
            supported version of that viewer is taken.
            If the viewer is not supported, the default viewer is taken.
        """
        viewers = self.viewers
        if viewer not in viewers:
            viewer = self.viewerDefault
        versions = viewers[viewer].versions
        if version not in versions:
            version = versions[-1]
        return (viewer, version)

    def getButtons(
        self, sceneId, actions, isSceneActive, viewerActive, versionActive, actionActive
    ):
        """Produces a set of buttons to launch 3D viewers for a scene.

        Parameters
        ----------
        sceneId: ObjectId
            The scene in question.
        actions: iterable of string
            The actions for which we have to create buttons.
            Typically `view` and possibly also `edit`.
        isSceneActive: boolean
            Whether this scene is active, i.e. loaded in a 3D viewer.
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

        buttons = []
        frame = None

        for viewer in viewers:
            isViewerActive = isSceneActive and viewer == viewerActive
            vwActive = "active" if isViewerActive else ""
            buttons.append(
                dedent(
                    f"""<span class="vw"><span class="vwl {vwActive}">{viewer}</span>
                        <span class="vwv">
                    """
                )
            )

            for version in viewers[viewer].versions:
                isVersionActive = isViewerActive and version == versionActive
                vsActive = "active" if isVersionActive else ""
                buttons.append(
                    f"""<span class="vv"><span class="vvl {vsActive}">{version}</span>"""
                )
                for action in actions:
                    isActionActive = isVersionActive and action == actionActive
                    btActive = "active" if isActionActive else ""

                    elem = "a"
                    attStr = ""

                    if btActive:
                        frame = dedent(
                            f"""
                            <div class="model">
                                <iframe
                                  class="previewer"
                                  src="/viewer/{viewer}/{version}/{action}/{sceneId}"/>
                                </iframe>
                            </div>
                            """
                        )
                        elem = "span"
                    else:
                        attStr = (
                            f' href="/scenes/{sceneId}/{viewer}/{version}/{action}" '
                        )

                    cls = f"button {btActive} vwb"
                    begin = f"""<{elem} class="{cls}" {attStr}>"""
                    end = f"</{elem}>"
                    buttons.append(f"{begin}{action}{end}")
                buttons.append("""</span> """)
            buttons.append("""</span></span> """)

        return (frame, "\n".join(buttons))

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

        viewerStatic = f"{viewerUrlBase}/{viewer}/{version}"
        viewerRoot = self.getRoot(urlBase, action, viewer)

        if viewer == "voyager":
            element = "explorer" if action == "view" else "story"
            return dedent(
                f"""
                <head>
                <meta charset="utf-8">
                <link
                  href="{viewerStatic}/fonts/fonts.css"
                  rel="stylesheet"
                />
                <link
                  rel="shortcut icon"
                  type="image/png"
                  href="{viewerStatic}/favicon.png"
                />
                <link
                  rel="stylesheet"
                  href="{viewerStatic}/css/voyager-{element}.{ext}.css"
                />
                <script
                  defer
                  src="{viewerStatic}/js/voyager-{element}.{ext}.js">
                </script>
                </head>
                <body>
                <voyager-{element}
                  root="{viewerRoot}"
                  document="{sceneName}.json"
                  resourceroot="{viewerStatic}"
                > </voyager-{element}>
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
                """
            )

    def getRoot(self, urlBase, action, viewer):
        """Composes the root url for a viewer.

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
