from control.flask import appMake, appStop, requestMethod, appInitializing


def appFactory(objects):
    """Sets up the main flask app.

    The main task here is to configure routes,
    i.e. mappings from url-patterns to functions that create responses

    !!! note "WebDAV enabling"
        This flask app will later be combined with a webdav app,
        so that the combined app has the business logic of the main app
        but can also handle webdav requests.

        The routes below contain a few patterns that are used for
        authorising WebDAV calls: the onses starting with `/auth` and `/cannot`.
        See also `control.webdavapp`.

    Parameters
    ----------
    objects
        a slew of objects that set up the toolkit with which the app works:
        settings, messaging and logging, MongoDb connection, 3d viewer support,
        higher level objects that can fetch chunks of content and distribute
        it over the web page.

    Returns
    -------
    object
        A WebDAV-enabled flask app, which is a wsgi app.

    """

    Settings = objects.Settings
    Messages = objects.Messages
    Auth = objects.Auth
    AuthOidc = objects.AuthOidc
    Content = objects.Content
    Pages = objects.Pages
    webdavMethods = Settings.webdavMethods

    app = appMake(__name__, static_folder="../static")

    if Messages is None:
        return app

    app.secret_key = Settings.secret_key

    oidc = AuthOidc.prepare(app)
    Auth.addAuthenticator(oidc)

    @app.before_request
    def identify():
        """Get details of the current user.

        !!! caution "Not always called"
            The `/webdav/...` requests trigger a sub request to `/auth/webdav....`
            When flask arrives at that request, this code will not be re-executed,
            but we definitely must do that, because it identifies who the current
            user is.
        """
        Auth.initUser()
        if not appInitializing():
            Auth.identify()

    @app.route("/favicon.ico")
    def favicon():
        """Get the favicon."""
        return Pages.fileData("favicon.ico")

    @app.route("/login")
    def login():
        """Perform a user login."""
        return Auth.login()

    @app.route("/afterlogin/referrer/<path:referrer>")
    @app.route("/afterlogin/referrer/", defaults={"referrer": "/"})
    @oidc.require_login
    def afterlogin(referrer):
        """Go back to the page the user was on before logging in."""
        return Auth.afterLogin(referrer)

    @app.route("/logout")
    def logout():
        """Perform a user logout."""
        return Auth.logout()

    @app.route("/collect")
    def collect():
        """Reset the database to reflect the pristine example data.

        Works only in test mode, can be invoked by any user.
        """
        return Pages.collect()

    @app.route("/backup/<string:project>")
    @app.route("/backup/", defaults={"project": None})
    def mkBackup(project=None):
        """Makes a backup of files and database data.

        The backup is stored on the data share of the server,
        under a name that reflects the current date-time.

        It is possible to restrict the backup to a single project.

        Works only in pilot mode.

        *   power users can backup the whole shebang;
        *   project organisers can backup their own projects;
        *   power users can backup all projects.
        """
        return Pages.mkBackup(project=project)

    @app.route("/restore/<string:backup>/<string:project>")
    @app.route("/restore/<string:backup>/", defaults={"project": None})
    def restore(backup, project=None):
        """Restores a backup.

        The chosen backup should be stored on the data share of the server under a name
        that reflects the current date-time.

        !!! note "New backup"
            First a new backup of the current data will be made,
            so you can revert if you accidentally performed a restore.

        It is possible to restrict to backups of a single project.

        Works only in pilot mode.

        *   power users can restore the whole shebang;
        *   project organisers can restore their own projects;
        *   power users can restore all projects.
        """
        return Pages.restore(backup, project=project)

    @app.route("/delbackup/<string:backup>/<string:project>")
    @app.route("/delbackup/<string:backup>/", defaults={"project": None})
    def delBackup(backup, project=None):
        """Deletes a backup.

        The chosen backup should be stored on the data share of the server under a name
        that reflects the current date-time.

        It is possible to restrict to backups of a single project.

        Works only in pilot mode.

        *   power users can delete backups of the whole shebang;
        *   project organisers can delete backups of their own projects;
        *   power users can delete backups of all projects.
        """
        return Pages.delBackup(backup, project=project)

    @app.route("/")
    @app.route("/home")
    def home():
        """Present the "home" page."""
        return Pages.home()

    @app.route("/about")
    def about():
        """Present the "about" page."""
        return Pages.about()

    @app.route("/surpriseme")
    def surpriseme():
        """Present the "Surprise Me" page."""
        return Pages.surprise()

    @app.route("/project")
    def projects():
        """Present the "projects" page with the list of projects."""
        return Pages.projects()

    @app.route("/admin")
    def admin():
        """Present the "My Work" page.

        This page contains the project/editions that the current user is involved in.
        Administrators will also see the complete list of projects and the list of users.
        """
        return Pages.admin()

    @app.route("/site/<string:site>/project/create")
    def createProject(site):
        """Create a new project with the current user as organiser.

        Parameters
        ----------
        site: string
            The id of the unique site record, which acts as master record for
            all the projects.
        """
        return Pages.createProject(site)

    @app.route("/project/<string:project>")
    def project(project):
        """Presents the landing page of a project.

        Parameters
        ----------
        project: string
            The id of the project record.
        """
        return Pages.project(project)

    @app.route("/project/<string:project>/delete")
    def deleteProject(project):
        """Deletes a project.

        Parameters
        ----------
        project: string
            The id of the project record.
        """
        return Pages.deleteItem("project", project)

    @app.route("/project/<string:project>/edition/create")
    def createEdition(project):
        """Create a new edition with the current user as editor.

        Parameters
        ----------
        project: string
            The id of the master project record.
        """
        return Pages.createEdition(project)

    @app.route("/edition/<string:edition>", defaults=dict(version=None, action=None))
    @app.route("/edition/<string:edition>/<string:version>", defaults=dict(action=None))
    @app.route("/edition/<string:edition>/<string:version>/<string:action>")
    def edition(edition, version, action):
        """Presents the landing page of an edition.

        The edition is shown in the viewer associated with the edition.

        Parameters
        ----------
        edition: string
            The id of the edition record.
        version: string | void
            The viewer version to use.
        action: string, optional None
            The mode in which the viewer is to be used (`read` or `update`).
        """
        return Pages.edition(edition, version=version, action=action)

    @app.route("/edition/<string:edition>/delete")
    def deleteEdition(edition):
        """Deletes a edition.

        Parameters
        ----------
        edition: string
            The id of the edition record.
        """
        return Pages.deleteItem("edition", edition)

    @app.route(
        "/viewer/<string:version>/<string:action>/<string:edition>/<string:subMode>"
    )
    def viewerFrame(version=None, action=None, edition=None, subMode=None):
        """Present the scene of an edition in a 3D viewer.

        This is typically loaded in an iframe, but it can also
        be loaded in a new browser window.

        Parameters
        ----------
        edition: string
            The edition id to which the scene belongs.
        version: string | None
            The viewer version to use.
        action: string | None
            The mode in which the viewer is to be used (`read` or `update`).
        subMode: string | None
            The sub mode in which the viewer is to be used (`update` or `create`).
        """
        return Pages.viewerFrame(edition, version, action, subMode)

    @app.route("/data/viewers/<path:path>")
    def viewerResource(path):
        """Serves components requested by viewers.

        Parameters
        ----------
        path: string
            Path on the file system where the resource resides.
        """
        return Pages.viewerResource(path)

    @app.route(
        "/data/project/<string:project>/edition/<string:edition>/",
        defaults=dict(path=None),
    )
    @app.route("/data/project/<string:project>/edition/<string:edition>/<path:path>")
    @app.route(
        "/data/project/<string:project>/", defaults=dict(edition=None, path=None)
    )
    @app.route(
        "/data/project/<string:project>/<path:path>", defaults=dict(edition=None)
    )
    @app.route("/data/", defaults=dict(project=None, edition=None, path=None))
    @app.route("/data/<path:path>", defaults=dict(project=None, edition=None))
    def fileData(project=None, edition=None, path=None):
        """Serves files directly from the file repository.

        Parameters
        ----------
        path: string
            Path on the file system where the resource resides, relative to project/edition.
        project: string | ObjectId | AttrDict
            The id of a project under which the resource is to be found.
        edition: string | ObjectId | AttrDict
            The id of an edition under which the resource is to be found.
        """
        return Pages.fileData(path, project=project, edition=edition)

    @app.route("/download/<string:table>/<string:record>")
    def download(table, record):
        """Download a project or edition.

        The following will be downloaded:

        *   The content of the record in the database, as a yaml file;
        *   The corresponding content on the file system:
            scene, models, articles, media.

        All content will be zipped into a file named after the project or edition.
        The name is composed of the table name and the id of the record, and has
        extension zip.

        Parameters
        ----------
        table: string
            The table where the item to be downloaded sits.
        record: string
            The record of the item to be downloaded.
        """
        return Content.download(table, record)

    @app.route(
        "/upload/<string:record>/<string:key>/<string:givenFileName>/<path:path>",
        methods=["POST"],
    )
    def upload(record, key, givenFileName, path):
        """Upload a file.

        Where the file will be stored depends on the context, which is provided by
        a project/edition record.

        Parameters
        ----------
        record: string
            The context record of the upload
        key: string
            The key of the upload
        path: string
            The save location for the file
        givenFileName: string | void
            The name of the file as which the uploaded file will be saved.
        """
        if givenFileName == "-":
            givenFileName = None
        return Pages.upload(record, key, path, givenFileName=givenFileName)

    @app.route(
        "/deletefile/<string:record>/<string:key>/<string:givenFileName>/<path:path>"
    )
    def deleteFile(record, key, givenFileName, path):
        """Deletes a file.

        This is about files that have been uploaded by users.

        Where the file is to be found depends on the context, which is provided by
        a project/edition record.

        record: string
            The context record of the file.
        key: string
            The key of the upload.
        path: string
            The location of the file.
        givenFileName: string | void
            The name of the file.
        """
        if givenFileName == "-":
            givenFileName = None
        return Pages.deleteFile(record, key, path, givenFileName=givenFileName)

    @app.route("/link/user/<string:table>/<string:record>", methods=["POST"])
    def linkUser(table, record):
        """Links a user to a project/edition in a certain role..

        The user and role are passed as request data.

        Parameters
        ----------
        table: string
            The table of the record to link to.
        record: string
            The id of the record to link to.
        """
        return Content.linkUser(table, record)

    @app.route(
        "/save/role/<string:user>/",
        defaults=dict(table=None, record=None),
        methods=["POST"],
    )
    @app.route(
        "/save/role/<string:user>/<string:table>/<string:record>/",
        methods=["POST"],
    )
    def saveRole(user, table, record):
        """Saves the role of a user.

        Either a site-wide role or a role wrt. a project/edition.

        The role itself is passed as request data.

        Parameters
        ----------
        table: string
            The table of the record the user is linked to.
        record: string
            The id of the record to the user is linked to.
        """
        return Content.saveRole(user, table, record)

    @app.route("/save/<string:table>/<string:record>/<string:key>", methods=["POST"])
    def saveValue(table, record, key):
        """Saves metadata to the database.

        Parameters
        ----------
        table: string
            The table of the record that contains the metadata
        record: string
            The id of the record that contains the metadata.
        key: string
            The key of the metadata.
        """
        return Content.saveValue(table, record, key)

    @app.route(
        "/auth/webdav/project/<string:project>/edition/<string:edition>/",
        defaults=dict(path=None),
        methods=tuple(webdavMethods),
    )
    @app.route(
        "/auth/webdav/project/<string:project>/edition/<string:edition>/<path:path>",
        methods=tuple(webdavMethods),
    )
    def authWebdav(project, edition, path):
        """Authorises webdav requests.

        When 3D viewers make direct requests to the server through WebDAV,
        these requests are intercepted here and it is checked whether it is authorised.

        Such requests are always made in the context of an edition, and hence a project.

        !!! caution "Identify needs to be called"
            This function is typically called in a request generated by another request.
            That means that the `before_request` function has already run.
            But we do need it to run here as well.
            That's why you see an `Auth.identify()` in the code.

        Parameters
        ----------
        project: string
            The id of the project context.
        edition: string
            The id of the edition context.
        path: string
            The rest of the WebDAV request.

        Returns
        -------
        boolean
            N.B.: this controller does not lead to a view, but to the answer
            whether the call is authorised.

            See `control.webdavapp.dispatchWebdav`.
        """
        Auth.initUser()
        Auth.identify()
        method = requestMethod()
        action = webdavMethods[method]
        return Pages.authWebdav(edition, method, path, action)

    @app.route("/auth/webdav/<path:path>", methods=tuple(webdavMethods))
    def webdavinvalid(path):
        """Prevents unrecognized webdav requests.

        WebDAV requests that are not made in a proper project/edition context
        will not be honoured.

        Parameters
        ----------
        path: string
            The original WebDAV request.

        Returns
        -------
        boolean
            Always False!

            N.B.: this controller does not lead to a view, but to the answer
            whether the call is authorised.

            See `control.webdavapp.dispatchWebdav`.
        """
        Messages.warning(logmsg=f"Invalid webdav access: {path}")
        return False

    @app.route("/cannot/webdav/<path:path>")
    def nowebdav(path):
        """Prevents unauthorised WebDAV requests.

        WebDAV requests that have been rejected will lead to an error page.

        Parameters
        ----------
        path: string
            The original WebDAV request.
        """
        Messages.warning(logmsg=f"Unauthorized webdav access: {path}")
        appStop()

    @app.route("/<path:path>")
    def remaining(path, methods=("GET", "POST") + tuple(webdavMethods)):
        """Handles unmatched urls.

        Parameters
        ----------
        path: string
            The url of the request.
        """
        return Pages.remaining(path)

    return app
