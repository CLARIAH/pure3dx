from control.flask import make, stop, method, initializing, send


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
    objects: `control.generic.AttrDict`
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
    Mongo = objects.Mongo
    Auth = objects.Auth
    AuthOidc = objects.AuthOidc
    Pages = objects.Pages
    Content = objects.Content
    webdavMethods = Settings.webdavMethods

    app = make(__name__, static_folder="../static")
    app.secret_key = Settings.secret_key

    oidc = AuthOidc.prepare(app)
    Auth.addAuthenticator(oidc)

    @app.before_request
    def identify():
        if not initializing():
            Auth.identify()

    @app.route("/favicon.ico")
    def favicon():
        favicon = Content.getData("favicon.ico")
        return send(favicon)

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

    @app.route("/projects")
    def projects():
        return Pages.projects()

    @app.route("/projects/create")
    def projectInsert():
        return Pages.projectInsert()

    @app.route("/projects/<string:projectId>")
    def project(projectId):
        return Pages.project(Mongo.cast(projectId))

    @app.route("/projects/<string:projectId>/editions/create")
    def editionInsert(projectId):
        return Pages.editionInsert(Mongo.cast(projectId))

    @app.route("/editions/<string:editionId>", defaults=dict(version=None, action=None))
    @app.route(
        "/editions/<string:editionId>/<string:version>", defaults=dict(action=None)
    )
    @app.route("/editions/<string:editionId>/<string:version>/<string:action>")
    def edition(editionId, version, action):
        return Pages.edition(Mongo.cast(editionId), version, action)

    @app.route(
        "/viewer/<string:version>/<string:action>/<string:editionId>"
    )
    def viewerFrame(version=None, action=None, editionId=None):
        return Pages.viewerFrame(Mongo.cast(editionId), version, action)

    @app.route("/data/viewers/<path:path>")
    def viewerResource(path):
        return Pages.viewerResource(path)

    @app.route(
        "/data/projects/<string:projectId>/editions/<string:editionId>/",
        defaults=dict(path=None),
    )
    @app.route(
        "/data/projects/<string:projectId>/editions/<string:editionId>/<path:path>",
    )
    @app.route(
        "/data/projects/<string:projectId>/",
        defaults=dict(editionId=None, path=None),
    )
    @app.route(
        "/data/projects/<string:projectId>/<path:path>",
        defaults=dict(editionId=None),
    )
    @app.route(
        "/data/",
        defaults=dict(projectId=None, editionId=None, path=None),
    )
    @app.route(
        "/data/<path:path>",
        defaults=dict(projectId=None, editionId=None),
    )
    def dataProjects(projectId=None, editionId=None, path=None):
        return Pages.dataProjects(
            path, projectId=Mongo.cast(projectId), editionId=Mongo.cast(editionId)
        )

    @app.route(
        "/upload/<string:table>/<string:recordId>/<string:key>/<path:path>",
        methods=["POST"],
    )
    def upload(table, recordId, key, path):
        return Pages.upload(table, Mongo.cast(recordId), key, path)

    @app.route(
        "/auth/webdav/projects/<string:projectId>/editions/<string:editionId>/",
        defaults=dict(path=None),
        methods=tuple(webdavMethods),
    )
    @app.route(
        "/auth/webdav/projects/<string:projectId>/editions/"
        "<string:editionId>/<path:path>",
        methods=tuple(webdavMethods),
    )
    def authWebdav(projectId, editionId, path):
        action = webdavMethods[method()]
        return Pages.authWebdav(
            Mongo.cast(projectId), Mongo.cast(editionId), path, action
        )

    @app.route("/auth/webdav/<path:path>", methods=tuple(webdavMethods))
    def webdavinvalid(path):
        Messages.warning(logmsg=f"Invalid webdav access: {path}")
        return False

    @app.route("/cannot/webdav/<path:path>")
    def nowebdav(path):
        Messages.warning(logmsg=f"Unauthorized webdav access: {path}")
        stop()

    @app.route("/<path:path>")
    def remaining(path):
        return Pages.remaining(path)

    return app
