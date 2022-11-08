from control.flask import makeFlask, redirectResult, stop, method


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
    Auth = objects.Auth
    Pages = objects.Pages
    webdavMethods = Settings.webdavMethods

    app = makeFlask(__name__, static_folder="../static")
    app.secret_key = Settings.secret_key

    # app url routes start here

    @app.route("/login")
    def login():
        if Auth.authenticate(login=True):
            good = True
        else:
            good = False
        return redirectResult("/", good)

    @app.route("/logout")
    def logout():
        Auth.deauthenticate()
        return redirectResult("/", True)

    @app.route("/")
    @app.route("/home")
    def home():
        return Pages.home()

    @app.route("/about")
    def about():
        return Pages.about()

    @app.route("/surpriseme")
    def surpriseme():
        Auth.authenticate()
        return Pages.surprise()

    @app.route("/projects")
    def projects():
        Auth.authenticate()
        return Pages.projects()

    @app.route("/projects/insert")
    def projectInsert():
        Auth.authenticate()
        return Pages.projectInsert()

    @app.route("/projects/<string:projectId>")
    def project(projectId):
        Auth.authenticate()
        return Pages.project(projectId)

    @app.route("/editions/<string:editionId>")
    def edition(editionId):
        Auth.authenticate()
        return Pages.edition(editionId)

    @app.route(
        "/scenes/<string:sceneId>",
        defaults=dict(viewer="", version="", action=""),
    )
    @app.route(
        "/scenes/<string:sceneId>/<string:viewer>",
        defaults=dict(version="", action=""),
    )
    @app.route(
        "/scenes/<string:sceneId>/<string:viewer>/<string:version>",
        defaults=dict(action=""),
    )
    @app.route(
        "/scenes/<string:sceneId>/<string:viewer>/<string:version>/<string:action>",
    )
    def scene(sceneId, viewer, version, action):
        Auth.authenticate()
        return Pages.scene(sceneId, viewer, version, action)

    @app.route(
        "/viewer/<string:viewer>/<string:version>/<string:action>/<string:sceneId>"
    )
    def viewerFrame(sceneId, viewer, version, action):
        Auth.authenticate()
        return Pages.viewerFrame(sceneId, viewer, version, action)

    @app.route("/data/viewers/<path:path>")
    def viewerResource(path):
        Auth.authenticate()
        return Pages.viewerResource(path)

    @app.route(
        "/data/projects/<string:projectId>/",
        defaults=dict(editionId="", path=""),
    )
    @app.route(
        "/data/projects/<string:projectId>/<path:path>",
        defaults=dict(editionId=""),
    )
    @app.route(
        "/data/projects/<string:projectId>/editions/<string:editionId>/",
        defaults=dict(path=""),
    )
    @app.route(
        "/data/projects/<string:projectId>/editions/<string:editionId>/<path:path>",
    )
    def dataProjects(projectId, editionId, path):
        Auth.authenticate()
        return Pages.dataProjects(projectId, editionId, path)

    @app.route(
        "/auth/webdav/projects/<string:projectId>/editions/<string:editionId>/",
        defaults=dict(path=""),
        methods=tuple(webdavMethods),
    )
    @app.route(
        "/auth/webdav/projects/<string:projectId>/editions/<string:editionId>/"
        "<path:path>",
        methods=tuple(webdavMethods),
    )
    def authWebdav(projectId, editionId, path):
        Auth.authenticate()
        action = webdavMethods[method()]
        return Pages.authWebdav(projectId, editionId, path, action)

    @app.route("/auth/webdav/<path:path>", methods=tuple(webdavMethods))
    def webdavinvalid(path):
        Messages.info(logmsg=f"Invalid webdav access {path=}")
        return False

    @app.route("/no/webdav/<path:path>")
    def nowebdav(path):
        Messages.info(logmsg=f"Unauthorized webdav access {path=}")
        stop()

    return app
