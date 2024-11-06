from .flask import redirectStatus, renderTemplate, sendFile, appStop, getReferrer


class Pages:
    def __init__(self, Settings, Viewers, Messages, Mongo, Content, Backup, Auth):
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
        self.Content = Content
        self.Backup = Backup
        self.Auth = Auth

    def precheck(self, edition):
        """Check the articles of an edition prior to publishing.

        Parameters
        ----------
        edition: string
            the edition

        After the operation:

        Goes back to the referrer url.
        The check operation will have generated a table of contents for the
        articles and media files, and these will be shown on the edition page.

        Returns
        -------
        response
        """
        Content = self.Content

        good = Content.precheck(edition)
        ref = getReferrer().removeprefix("/")
        return redirectStatus(f"/{ref}", good)

    def publish(self, edition, force):
        """Publish an edition as static pages.

        Parameters
        ----------
        edition: string
            the edition
        force: boolean
            If True, ignore when some checks fail

        After the operation:

        *   *success*: goes back to referrer url, good status
        *   *failure*: goes back to referrer url, error status

        Returns
        -------
        response
        """
        Content = self.Content

        good = Content.publish(edition, force)
        ref = getReferrer().removeprefix("/")
        return redirectStatus(f"/{ref}", good)

    def republish(self, edition, force):
        """Re-publish an edition as static pages.

        Parameters
        ----------
        edition: string
            the edition
        force: boolean
            If True, ignore when some checks fail

        After the operation:

        *   *success*: goes back to referrer url, good status
        *   *failure*: goes back to referrer url, error status

        Returns
        -------
        response
        """
        Content = self.Content

        good = Content.republish(edition, force)
        ref = getReferrer().removeprefix("/")
        return redirectStatus(f"/{ref}", good)

    def unpublish(self, edition):
        """Unpublish an edition from the static pages.

        Parameters
        ----------
        edition: string
            the edition

        After the operation:

        *   *success*: goes back to referrer url, good status
        *   *failure*: goes back to referrer url, error status

        Returns
        -------
        response
        """
        Content = self.Content

        good = Content.unpublish(edition)
        ref = getReferrer().removeprefix("/")
        return redirectStatus(f"/{ref}", good)

    def generate(self):
        """Regenerate the static HTML pages for the whole published site.

        After the operation:

        *   *success*: goes back to referrer url, good status
        *   *failure*: goes back to referrer url, error status

        Returns
        -------
        response
        """
        Content = self.Content

        good = Content.generate()
        ref = getReferrer().removeprefix("/")
        return redirectStatus(f"/{ref}", good)

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
        Backup = self.Backup
        Auth = self.Auth

        if not Auth.mayBackup(project=project):
            Messages.warning(
                msg="Making a backup is not allowed",
                logmsg=("Making a backup is not allowed"),
            )
            ref = getReferrer().removeprefix("/")
            return redirectStatus(f"/{ref}", False)

        good = Backup.mkBackup(project=project)
        ref = getReferrer().removeprefix("/")
        return redirectStatus(f"/{ref}", good)

    def restoreBackup(self, backup, project=None):
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
        Backup = self.Backup
        Auth = self.Auth

        (projectId, project) = Mongo.get("project", project)

        if not Auth.mayBackup(project=project):
            Messages.warning(
                msg="Restoring from a backup is not allowed",
                logmsg=("Restoring from a backup is not allowed"),
            )
            ref = getReferrer().removeprefix("/")
            return redirectStatus(f"/{ref}", False)
        good = Backup.restoreBackup(backup, project=project)
        back = "/alogout" if project is None else f"/project/{projectId}"
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
        Backup = self.Backup
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
        good = Backup.delBackup(backup, project=project)
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

    def createUser(self, user):
        """Creates a new test user.

        After the operation:

        *   *success*: goes to admin url, good status
        *   *failure*: goes to admin url, error status

        Returns
        -------
        response
        """
        Messages = self.Messages
        Content = self.Content
        result = Content.createUser(user)

        good = result.get("status", False)
        if good:
            user = result["name"]
            Messages.info(logmsg=f"Created user {user}", msg=f"user {user} created")
        else:
            Messages.warning(
                logmsg=f"Could not create new user {user}",
                msg=f"failed to create new user {user}",
            )
            for kind, msg in result.get("messages", []):
                Messages.message(kind, msg, stop=False)

        newUrl = "/admin"
        return redirectStatus(newUrl, good)

    def deleteUser(self, user):
        """Deletes a test user.

        After the operation:

        *   *success*: goes to admin url, good status
        *   *failure*: goes to admin url, error status

        Returns
        -------
        response
        """
        Messages = self.Messages
        Content = self.Content
        result = Content.deleteUser(user)

        good = result.get("status", False)
        if good:
            Messages.info(logmsg=f"Deleted user {user}", msg=f"user {user} deleted")
        else:
            Messages.warning(
                logmsg=f"Could not delete user {user}",
                msg=f"failed to delete new user {user}",
            )
            for kind, msg in result.get("messages", []):
                Messages.message(kind, msg, stop=False)

        newUrl = "/admin"
        return redirectStatus(newUrl, good)

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
        Backup = self.Backup
        runProd = Settings.runProd

        (projectId, project) = Mongo.get("project", project)
        publishInfo = Content.getPublishInfo("project", project)
        actionHeading = H.h(3, "Actions")
        downloadButton = Content.getDownload("project", project)
        backups = "" if runProd else Backup.getBackups(project=project)
        editionHeading = H.h(3, "Editions")
        editions = Content.getEditions(project)
        left = (
            Content.getValues(
                "project",
                project,
                " + ".join(
                    """
                    title@3
                    creator@0
                    contributor@0
                    """.strip().split()
                ),
            )
            + publishInfo
            + actionHeading
            + downloadButton
            + backups
            + editionHeading
            + editions
        )
        right = Content.getValues(
            "project",
            project,
            " + ".join(
                """
                abstract@4
                description@4
                provenance@4
                instructionalMethod@4
                period@4
                place@4
                subject@4
                """.strip().split()
            ),
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
        Viewers = self.Viewers
        Content = self.Content
        Mongo = self.Mongo
        Auth = self.Auth

        tocFile = Settings.tocFile

        (editionId, edition) = Mongo.get("edition", edition)
        if edition is None:
            return redirectStatus("/project", True)

        projectId = edition.projectId
        (projectId, project) = Mongo.get("project", projectId)
        if project is None:
            return redirectStatus("/project", True)

        (viewer, sceneFile) = Viewers.getViewInfo(edition)

        breadCrumb = Content.breadCrumb(project)
        publishButton = Content.getPublishInfo("edition", edition)
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
            + Content.getValues(
                "edition", edition, "title@4 + creator@0 + contributor@0"
            )
            + publishButton
            + actionHeading
            + downloadButton
            + sceneHeading
            + sceneMaterial
        )
        right = Content.getValues(
            "edition",
            edition,
            "abstract@5 + description@5 + provenance@5 + instructionalMethod@5",
        ) + Content.getDataFile("edition", edition, tocFile, content=True, lenient=True)

        return self.page("projects", left=left, right=right)

    def fromPub(self, projectIdGiven, editionIdGiven):
        """Redirect to a project or edition or the home page.

        If the edition or project does not exist, show a friendly message.
        """
        Mongo = self.Mongo
        Messages = self.Messages
        Settings = self.Settings
        backPrefix = Settings.backPrefix
        authorLabel = Settings.authorLabel

        homeUrl = "/"

        if projectIdGiven is None and editionIdGiven is None:
            return redirectStatus(homeUrl, True)

        projectIdVerified = None
        editionIdVerified = None

        if editionIdGiven is not None:
            (editionIdVerified, editionVerified) = Mongo.get("edition", editionIdGiven)
            if editionVerified is not None:
                projectIdVerifiedFromEdition = editionVerified.projectId

        if projectIdGiven is not None:
            (projectIdVerified, projectVerified) = Mongo.get("project", projectIdGiven)

        if editionIdGiven is not None:
            if editionIdVerified is None:
                Messages.error(
                    msg=f"This edition no longer exists in {authorLabel}",
                    logmsg=f"{backPrefix}: Edition {editionIdGiven} no longer exists",
                    stop=False,
                )
                newUrl = (
                    homeUrl
                    if projectIdVerified is None
                    else f"/project/{projectIdVerified}"
                )

            else:
                if projectIdGiven and projectIdVerified != projectIdVerifiedFromEdition:
                    Messages.warning(
                        msg=(
                            "Found the edition but in a different project "
                            f"in {authorLabel}"
                        ),
                        logmsg=(
                            f"{backPrefix}: Edition {editionIdGiven} does not"
                            f"belong to project {projectIdGiven}"
                        ),
                    )
                else:
                    Messages.good(
                        msg=("Found the edition and project " f"in {authorLabel}"),
                    )

                newUrl = f"/edition/{editionIdVerified}"

        else:  # now projectIdGiven is not None
            if projectIdVerified is None:
                Messages.error(
                    msg=f"This project no longer exists in {authorLabel}",
                    logmsg=f"{backPrefix}: Project {projectIdGiven} no longer exists",
                    stop=False,
                )
                newUrl = homeUrl

            else:
                Messages.good(
                    msg=("Found the project " f"in {authorLabel}"),
                )
                newUrl = f"/project/{projectIdVerified}"

        return redirectStatus(newUrl, True)

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
        Mongo = self.Mongo
        Viewers = self.Viewers
        Auth = self.Auth

        (editionId, edition) = Mongo.get("edition", edition)
        if editionId is None:
            return renderTemplate("viewer", viewerCode="")

        (viewer, sceneFile) = Viewers.getViewInfo(edition)
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

        dataPath = Content.getDataFile(table, record, path)
        return sendFile(dataPath)

    def upload(self, record, key, path, targetFileName=None):
        """Upload a file.

        Parameters
        ----------
        record: string | ObjectId | AttrDict
            The context record of the upload
        key: string
            The key of the upload
        path: string
            The save location for the file
        targetFileName: string, optional None
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
            record, key, path, fileName, targetFileName=targetFileName
        )

    def deleteFile(self, record, key, path, targetFileName=None):
        """Delete a file.

        Parameters
        ----------
        record: string | ObjectId | AttrDict
            The context record of the upload.
        key: string
            The key of the upload.
        path: string
            The location of the file.
        targetFileName: string, optional None
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
            record, key, path, fileName, targetFileName=targetFileName
        )

    def authWebdav(self, edition, method, path, action):
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

        User = Auth.myDetails()
        user = User.user

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
        Backup = self.Backup
        Auth = self.Auth

        navigation = self.navigation(url)
        (specialLoginWidget, loginWidget) = Auth.wrapLogin()
        banner = Settings.banner
        if Backup is not None:
            banner = banner.replace("«backups»", Backup.getBackups(project=None))

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
        pubUrl = Settings.pubUrl
        published = Settings.published

        # 1st column: url
        # 2nd column: interface string
        # 3rd column: True: enabled, False: disabled
        # 4th column: implemented

        TABS = (
            ("home", "Home", True, True),
            ("about", "About", True, True),
            ("project", "3D Projects", True, True),
            (pubUrl, "Published Projects ⌲", True, True),
            ("admin", "My Work", True, True),
            ("directory", "3D Directory", False, False),
            ("surpriseme", "Surprise Me", True, False),
            ("advancedsearch", "Advanced Search", False, False),
        )

        search = H.span(
            [
                H.input(
                    "search",
                    "",
                    name="search",
                    placeholder="search item",
                    cls="button disabled",
                    disabled="",
                    style="display:none"
                ),
                H.input(
                    "submit",
                    "Search",
                    cls="button disabled",
                    type="button disabled",
                    disabled="",
                    style="display:none"
                ),
            ],
            cls="search-bar",
        )

        divContent = []

        for tab, label, enabled, implemented in TABS:
            if not implemented:
                continue

            active = "active" if url == tab else ""

            if enabled:
                elem = "a"
                cls = active
                href = [tab if "/" in tab else f"/{tab}"]
                target = dict(target=published) if "/" in tab else {}
            else:
                elem = "span"
                cls = "disabled"
                href = []
                target = {}

            fullCls = f"button large {cls}"
            divContent.append(H.elem(elem, label, *href, cls=fullCls, **target))

        divContent.append(search)

        return H.div(divContent, cls="tabs")
