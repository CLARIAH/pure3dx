from flask import Flask, redirect, abort, request


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
    AuthOidc = objects.AuthOidc
    Pages = objects.Pages
    webdavMethods = Settings.webdavMethods

    app = Flask(__name__, static_folder="../static")
    app.secret_key = Settings.secret_key

    oidcauth = AuthOidc.prepare(app)

    @app.route("/loginoidc")
    def loginoidc():
        if oidcauth.user_loggedin:
            return (f"Hello, {oidcauth.user_getfield('nickname')}\nwith email {oidcauth.user_getfield('email')}\nand sub {oidcauth.user_getfield('sub')}")
        else:
            return redirect("/private")

    @app.route("/private")
    @oidcauth.require_login
    def noaccessprivate():
        return redirect("/loginoidc")

    def redirectResult(url, good):
        code = 302 if good else 303
        return redirect(url, code=code)

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
        return Pages.surprise()

    @app.route("/projects")
    def projects():
        return Pages.projects()

    @app.route("/projects/<string:projectId>")
    def project(projectId):
        return Pages.project(projectId)

    @app.route("/editions/<string:editionId>")
    def edition(editionId):
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
        return Pages.scene(sceneId, viewer, version, action)

    @app.route(
        "/viewer/<string:viewer>/<string:version>/<string:action>/<string:sceneId>"
    )
    def viewerFrame(sceneId, viewer, version, action):
        return Pages.viewerFrame(sceneId, viewer, version, action)

    @app.route("/data/viewers/<path:path>")
    def viewerResource(path):
        return Pages.viewerResource(path)

    @app.route(
        "/data/projects/<string:projectName>/",
        defaults=dict(editionName="", path=""),
    )
    @app.route(
        "/data/projects/<string:projectName>/<path:path>",
        defaults=dict(editionName=""),
    )
    @app.route(
        "/data/projects/<string:projectName>/editions/<string:editionName>/",
        defaults=dict(path=""),
    )
    @app.route(
        "/data/projects/<string:projectName>/editions/<string:editionName>/<path:path>",
    )
    def dataProjects(projectName, editionName, path):
        return Pages.dataProjects(projectName, editionName, path)

    @app.route(
        "/auth/webdav/projects/<string:projectName>/editions/<string:editionName>/",
        defaults=dict(path=""),
        methods=tuple(webdavMethods),
    )
    @app.route(
        "/auth/webdav/projects/<string:projectName>/editions/<string:editionName>/"
        "<path:path>",
        methods=tuple(webdavMethods),
    )
    def authWebdav(projectName, editionName, path):
        action = webdavMethods[request.method]
        return Pages.authWebdav(projectName, editionName, path, action)

    @app.route("/auth/webdav/<path:path>", methods=tuple(webdavMethods))
    def webdavinvalid(path):
        Messages.info(logmsg=f"Invalid webdav access {path=}")
        return False

    @app.route("/no/webdav/<path:path>")
    def nowebdav(path):
        Messages.info(logmsg=f"Unauthorized webdav access {path=}")
        abort(404)

    return app
