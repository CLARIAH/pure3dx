from textwrap import dedent


class Viewers:
    def __init__(self, config):
        """Knowledge of the installed 3D viewers.

        This class knows which (versions of) viewers are installed,
        and has the methods to invoke them.

        It is instantiated by a singleton object.

        Parameters
        ----------
        config: AttrDict
            App-wide configuration data obtained from
            `control.config.Config.config`.
        """
        self.config = config
        self.viewers = config.viewers
        self.viewerDefault = config.viewerDefault

    def addAuth(self, Auth):
        self.Auth = Auth

    def check(self, viewer, version):
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
        viewers = self.viewers

        buttons = []
        frame = ""

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
        config = self.config
        debugMode = config.debugMode
        viewerUrlBase = config.viewerUrlBase

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
        viewers = self.viewers

        if viewer not in viewers:
            return None

        modes = viewers[viewer].modes

        prefix = modes[action] or modes.view

        return f"{prefix}/{urlBase}"
