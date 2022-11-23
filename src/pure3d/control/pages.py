from textwrap import dedent

from control.flask import redirectStatus, template, send, stop, getReferrer


TABS = (
    ("home", "Home", True),
    ("about", "About", True),
    ("projects", "3D Projects", True),
    ("directory", "3D Directory", False),
    ("surpriseme", "Surprise Me", True),
    ("advancedsearch", "Advanced Search", False),
)


class Pages:
    def __init__(self, Settings, Viewers, Messages, Content, Auth):
        """Making responses that can be displayed as web pages.

        This class has methods that correspond to routes in the app,
        for which they get the data (using `control.content.Content`),
        which gets then wrapped in HTML.

        It is instantiated by a singleton object.

        Most methods generate a response that contains the content of a complete
        page. For those methods we do not document the return value.

        Some methods return something different.
        If so, it the return value will be documented.

        Parameters
        ----------
        Settings: `control.helpers.generic.AttrDict`
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Viewers: object
            Singleton instance of `control.viewers.Viewers`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        Mongo: object
            Singleton instance of `control.mongo.Mongo`.
        Content: object
            Singleton instance of `control.content.Content`.
        Auth: object
            Singleton instance of `control.auth.Auth`.
        """
        self.Settings = Settings
        self.Viewers = Viewers
        self.Messages = Messages
        Messages.debugAdd(self)
        self.Content = Content
        self.Auth = Auth

    def remaining(self, path):
        Messages = self.Messages

        def splitUrl(url):
            url = url.strip('/')
            parts = url.rsplit("/", 1)
            lastPart = parts[-1]
            firstPart = parts[0] if len(parts) > 1 else ""
            firstPart = f"/{firstPart}"
            return (firstPart, lastPart)

        (firstPath, lastPath) = splitUrl(path)

        if lastPath in {"delete", "edit", "view"}:
            Messages.warning(
                logmsg=f"Not yet implemented /{lastPath}: /{path}",
                msg=f"Not yet implemented: /{lastPath}",
            )
            ref = getReferrer()
            (firstRef, lastRef) = splitUrl(ref)
            back = firstRef if lastRef in {"delete", "edit", "view"} else f"/{ref}"
            return redirectStatus(back, True)

        Messages.warning(logmsg=f"Not found: /{path}")
        stop()

    def home(self):
        """The site-wide home page."""
        left = self.putValues("title@1 + abstract@2")
        return self.page("home", left=left)

    def about(self):
        """The site-wide about page."""
        left = self.putValues("title@1 + abstract@2")
        right = self.putValues("description@2 + provenance@2")
        return self.page("about", left=left, right=right)

    def surprise(self):
        """The "surprise me!" page."""
        Content = self.Content
        surpriseMe = Content.getSurprise()
        left = self.putValues("title@1")
        right = surpriseMe
        return self.page("surpriseme", left=left, right=right)

    def projects(self):
        """The page with the list of projects."""
        Content = self.Content
        projects = Content.getProjects()
        left = self.putValues("title@2") + projects
        return self.page("projects", left=left)

    def projectInsert(self):
        """Inserts a project and shows the new project."""
        Messages = self.Messages
        Content = self.Content
        projectId = Content.insertProject()
        if projectId is None:
            Messages.warning(
                logmsg="Could not create new project",
                msg="failed to create new project",
            )
            newUrl = "/projects"
        else:
            Messages.info(
                logmsg=f"Created project {projectId}", msg="new project created"
            )
            newUrl = f"/projects/{projectId}"
        return redirectStatus(newUrl, projectId is not None)

    def project(self, projectId):
        """The landing page of a project.

        Parameters
        ----------
        projectId: ObjectId
            The project in question.
        """
        Content = self.Content
        editions = Content.getEditions(projectId)
        left = self.putValues("title@3 + creator@4", projectId=projectId) + editions
        right = self.putValues(
            "abstract@4 + description@4 + provenance@4 + instructionalMethod@4",
            projectId=projectId,
        )
        return self.page("projects", left=left, right=right)

    def editionInsert(self, projectId):
        """Inserts an edition into a project and shows the new edition.

        Parameters
        ----------
        projectId: ObjectId
            The project to which the edition belongs.
        """
        Messages = self.Messages
        Content = self.Content
        editionId = Content.insertEdition(projectId)
        if editionId is None:
            Messages.warning(
                logmsg="Could not create new edition",
                msg="failed to create new edition",
            )
            newUrl = f"/projects/{projectId}"
        else:
            Messages.info(
                logmsg=f"Created edition {editionId}", msg="new edition created"
            )
            newUrl = f"/editions/{editionId}"
        return redirectStatus(newUrl, editionId is not None)

    def edition(self, editionId):
        """The landing page of an edition.

        This page contains a list of scenes.
        One of these scenes will be loaded in a 3D viewer.
        It is dependent on defaults which scene in which viewer/version/mode.

        Parameters
        ----------
        editionId: ObjectId
            The edition in question.
            From the edition record we can find the project too.
        """
        Content = self.Content
        editionInfo = Content.getRecord("editions", _id=editionId)
        projectId = editionInfo.projectId
        return self.scenes(projectId, editionId, None, None, None, None)

    def sceneInsert(self, projectId, editionId):
        """Inserts a scene into an edition and shows the new scene.

        Parameters
        ----------
        projectId: ObjectId
            The project to which the scene belongs.
        editionId: ObjectId
            The edition to which the scene belongs.
        """
        Messages = self.Messages
        Content = self.Content
        sceneId = Content.insertScene(projectId, editionId)
        if sceneId is None:
            Messages.warning(
                logmsg="Could not create new scene",
                msg="failed to create new scene",
            )
            newUrl = f"/editions/{editionId}"
        else:
            Messages.info(
                logmsg=f"Created scene {sceneId}", msg="new scene created"
            )
            newUrl = f"/scenes/{sceneId}"
        return redirectStatus(newUrl, sceneId is not None)

    def scene(self, sceneId, viewer, version, action):
        """The landing page of an edition, but with a scene marked as active.

        This page contains a list of scenes.
        One of these scenes is chosen as the active scene and
        will be loaded in a 3D viewer.
        It is dependent on the parameters and/or defaults
        in which viewer/version/mode.

        Parameters
        ----------
        sceneId: ObjectId
            The active scene in question.
            From the scene record we can find the edition and the project too.
        viewer: string or None
            The viewer to use.
        version: string or None
            The version to use.
        action: string or None
            The mode in which the viewer is to be used (`view` or `edit`).
        """
        Content = self.Content
        sceneInfo = Content.getRecord("scenes", _id=sceneId)
        projectId = sceneInfo.projectId
        editionId = sceneInfo.editionId
        return self.scenes(projectId, editionId, sceneId, viewer, version, action)

    def scenes(self, projectId, editionId, sceneId, viewer, version, action):
        """Workhorse for `Pages.edition()` and `Pages.scene()`.

        The common part between the two functions mentioned.
        """
        Content = self.Content
        Auth = self.Auth

        back = self.backLink(projectId)
        self.debug(f"SCENES: {editionId=}")
        action = Auth.makeSafe("editions", editionId, action)
        sceneMaterial = (
            ""
            if action is None
            else Content.getScenes(
                projectId,
                editionId,
                sceneId=sceneId,
                viewer=viewer,
                version=version,
                action=action,
            )
        )
        left = (
            back
            + self.putValues("title@4", projectId=projectId, editionId=editionId)
            + sceneMaterial
        )
        right = self.putValues(
            "abstract@5 + description@5 + provenance@5 + instructionalMethod@5",
            projectId=projectId,
            editionId=editionId,
        )
        return self.page("projects", left=left, right=right)

    def viewerFrame(self, sceneId, viewer, version, action):
        """The page loaded in an iframe where a 3D viewer operates.

        Parameters
        ----------
        sceneId: ObjectId
            The scene that is shown.
        viewer: string or None
            The viewer to use.
        version: string or None
            The version to use.
        action: string or None
            The mode in which the viewer is to be used (`view` or `edit`).
        """
        Content = self.Content
        Viewers = self.Viewers
        Auth = self.Auth

        sceneInfo = Content.getRecord("scenes", _id=sceneId)
        sceneName = sceneInfo.name

        projectId = sceneInfo.projectId
        editionId = sceneInfo.editionId

        urlBase = f"projects/{projectId}/editions/{editionId}/"

        action = Auth.makeSafe("scenes", sceneId, action)

        viewerCode = (
            ""
            if action is None
            else Viewers.genHtml(urlBase, sceneName, viewer, version, action)
        )
        return template("viewer", viewerCode=viewerCode)

    def viewerResource(self, path):
        """Components requested by viewers.

        This is the javascript code, the css, and other resources
        that are part of the 3D viewer software.

        Parameters
        ----------
        path: string
            Path on the file system under the viewers base directory
            where the resource resides.

        Returns
        -------
        response
            The response consists of the contents of the
            file plus headers derived from the path.
            If the file does not exists, a 404 is returned.
        """
        Content = self.Content

        dataPath = Content.getViewerFile(path)
        return send(dataPath)

    def dataProjects(self, path, projectId, editionId=None):
        """Data content requested by viewers.

        This is the material belonging to the scene,
        the scene json itself and additional resources,
        that are part of the user contributed content that is under
        control of the viewer: annotations, media, etc.

        Parameters
        ----------
        path: string
            Path on the file system under the data directory
            where the resource resides.
            The path is relative to the project, and, if given, the edition.
        projectId: ObjectId
            The id of a project under which the resource is to be found.
        editionId: ObjectId, optional None
            If not None, the name of an edition under which the resource
            is to be found.

        Returns
        -------
        response
            The response consists of the contents of the
            file plus headers derived from the path.
            If the file does not exists, a 404 is returned.
        """
        Content = self.Content

        dataPath = Content.getData(path, projectId, editionId=editionId)
        return send(dataPath)

    def page(self, url, left=None, right=None):
        """Workhorse function to get content on the page.

        Parameters
        ----------
        url: string
            Initial part of the url that triggered the page function.
            This part is used to make one of the tabs on the web page active.
        left: string, optional None
            Content for the left column of the page.
        right: string, optional None
            Content for the right column of the page.
        """
        Settings = self.Settings
        Messages = self.Messages
        Auth = self.Auth

        navigation = self.navigation(url)
        loginWidget = Auth.wrapLogin()

        return template(
            "index",
            versionInfo=Settings.versionInfo,
            navigation=navigation,
            materialLeft=left or "",
            materialRight=right or "",
            messages=Messages.generateMessages(),
            loginWidget=loginWidget,
        )

    def authWebdav(self, projectId, editionId, path, action):
        """Authorises a webdav request.

        When a viewer makes a WebDAV request to the server,
        that request is first checked here for authorisation.

        See `control.webdavapp.dispatchWebdav()`.

        Parameters
        ----------
        projectId: ObjectId
            The project in question.
        editionId: ObjectId
            The edition in question.
        path: string
            The path relative to the directory of the edition.
        action: string
            The operation that the WebDAV request wants to do on the data
            (`view` or `edit`).

        Returns
        -------
        boolean
            Whether the action is permitted on ths data by the current user.
        """
        Messages = self.Messages
        Auth = self.Auth

        permitted = Auth.authorise("editions", recordId=editionId, action=action)
        if not permitted:
            User = Auth.myDetails()
            user = User.sub
            name = User.nickname
            Messages.info(
                logmsg=f"WEBDAV unauthorised by user {name} ({user})"
                f" on project {projectId} edition {editionId} path {path}"
            )
        return permitted

    def navigation(self, url):
        """Generates the navigation controls.

        Especially the tab bar.

        Parameters
        ----------
        url: string
            Initial part of the url on the basis of which one of the
            tabs can be made active.

        Returns
        -------
        string
            The HTML of the navigation.
        """
        search = dedent(
            """
            <span class="search-bar">
                <input
                    type="search"
                    name="search"
                    placeholder="search item"
                    class="button disabled"
                >
                <input type="submit" value="Search" class="button disabled">
            </span>
            """
        )
        html = ["""<div class="tabs">"""]

        for (tab, label, enabled) in TABS:
            active = "active" if url == tab else ""
            elem = "a" if enabled else "span"
            href = f""" href="/{tab}" """ if enabled else ""
            cls = active if enabled else "disabled"
            html.append(
                dedent(
                    f"""
                    <{elem}
                        {href}
                        class="button large {cls}"
                    >{label}</{elem}>
                    """
                )
            )
        html.append(search)
        html.append("</div>")
        return "\n".join(html)

    def backLink(self, projectId):
        """Makes a link to the landing page of a project.

        Parameters
        ----------
        projectId: ObjectId
            The project in question.
        """
        projectUrl = f"/projects/{projectId}"
        cls = """ class="button" """
        href = f""" href="{projectUrl}" """
        text = """back to the project page"""
        return f"""<p><a {cls} {href}>{text}</a></p>"""

    def putValues(self, fieldSpecs, projectId=None, editionId=None):
        """Puts several pieces of metadata on the web page.

        Parameters
        ----------
        fieldSpecs: string
            `,`-separated list of fieldSpecs

        Returns
        -------
        string
            The join of the individual results of retrieving metadata value.
        """
        Content = self.Content

        return "\n".join(
            Content.getValue(
                key,
                projectId=projectId,
                editionId=editionId,
                level=level,
            )
            or ""
            for (key, level) in (
                fieldSpec.strip().split("@", 1) for fieldSpec in fieldSpecs.split("+")
            )
        )
