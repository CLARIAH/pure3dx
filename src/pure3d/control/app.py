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
    app.secret_key = Settings.secret_key

    oidc = AuthOidc.prepare(app)
    Auth.addAuthenticator(oidc)

    @app.before_request
    def identify():
        if not appInitializing():
            Auth.identify()

    @app.route("/favicon.ico")
    def favicon():
        return Pages.fileData("favicon.ico")

    @app.route("/login")
    def login():
        return Auth.login()

    @app.route("/afterlogin/referrer/<path:referrer>")
    @app.route("/afterlogin/referrer/", defaults={"referrer": "/"})
    @oidc.require_login
    def afterlogin(referrer):
        return Auth.afterLogin(referrer)

    @app.route("/logout")
    def logout():
        return Auth.logout()

    @app.route("/reset")
    def reset():
        return Pages.reset()

    @app.route("/collect")
    def collect():
        return Pages.collect()

    @app.route("/")
    @app.route("/home")
    def home():
        return Pages.home()

    @app.route("/about")
    def about():
        return Pages.about()

    @app.route("/surpriseme")
    def surpriseme():
        return Pages.surprise()

    @app.route("/project")
    def projects():
        return Pages.projects()

    @app.route("/mywork")
    def mywork():
        return Pages.mywork()

    @app.route("/project/create")
    def projectInsert():
        return Pages.projectInsert()

    @app.route("/project/<string:project>")
    def project(project):
        return Pages.project(project)

    @app.route("/project/<string:project>/edition/create")
    def editionInsert(project):
        return Pages.editionInsert(project)

    @app.route("/edition/<string:edition>", defaults=dict(version=None, action=None))
    @app.route("/edition/<string:edition>/<string:version>", defaults=dict(action=None))
    @app.route("/edition/<string:edition>/<string:version>/<string:action>")
    def edition(edition, version, action):
        return Pages.edition(edition, version=version, action=action)

    @app.route("/viewer/<string:version>/<string:action>/<string:edition>")
    def viewerFrame(version=None, action=None, edition=None):
        return Pages.viewerFrame(edition, version, action)

    @app.route("/data/viewers/<path:path>")
    def viewerResource(path):
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
        return Pages.fileData(path, project=project, edition=edition)

    @app.route(
        "/upload/<string:record>/<string:key>/<string:givenFileName>/<path:path>",
        methods=["POST"],
    )
    def upload(record, key, givenFileName, path):
        if givenFileName == "-":
            givenFileName = None
        return Pages.upload(record, key, path, givenFileName=givenFileName)

    @app.route(
        "/deletefile/<string:record>/<string:key>/<string:givenFileName>/<path:path>"
    )
    def deleteFile(record, key, givenFileName, path):
        if givenFileName == "-":
            givenFileName = None
        return Pages.deleteFile(record, key, path, givenFileName=givenFileName)

    @app.route("/save/<string:table>/<string:record>/<string:key>", methods=["POST"])
    def saveValue(table, record, key):
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
        action = webdavMethods[requestMethod()]
        return Pages.authWebdav(edition, path, action)

    @app.route("/auth/webdav/<path:path>", methods=tuple(webdavMethods))
    def webdavinvalid(path):
        Messages.warning(logmsg=f"Invalid webdav access: {path}")
        return False

    @app.route("/cannot/webdav/<path:path>")
    def nowebdav(path):
        Messages.warning(logmsg=f"Unauthorized webdav access: {path}")
        appStop()

    @app.route("/<path:path>")
    def remaining(path):
        return Pages.remaining(path)

    return app
