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
    AuthOidc = objects.AuthOidc
    SendMail = objects.SendMail
    Pages = objects.Pages
    Content = objects.Content
    webdavMethods = Settings.webdavMethods

    app = make(__name__, static_folder="../static")
    app.secret_key = Settings.secret_key

    oidc = AuthOidc.prepare(app)
    Auth.addAuthenticator(oidc)

    # getting mail client
    send_mail = SendMail.prepare(app)

    # test sending
    send_mail.send_test_mail("qiqing.ding@di.huc.knaw.nl")
    ## how to send ##
    # 1 sending a raw message which consists of 3 str args
    send_mail.send_raw(title="test title1", message="test message 1", recipient="test1@test.com")

    # 2 sending a EmailMessage
    from control.sendmail import EmailMessage
    email2 = EmailMessage(title="test title 2", message="test message 2", recipient="qiqing.ding@di.huc.knaw.nl")
    send_mail.send(email2)

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
        objects.Collect.fetch()
        return Pages.home()

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

    @app.route("/projects/<string:projectId>/editions/<string:editionId>/scenes/create")
    def sceneInsert(projectId, editionId):
        return Pages.sceneInsert(Mongo.cast(projectId), Mongo.cast(editionId))

    @app.route(
        "/viewer/<string:viewer>/<string:version>/<string:action>/<string:sceneId>"
    )
    def viewerFrame(sceneId, viewer, version, action):
        return Pages.viewerFrame(Mongo.cast(sceneId), viewer, version, action)

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
    def dataProjects(projectId, editionId, path):
        return Pages.dataProjects(
            path, projectId=Mongo.cast(projectId), editionId=Mongo.cast(editionId)
        )

    @app.route(
        "/upload/<string:table>/<string:recordId>/<string:field>/<path:path>",
        methods=["POST"],
    )
    def upload(table, recordId, field, path):
        return Pages.upload(table, Mongo.cast(recordId), field, path)

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
