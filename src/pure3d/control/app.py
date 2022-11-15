from control.flask import make, redirectStatus, stop, method


def appFactory(objects):
    """Sets up the main flask app.

    The main task here is to configure routes,
    i.e. mappings from url-patterns to functions that create responses

    !!! note "WebDAV enabling"
        This flask app will later be combined with a webdav app,
        so that the combined app has the business logic of the main app
        but can also handle webdav requests.

        The routes below contain a few patterns that are used for
        authorising WebDAV calls: the onses starting with `/auth` and `/no`.
        See also `control.webdavapp`.

    Parameters
    ----------
    objects: `control.helpers.generic.AttrDict`
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
    Pages = objects.Pages
    webdavMethods = Settings.webdavMethods

    app = make(__name__, static_folder="../static")
    app.secret_key = Settings.secret_key

    Auth.identify()

    # app url routes start here

    @app.route("/login")
    def login():
        good = Auth.login()
        return redirectStatus("/", good)

    @app.route("/logout")
    def logout():
        Auth.logout()
        return redirectStatus("/", True)

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

    @app.route("/projects/insert")
    def projectInsert():
        return Pages.projectInsert()

    @app.route("/projects/<string:projectId>")
    def project(projectId):
        return Pages.project(Mongo.cast(projectId))

    @app.route("/editions/<string:editionId>")
    def edition(editionId):
        return Pages.edition(Mongo.cast(editionId))

    @app.route(
        "/scenes/<string:sceneId>",
        defaults=dict(viewer=None, version=None, action=None),
    )
    @app.route(
        "/scenes/<string:sceneId>/<string:viewer>",
        defaults=dict(version=None, action=None),
    )
    @app.route(
        "/scenes/<string:sceneId>/<string:viewer>/<string:version>",
        defaults=dict(action=None),
    )
    @app.route(
        "/scenes/<string:sceneId>/<string:viewer>/<string:version>/<string:action>",
    )
    def scene(sceneId, viewer, version, action):
        return Pages.scene(Mongo.cast(sceneId), viewer, version, action)

    @app.route(
        "/viewer/<string:viewer>/<string:version>/<string:action>/<string:sceneId>"
    )
    def viewerFrame(sceneId, viewer, version, action):
        return Pages.viewerFrame(Mongo.cast(sceneId), viewer, version, action)

    @app.route("/data/viewers/<path:path>")
    def viewerResource(path):
        return Pages.viewerResource(path)

    @app.route(
        "/data/projects/<string:projectId>/",
        defaults=dict(editionId=None, path=None),
    )
    @app.route(
        "/data/projects/<string:projectId>/editions/<string:editionId>/",
        defaults=dict(path=None),
    )
    @app.route(
        "/data/projects/<string:projectId>/editions/<string:editionId>/<path:path>",
    )
    @app.route(
        "/data/projects/<string:projectId>/<path:path>",
        defaults=dict(editionId=None),
    )
    def dataProjects(projectId, editionId, path):
        return Pages.dataProjects(
            path, Mongo.cast(projectId), editionId=Mongo.cast(editionId)
        )

    @app.route(
        "/auth/webdav/projects/<string:projectId>/editions/<string:editionId>/",
        defaults=dict(path=None),
        methods=tuple(webdavMethods),
    )
    @app.route(
        "/auth/webdav/projects/<string:projectId>/editions/<string:editionId>/"
        "<path:path>",
        methods=tuple(webdavMethods),
    )
    def authWebdav(projectId, editionId, path):
        action = webdavMethods[method()]
        return Pages.authWebdav(
            Mongo.cast(projectId), Mongo.cast(editionId), path, action
        )

    @app.route("/auth/webdav/<path:path>", methods=tuple(webdavMethods))
    def webdavinvalid(path):
        Messages.info(logmsg=f"Invalid webdav access: {path}")
        return False

    @app.route("/no/webdav/<path:path>")
    def nowebdav(path):
        Messages.info(logmsg=f"Unauthorized webdav access: {path}")
        stop()

    return app
