from control.flask import redirectStatus, template, send, stop, getReferrer
from control.html import HtmlElements as H


class Pages:
    def __init__(self, Settings, Viewers, Messages, Collect, Content, Auth):
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
        Settings: `control.generic.AttrDict`
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Viewers: object
            Singleton instance of `control.viewers.Viewers`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        Mongo: object
            Singleton instance of `control.mongo.Mongo`.
        Collect: object
            Singleton instance of `control.collect.Collect`.
        Content: object
            Singleton instance of `control.content.Content`.
        Auth: object
            Singleton instance of `control.auth.Auth`.
        """
        self.Settings = Settings
        self.Viewers = Viewers
        self.Messages = Messages
        Messages.debugAdd(self)
        self.Collect = Collect
        self.Content = Content
        self.Auth = Auth

    def collect(self):
        """Data reset: collect the example data again."""
        Collect = self.Collect
        Messages = self.Messages

        Collect.fetch()
        Messages.info(msg="data reset done!")
        ref = getReferrer()
        return redirectStatus(ref, True)

    def home(self):
        """The site-wide home page."""
        left = self.putValues("siteTitle@1 + abstract@2")
        return self.page("home", left=left)

    def about(self):
        """The site-wide about page."""
        left = self.putValues("siteTitle@1 + abstract@2")
        right = self.putValues("description@2 + provenance@2")
        return self.page("about", left=left, right=right)

    def surprise(self):
        """The "surprise me!" page."""
        Content = self.Content
        surpriseMe = Content.getSurprise()
        left = self.putValues("siteTitle@1")
        right = surpriseMe
        return self.page("surpriseme", left=left, right=right)

    def projects(self):
        """The page with the list of projects."""
        Content = self.Content
        projects = Content.getProjects()
        left = self.putValues("siteTitle@2") + projects
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
        editionHeading = H.h(3, "Editions")
        left = (
            self.putValues("title@3 + creator@0", projectId=projectId)
            + editionHeading
            + editions
        )
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

    def edition(self, editionId, version, action):
        """The landing page of an edition, possibly with a scene marked as active.

        An edition knows the scene it should display and the viewer that was
        used to create the scene.

        If action is None, only the edition logo will be shown, no viewer
        will be loaded.

        If action is not None, its value determines which viewer will be loaded
        in the 3D viewer.
        It is dependent on the parameters and/or defaults
        in which viewer/version/mode.

        If version is not None, this will override the default version.

        Parameters
        ----------
        editionId: ObjectId
            The editionin quesion.
            From the scene record we can find the edition and the project too.
        version: string or None
            The viewer version to use.
        action: string or None
            The mode in which the viewer is to be used (`read` or `update`).
        """
        Content = self.Content
        Auth = self.Auth

        editionInfo = Content.getItem("edition", _id=editionId)
        editionSettings = editionInfo.get("settings", {})
        authorTool = editionSettings.get("authorTool")
        sceneName = authorTool.sceneFile
        projectId = editionInfo.projectId
        breadCrumb = self.breadCrumb(projectId)
        action = Auth.makeSafe("edition", editionId, action)
        sceneMaterial = (
            ""
            if action is None
            else Content.getScene(
                editionId,
                version=version,
                action=action,
            )
        )
        left = (
            breadCrumb
            + self.putValues("title@4", projectId=projectId, editionId=editionId)
            + H.h(4, "Model files")
            + H.div(
                self.putUpload("model", projectId=projectId, editionId=editionId),
                cls="modelfile",
            )
            + H.h(4, "Scene")
            + H.div(
                self.putUpload(
                    "scene",
                    fileName=sceneName,
                    projectId=projectId,
                    editionId=editionId,
                ),
                cls="scenefile",
            )
            + sceneMaterial
        )
        right = self.putValues(
            "abstract@5 + description@5 + provenance@5 + instructionalMethod@5",
            projectId=projectId,
            editionId=editionId,
        )
        return self.page("projects", left=left, right=right)

    def viewerFrame(self, editionId, version, action):
        """The page loaded in an iframe where a 3D viewer operates.

        Parameters
        ----------
        editionId: ObjectId
            The edition that is shown.
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

        viewerDefault = Viewers.viewerDefault
        editionInfo = Content.getItem("edition", _id=editionId)
        projectId = editionInfo.projectId
        editionSettings = editionInfo.get("settings", {})
        authorTool = editionSettings.get("authorTool")
        viewer = authorTool.get("name", viewerDefault)
        sceneName = authorTool.sceneFile

        urlBase = f"projects/{projectId}/editions/{editionId}/"

        action = Auth.makeSafe("edition", editionId, action)

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

    def dataProjects(self, path, projectId=None, editionId=None):
        """Data content requested directly from the file repository.

        This is

        * the material requested by the viewers:
          the scene json itself and additional resources,
          that are part of the user contributed content that is under
          control of the viewer: annotations, media, etc.
        * icons for the site, projects, and editions

        Parameters
        ----------
        path: string
            Path on the file system under the data directory
            where the resource resides.
            The path is relative to the project, and, if given, the edition.
        projectId: ObjectId, optional None
            The id of a project under which the resource is to be found.
            If None, it is site-wide material.
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

        dataPath = Content.getData(path, projectId=projectId, editionId=editionId)
        return send(dataPath)

    def upload(self, table, recordId, key, path):
        Content = self.Content

        parts = path.rstrip("/").rsplit("/", 1)
        fileName = parts[-1]
        path = parts[0] if len(parts) == 2 else ""

        return Content.save(table, recordId, key, path, fileName)

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

        permitted = Auth.authorise(
            "edition",
            recordId=editionId,
            action=action,
            project=projectId,
        )
        if not permitted:
            User = Auth.myDetails()
            user = User.sub
            name = User.nickname
            Messages.info(
                logmsg=f"WEBDav unauthorised by user {name} ({user})"
                f" on project {projectId} edition {editionId} path {path}"
            )
        return permitted

    def remaining(self, path):
        """When the url of the request is not recognized.

        Parameters
        ----------
        path: string
            The url (without leading /) that is not recognized.

        Returns
        -------
        response
            Either a redirect to the referred, for some
            recognized urls that correspond to not-yet
            implemented one. Or a 404 abort for all other
            cases.
        """
        Messages = self.Messages

        def splitUrl(url):
            url = url.strip("/")
            parts = url.rsplit("/", 1)
            lastPart = parts[-1]
            firstPart = parts[0] if len(parts) > 1 else ""
            firstPart = f"/{firstPart}"
            return (firstPart, lastPart)

        (firstPath, lastPath) = splitUrl(path)

        if lastPath in {"read", "update", "delete"}:
            Messages.warning(
                logmsg=f"Not yet implemented /{lastPath}: /{path}",
                msg=f"Not yet implemented: /{lastPath}",
            )
            ref = getReferrer()
            (firstRef, lastRef) = splitUrl(ref)
            back = firstRef if lastRef in {"read", "update", "delete"} else f"/{ref}"
            return redirectStatus(back, True)

        Messages.warning(logmsg=f"Not found: /{path}")
        stop()

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
        # Messages = self.Messages
        Auth = self.Auth

        navigation = self.navigation(url)
        iconSite = self.putUpload("iconSite")
        (testLoginWidget, loginWidget) = Auth.wrapLogin()

        return template(
            "index",
            banner=Settings.banner,
            versionInfo=Settings.versionInfo,
            navigation=navigation,
            materialLeft=left or "",
            materialRight=right or "",
            testLoginWidget=testLoginWidget,
            loginWidget=loginWidget,
            iconSite=iconSite,
        )

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

        TABS = (
            ("home", "Home", True),
            ("about", "About", True),
            ("projects", "3D Projects", True),
            ("directory", "3D Directory", False),
            ("surpriseme", "Surprise Me", True),
            ("advancedsearch", "Advanced Search", False),
        )

        search = H.span(
            [
                H.input(
                    "search",
                    "",
                    name="search",
                    placeholder="search item",
                    cls="button disabled",
                ),
                H.input("submit", "Search", cls="button disabled"),
            ],
            cls="search-bar",
        )

        divContent = []

        for (tab, label, enabled) in TABS:
            active = "active" if url == tab else ""
            if enabled:
                elem = "a"
                cls = active
                href = [f"/{tab}"]
            else:
                elem = "span"
                cls = "disabled"
                href = []
            fullCls = f"button large {cls}"
            divContent.append(H.elem(elem, label, *href, cls=fullCls))

        divContent.append(search)

        return H.div(divContent, cls="tabs")

    def breadCrumb(self, projectId):
        """Makes a link to the landing page of a project.

        Parameters
        ----------
        projectId: ObjectId
            The project in question.
        """
        Content = self.Content
        projectUrl = f"/projects/{projectId}"
        text = Content.getValue("title", projectId=projectId, bare=True)
        return H.p(
            [
                "Project: ",
                H.a(
                    [text, H.gt()],
                    projectUrl,
                    cls="button",
                    title="back to the project page",
                ),
            ]
        )

    def putValues(self, fieldSpecs, projectId=None, editionId=None):
        """Puts several pieces of metadata on the web page.

        Parameters
        ----------
        fieldSpecs: string
            `,`-separated list of fieldSpecs
        projectId: ObjectId, optional None
            The project in question.
        editionId: ObjectId, optional None
            The edition in question.

        Returns
        -------
        string
            The join of the individual results of retrieving metadata value.
        """
        Content = self.Content

        return H.content(
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

    def putUpload(self, key, fileName=None, projectId=None, editionId=None, cls=None):
        """Puts a file upload control on a page.

        Parameters
        ----------
        key: string
            the key that identifies the kind of upload
        fileName: string, optional None
            If present, it indicates that the uploaded file will have this prescribed
            name.
            A file name for an upload object may also have been specified in
            the datamodel configuration.
        projectId: ObjectId, optional None
            The project in question.
        editionId: ObjectId, optional None
            The edition in question.
        cls: string, optional None
            An extra CSS class for the control

        Returns
        -------
        string
            A control that shows the file and possibly provides an upload/delete
            control for it.
        """
        Content = self.Content

        return (
            Content.getUpload(
                key, fileName=fileName, projectId=projectId, editionId=editionId
            )
            or ""
        )
