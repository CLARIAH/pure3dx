from textwrap import dedent

from control.generic import AttrDict
from control.html import HtmlElements as H


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
            If the viewer is supported, but not the version, the default version
            of that viewer is taken, if there is a default version,
            otherwise the latest supported version.
            If the viewer is not supported, the default viewer is taken.
            See the `fail` parameter above.
        """
        viewers = self.viewers
        if viewer not in viewers:
            viewer = self.viewerDefault
        viewerInfo = viewers[viewer]
        versions = viewerInfo.versions
        defaultVersion = viewerInfo.defaultVersion
        if version not in versions:
            version = defaultVersion if defaultVersion in versions else versions[-1]
        return (viewer, version)

    def getFrame(self, sceneId, actions, viewerActive, versionActive, actionActive):
        """Produces a set of buttons to launch 3D viewers for a scene.

        Parameters
        ----------
        sceneId: ObjectId
            The scene in question.
        actions: iterable of string
            The actions for which we have to create buttons.
            Typically `read` and possibly also `update`.
        viewerActive: string or None
            The viewer in which the scene is currently loaded,
            if any, otherwise None
        versionActive: string or None
            The version of the viewer in which the scene is currently loaded,
            if any, otherwise None
        actionActive: string or None
            The mode in which the scene is currently loaded in the viewer
            (`read` or `update`),
            if any, otherwise None

        Returns
        -------
        string
            The HTML that represents the buttons.
        """
        actionInfo = self.Settings.auth.actions
        viewers = self.viewers

        src = f"/viewer/{viewerActive}/{versionActive}/{actionActive}/{sceneId}"
        frame = H.div(
            H.div(H.iframe(src, cls="previewer"), cls="surround"), cls="model"
        )

        def getViewerButtons(viewer, active):
            activeCls = "active" if active else ""
            return H.span(
                [
                    H.span(viewer, cls=f"vwl {activeCls}"),
                    H.span(
                        [
                            getVersionButtons(
                                viewer, version, active and version == versionActive
                            )
                            for version in viewers[viewer].versions
                        ],
                        cls="vwv",
                    ),
                ],
                cls="vw",
            )

        def getVersionButtons(viewer, version, active):
            nonlocal activeButtons

            activeCls = "active" if active else ""

            versionButtons = H.span(
                [H.span(version, cls=f"vvl {activeCls}")]
                + [
                    getActionButton(
                        viewer, version, action, active and action == actionActive
                    )
                    for action in actions
                    if action != "delete"
                ],
                cls="vv",
            )

            if active:
                activeButtons = versionButtons
            return versionButtons

        def getActionButton(viewer, version, action, active):
            activeCls = "active" if active else ""
            thisActionInfo = AttrDict(actionInfo.get(action, {}))
            acro = thisActionInfo.acro
            name = thisActionInfo.name

            atts = {}

            if active:
                elem = "span"
                href = []
            else:
                elem = "a"
                href = [f"/scenes/{sceneId}/{viewer}/{version}/{action}"]

                if action == "update":
                    viewerHref = f"/viewer/{viewer}/{version}/{action}/{sceneId}"
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
            atts["title"] = f"{name} this scene in {titleFragment}"

            cls = f"button {activeCls} vwb"

            return H.elem(elem, acro, *href, cls=cls, **atts)

        allButtons = [
            getViewerButtons(viewer, viewer == viewerActive) for viewer in viewers
        ]

        activeButtons = [
            H.span(viewerActive, cls="vwla"),
            H.span(versionActive, cls="vvla"),
        ] + [
            getActionButton(viewerActive, versionActive, action, action == actionActive)
            for action in actions
            if action != "delete"
        ]

        buttons = H.details(activeButtons, allButtons, f"vwbuttons-{sceneId}")

        return (frame, buttons)

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
            The chosen mode in which the viewer is launched (`read` or `update`).

        Returns
        -------
        string
            The HTML for the iframe.
        """
        viewers = self.viewers
        Settings = self.Settings
        debugMode = Settings.debugMode
        viewerUrlBase = Settings.viewerUrlBase

        ext = "dev" if debugMode else "min"

        viewerStaticRoot = self.getStaticRoot(viewerUrlBase, action, viewer, version)

        viewerRoot = self.getRoot(urlBase, action, viewer)

        if viewer == "voyager":
            modes = viewers[viewer].modes
            element = modes[action].element
            fileBase = modes[action].fileBase
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
                        H.link(
                            "stylesheet", f"{viewerStaticRoot}/css/{fileBase}.{ext}.css"
                        ),
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
                        "XXXXXXXXXX",
                        root=viewerRoot,
                        document=f"{sceneName}.json",
                        resourceroot=f"{viewerStaticRoot}/",
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
        if not self.check(viewer, version):
            return None

        return f"{viewerUrlBase}/{viewer}/{version}"
