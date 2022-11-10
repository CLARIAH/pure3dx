from control.messages import Messages as MessagesCls
from control.config import Config as ConfigCls
from control.mongo import Mongo as MongoCls
from control.collect import Collect as CollectCls
from control.viewers import Viewers as ViewersCls
from control.content import Content as ContentCls
from control.users import Users as UsersCls
from control.pages import Pages as PagesCls
from control.editsessions import EditSessions as EditSessionsCls
from control.auth import Auth as AuthCls
from control.authoidc import AuthOidc as AuthOidcCls
from control.helpers.generic import AttrDict


def prepare(webdavMethods=None, trivial=False, flask=True):
    """Prepares the way for setting up the Flask webapp.

    Several classes are instantiated with a singleton object;
    each of these objects has a dedicated task in the app:

    * `control.config.Config.Settings`: all configuration aspects
    * `control.messages.Messages`: handle all messaging to user and sysadmin
    * `control.mongo.Mongo`: higher-level commands to the MongoDb
    * `control.viewers.Viewers`: support the third party 3D viewers
    * `control.users.Users`: manage the user data that the app needs
    * `control.content.Content`: retrieve all data that needs to be displayed
    * `control.auth.Auth`: compute the permission of the current user
      to access content
    * `control.pages.Pages`: high-level functions that
      distribute content over the page

    !!! note "Should be run once!"
        These objects are used in several web apps:

        * the main web app
        * a copy of the main app that is enriched with the webdav functionality

        However, these objects should be initialized once, before either app starts,
        and the same objects should be passed to both invocations of the
        factory functions that make them (`control.app.appFactory`).

        The invocations are done in `control.webdavapp.appFactory`.

    Parameters
    ----------
    trivial: boolean, optional False
        If True, skips the initialization of most objects.
        Useful if the pure3d app container should run without doing anything.
        This happens when we just want to start the container and run shell commands
        inside it, for example after a complicated refactoring when the flask app has
        too many bugs.

    flask: boolean, optional True
        If False, skips several configuration steps.
        Useful if you need configuration details of the app before
        flask is running. Cases are:

        * when setting up the webdav app (`control.webdavapp`) you need some
          configuration details, and this happens before the flask app is set up
        * when importing data into MongoDb, we need only non-flask parts of the app.
          This kind of import happens manually in a running container
          on the command line.

    Returns
    -------
    `control.helpers.generic.AttrDict`
        A dictionary keyed by the names of the singleton objects and valued
        by the singleton objects themselves.

    """
    if trivial:
        Settings = AttrDict(dict(secret_key=None))
        Messages = None
        Mongo = None
        Collect = None
        Viewers = None
        Users = None
        Content = None
        Auth = None
        EditSessions = None
        Pages = None
        AuthOidc = None
    else:
        Settings = ConfigCls(MessagesCls(None, flask=flask), flask=flask).Settings
        Settings.webdavMethods = webdavMethods
        Messages = MessagesCls(Settings, flask=flask)

        Mongo = MongoCls(Settings, Messages)
        Collect = CollectCls(Settings, Messages, Mongo)
        Collect.fetch()

        Viewers = ViewersCls(Settings)

        Users = UsersCls(Settings, Messages, Mongo)
        Content = ContentCls(Settings, Viewers, Messages, Mongo)
        Auth = AuthCls(Settings, Messages, Mongo, Users, Content)
        AuthOidc = AuthOidcCls()
        EditSessions = EditSessionsCls(Mongo)

        Content.addAuth(Auth)
        Viewers.addAuth(Auth)

        Pages = PagesCls(Settings, Viewers, Messages, Content, Auth, Users)

    return AttrDict(
        Settings=Settings,
        Messages=Messages,
        Mongo=Mongo,
        Collect=Collect,
        Viewers=Viewers,
        Users=Users,
        Content=Content,
        Auth=Auth,
        EditSessions=EditSessions,
        Pages=Pages,
        AuthOidc=AuthOidc,
    )
