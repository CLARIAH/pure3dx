from control.flask import redirectStatus, renderTemplate, sendFile, appStop, getReferrer


class Pages:
    def __init__(self, Settings, Viewers, Messages, Mongo, Collect, Content, Auth):
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
        Settings: AttrDict
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
        self.Mongo = Mongo
        self.Collect = Collect
        self.Content = Content
        self.Auth = Auth

    def collect(self):
        """Data reset: collect the example data again.

        After the operation:

        *   *success*: goes to home page, good status
        *   *failure*: goes back to referrer url, error status

        Returns
        -------
        response
        """
        Settings = self.Settings
        Collect = self.Collect
        Messages = self.Messages
        runMode = Settings.runMode

        if runMode != "test":
            Messages.warning(
                msg="Reset data is not allowed in this mode",
                logmsg=f"Reset data is not allowed in mode {runMode}",
            )
            ref = getReferrer().removeprefix("/")
            return redirectStatus(f"/{ref}", False)

        Collect.fetch()
        Messages.info(msg="data reset done!")
        return redirectStatus("/home", True)

    def mkBackup(self, project=None):
        """Backup: Save file and database data in a backup directory.

        Parameters
        ----------
        project: string, optional None
            If given, only backs up the given project.

        After the operation:

        *   *success*: goes back to referrer url, good status
        *   *failure*: goes back to referrer url, error status

        Returns
        -------
        response
        """
        Messages = self.Messages
        Content = self.Content
        Auth = self.Auth

        if not Auth.mayBackup(project=project):
            Messages.warning(
                msg="Making a backup is not allowed",
                logmsg=("Making a backup is not allowed"),
            )
            ref = getReferrer().removeprefix("/")
            return redirectStatus(f"/{ref}", False)

        good = Content.mkBackup(project=project)
        ref = getReferrer().removeprefix("/")
        return redirectStatus(f"/{ref}", good)

    def restore(self, backup, project=None):
        """Restore from a backup. Make a new backup first.

        After the operation:

        *   *success*:
            *   site-wide restore: goes to logout url, good status
            *   project-specific restore: goes to project url, good status
        *   *failure*: goes back to referrer url, error status

        Parameters
        ----------
        backup: string
            The name of the backup as stored in the backups directory on the server.
        project: string, optional None
            If given, restores the given project.

        Returns
        -------
        response
        """
        Messages = self.Messages
        Mongo = self.Mongo
        Content = self.Content
        Auth = self.Auth

        (projectId, project) = Mongo.get("project", project)

        if not Auth.mayBackup(project=project):
            Messages.warning(
                msg="Restoring from a backup is not allowed",
                logmsg=("Restoring from a backup is not allowed"),
            )
            ref = getReferrer().removeprefix("/")
            return redirectStatus(f"/{ref}", False)
        good = Content.restore(backup, project=project)
        back = "/logout" if project is None else f"/project/{projectId}"
        return redirectStatus(back, good)

    def delBackup(self, backup, project=None):
        """Deletes a backup.

        After the operation:

        *   *success*: goes back to referrer url, good status
        *   *failure*: goes back to referrer url, error status

        Parameters
        ----------
        backup: string
            The name of the backup as stored in the backups directory on the server.
        project: string, optional None
            If given, deletes a backup of the given project.

        Returns
        -------
        response
        """
        Messages = self.Messages
        Mongo = self.Mongo
        Content = self.Content
        Auth = self.Auth

        (projectId, project) = Mongo.get("project", project)

        ref = getReferrer().removeprefix("/")
        back = f"/{ref}"

        if not Auth.mayBackup(project=project):
            Messages.warning(
                msg="Deleting a backup is not allowed",
                logmsg=("Deleting a backup is not allowed"),
            )
            return redirectStatus(back, False)
        good = Content.delBackup(backup, project=project)
        return redirectStatus(back, good)

    def home(self):
        """The site-wide home page.

        Returns
        -------
        response
        """
        Content = self.Content
        (table, recordId, record) = Content.relevant()
        if recordId is None:
            left = None
        else:
            left = Content.getValues(table, record, "siteTitle@1 + abstract@2")
        return self.page("home", left=left)

    def about(self):
        """The site-wide about page.

        Returns
        -------
        response
        """
        Content = self.Content
        (table, recordId, record) = Content.relevant()
        if recordId is None:
            (left, right) = (None, None)
        else:
            left = Content.getValues(table, record, "siteTitle@1 + abstract@2")
            right = Content.getValues(table, record, "description@2 + provenance@2")
        return self.page("about", left=left, right=right)

    def surprise(self):
        """The "surprise me!" page.

        Returns
        -------
        response
        """
        Content = self.Content
        (table, recordId, record) = Content.relevant()
        if recordId is None:
            (left, right) = (None, None)
        else:
            surpriseMe = Content.getSurprise()
            left = Content.getValues(table, record, "siteTitle@1")
            right = surpriseMe
        return self.page("surpriseme", left=left, right=right)

    def projects(self):
        """The page with the list of projects.

        Returns
        -------
        response
        """
        Content = self.Content
        (table, recordId, record) = Content.relevant()
        if recordId is None:
            left = None
        else:
            projects = Content.getProjects()
            left = Content.getValues(table, record, "siteTitle@2") + projects
        return self.page("projects", left=left)

    def admin(self):
        """The page with the list of projects, editions, and users.

        Returns
        -------
        response
        """
        Content = self.Content
        (table, recordId, record) = Content.relevant()
        if recordId is None:
            left = None
        else:
            items = Content.getAdmin()
            left = Content.getValues(table, record, "siteTitle@2") + items
        return self.page("admin", left=left)

    def createProject(self, site):
        """Creates a project and shows the new project.

        The current user is linked to this project as organiser.

        After the operation:

        *   *success*: goes to new project url, good status
        *   *failure*: goes to all projects url, error status

        Returns
        -------
        response
        Returns
        -------
        response
        """
        Messages = self.Messages
        Content = self.Content
        projectId = Content.createProject(site)

        if projectId is None:
            Messages.warning(
                logmsg="Could not create new project",
                msg="failed to create new project",
            )
            newUrl = "/project"
        else:
            Messages.info(
                logmsg=f"Created project {projectId}", msg="new project created"
            )
            newUrl = f"/project/{projectId}"

        return redirectStatus(newUrl, projectId is not None)

    def project(self, project):
        """The landing page of a project.

        Parameters
        ----------
        project: string | ObjectId | AttrDict
            The project in question.

        Returns
        -------
        response
        """
        Settings = self.Settings
        H = Settings.H
        Mongo = self.Mongo
        Content = self.Content
        (projectId, project) = Mongo.get("project", project)
        actionHeading = H.h(3, "Actions")
        downloadButton = Content.getDownload("project", project)
        backups = Content.getBackups(project=project)
        editionHeading = H.h(3, "Editions")
        editions = Content.getEditions(project)
        left = (
            Content.getValues("project", project, "title@3 + creator@0")
            + actionHeading
            + downloadButton
            + backups
            + editionHeading
            + editions
        )
        right = Content.getValues(
            "project",
            project,
            "abstract@4 + description@4 + provenance@4 + instructionalMethod@4",
        )
        return self.page("projects", left=left, right=right)

    def createEdition(self, project):
        """Inserts an edition into a project and shows the new edition.

        The current user is linked to this edition as editor.

        After the operation:

        *   *success*: goes to new edition url, good status
        *   *failure*: goes to project url, error status

        Returns
        -------
        response
        Parameters
        ----------
        project: string | ObjectId | AttrDict
            The project to which the edition belongs.

        Returns
        -------
        response
        """
        Messages = self.Messages
        Mongo = self.Mongo
        Content = self.Content

        (projectId, project) = Mongo.get("project", project)
        if projectId is None:
            return redirectStatus("/home", False)

        editionId = Content.createEdition(project)

        if editionId is None:
            Messages.warning(
                logmsg="Could not create new edition",
                msg="failed to create new edition",
            )
            newUrl = f"/project/{projectId}"
        else:
            Messages.info(
                logmsg=f"Created edition {editionId}", msg="new edition created"
            )
            newUrl = f"/edition/{editionId}"
        return redirectStatus(newUrl, editionId is not None)

    def edition(self, edition, version=None, action=None):
        """The landing page of an edition, possibly with a scene marked as active.

        An edition knows the scene it should display and the viewer that was
        used to create the scene.

        If action is not None, its value determines which viewer will be loaded
        in the 3D viewer.
        It is dependent on the parameters and/or defaults
        in which viewer/version/mode.

        If version is not None, this will override the default version.

        Parameters
        ----------
        edition: string | ObjectId | AttrDict
            The editionin quesion.
            From the edition record we can find the project too.
        version: string, optional None
            The viewer version to use.
        action: string, optional None
            The mode in which the viewer is to be used (`read` or `update`).

        Returns
        -------
        response
        """
        Settings = self.Settings
        H = Settings.H
        Content = self.Content
        Mongo = self.Mongo
        Auth = self.Auth

        (editionId, edition) = Mongo.get("edition", edition)
        if edition is None:
            return redirectStatus("/project", True)

        projectId = edition.projectId
        (projectId, project) = Mongo.get("project", projectId)
        if project is None:
            return redirectStatus("/project", True)

        (viewer, sceneFile) = Content.getViewInfo(edition)

        breadCrumb = Content.breadCrumb(project)
        actionHeading = H.h(3, "Actions")
        downloadButton = Content.getDownload("edition", edition)

        if action is None:
            action = "read"
        action = Auth.makeSafe("edition", edition, action)
        sceneHeading = H.h(3, "Scene")
        sceneMaterial = (
            ""
            if False and action is None
            else Content.getScene(projectId, edition, version=version, action=action)
        )
        left = (
            breadCrumb
            + Content.getValues("edition", edition, "title@4")
            + actionHeading
            + downloadButton
            + sceneHeading
            + sceneMaterial
        )
        right = Content.getValues(
            "edition",
            edition,
            "abstract@5 + description@5 + provenance@5 + instructionalMethod@5",
        )
        return self.page("projects", left=left, right=right)

    def deleteItem(self, table, record):
        """Deletes an item, project or edition.

        After the operation:

        *   *success*: goes to all-projects url or master project url, good status
        *   *failure*: goes to back referrer url, error status

        Parameters
        ----------
        table: string
            The kind of item: `project` or `edition`.
        record: string | ObjectId | AttrDict
            The item in question.

        Returns
        -------
        response
        """
        Messages = self.Messages
        Mongo = self.Mongo
        Content = self.Content

        ref = getReferrer().removeprefix("/")
        back = f"/{ref}"

        (recordId, record) = Mongo.get(table, record)
        if recordId is None:
            return redirectStatus(back, False)

        result = Content.deleteItem(table, record)

        if result:
            Messages.info(logmsg=f"Deleted {table} {recordId}", msg=f"{table} deleted")
            back = "/project"
            if table == "edition":
                projectId = record.projectId
                back += f"/{projectId}"
        else:
            Messages.warning(
                logmsg=f"Could not delete {table} {recordId}",
                msg=f"failed to delete {table}",
            )
        return redirectStatus(back, True)

    def viewerFrame(self, edition, version, action, subMode):
        """The page loaded in an iframe where a 3D viewer operates.

        Parameters
        ----------
        edition: string | ObjectId | AttrDict
            The edition that is shown.
        version: string | None
            The version to use.
        action: string | None
            The mode in which the viewer is to be used (`read` or `update`).
        subMode: string | None
            The sub mode in which the viewer is to be used (`update` or `create`).

        Returns
        -------
        response
        """
        Content = self.Content
        Mongo = self.Mongo
        Viewers = self.Viewers
        Auth = self.Auth

        (editionId, edition) = Mongo.get("edition", edition)
        if editionId is None:
            return renderTemplate("viewer", viewerCode="")

        (viewer, sceneFile) = Content.getViewInfo(edition)
        projectId = edition.projectId

        urlBase = f"project/{projectId}/edition/{editionId}/"

        action = Auth.makeSafe("edition", edition, action)

        viewerCode = (
            ""
            if action is None or sceneFile is None
            else Viewers.genHtml(urlBase, sceneFile, viewer, version, action, subMode)
        )
        return renderTemplate("viewer", viewerCode=viewerCode)

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
            If the file does not exist, a 404 is returned.
        """
        Content = self.Content

        dataPath = Content.getViewerFile(path)
        return sendFile(dataPath)

    def fileData(self, path, project=None, edition=None):
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
        project: string | ObjectId | AttrDict
            The id of a project under which the resource is to be found.
            If None, it is site-wide material.
        edition: string | ObjectId | AttrDict
            If not None, the name of an edition under which the resource
            is to be found.

        Returns
        -------
        response
            The response consists of the contents of the
            file plus headers derived from the path.
            If the file does not exist, a 404 is returned.
        """
        Content = self.Content
        (table, recordId, record) = Content.relevant(project=project, edition=edition)
        if recordId is None:
            return ""

        dataPath = Content.getData(table, record, path)
        return sendFile(dataPath)

    def upload(self, record, key, path, givenFileName=None):
        """Upload a file.

        Parameters
        ----------
        record: string | ObjectId | AttrDict
            The context record of the upload
        key: string
            The key of the upload
        path: string
            The save location for the file
        givenFileName: string, optional None
            The name of the file as which the uploaded file will be saved;
            if is None, the file will be saved with the name from the request.

        Returns
        -------
        response
            With json data containing a status and a content member.
            The content is new content to display the upload widget with.
        """
        Content = self.Content

        parts = path.rstrip("/").rsplit("/", 1)
        fileName = parts[-1]
        path = parts[0] if len(parts) == 2 else ""

        return Content.saveFile(
            record, key, path, fileName, givenFileName=givenFileName
        )

    def deleteFile(self, record, key, path, givenFileName=None):
        """Delete a file.

        Parameters
        ----------
        record: string | ObjectId | AttrDict
            The context record of the upload.
        key: string
            The key of the upload.
        path: string
            The location of the file.
        givenFileName: string, optional None
            The name of the file.

        Returns
        -------
        response
            With json data containing a status, msg, and content members.
            The content is new content to display the upload widget with.
        """
        Content = self.Content

        parts = path.rstrip("/").rsplit("/", 1)
        fileName = parts[-1]
        path = parts[0] if len(parts) == 2 else ""

        return Content.deleteFile(
            record, key, path, fileName, givenFileName=givenFileName
        )

    def authWebdav(self, edition, path, action):
        """Authorises a webdav request.

        When a viewer makes a WebDAV request to the server,
        that request is first checked here for authorisation.

        See `control.webdavapp.dispatchWebdav()`.

        Parameters
        ----------
        edition: string | ObjectId | AttrDict
            The edition in question.
        path: string
            The path relative to the directory of the edition.
        action: string
            The operation that the WebDAV request wants to do on the data
            (`read` or `update`).

        Returns
        -------
        boolean
            Whether the action is permitted on ths data by the current user.
        """
        Messages = self.Messages
        Mongo = self.Mongo
        Auth = self.Auth

        (editionId, edition) = Mongo.get("edition", edition)
        if editionId is None:
            return False

        permitted = Auth.authorise("edition", record=edition, action=action)

        if not permitted:
            User = Auth.myDetails()
            user = User.user
            name = User.nickname

            Messages.info(
                logmsg=f"WEBDav unauthorised by user {name} ({user})"
                f" on edition {editionId} path {path}"
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
            """Auxiliary inner function."""
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
        appStop()

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
        Content = self.Content
        Auth = self.Auth

        navigation = self.navigation(url)
        (specialLoginWidget, loginWidget) = Auth.wrapLogin()
        banner = Settings.banner.replace("«backups»", Content.getBackups(project=None))

        (table, recordId, record) = Content.relevant()
        if recordId is None:
            return renderTemplate(
                "index",
                banner=banner,
                versionInfo=Settings.versionInfo,
                navigation=navigation,
                materialLeft=left or "",
                materialRight=right or "",
                specialLoginWidget=specialLoginWidget,
                loginWidget=loginWidget,
                iconSite="",
            )

        iconSite = Content.getUpload(record, "iconSite")

        return renderTemplate(
            "index",
            banner=banner,
            versionInfo=Settings.versionInfo,
            navigation=navigation,
            materialLeft=left or "",
            materialRight=right or "",
            specialLoginWidget=specialLoginWidget,
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
        Settings = self.Settings
        H = Settings.H

        # 1st column: url
        # 2nd column: interface string
        # 3rd column: True: enabled, False: disabled
        # 4th column: authorised

        TABS = (
            ("home", "Home", True, True),
            ("about", "About", True, True),
            ("project", "3D Projects", True, True),
            ("admin", "My Work", True, True),
            ("directory", "3D Directory", False, True),
            ("surpriseme", "Surprise Me", True, True),
            ("advancedsearch", "Advanced Search", False, True),
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

        for (tab, label, enabled, authorised) in TABS:
            if not authorised:
                continue
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
