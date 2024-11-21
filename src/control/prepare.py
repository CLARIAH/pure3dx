from pybars import Compiler

from .messages import Messages as MessagesCls
from .config import Config as ConfigCls
from .mongo import Mongo as MongoCls
from .viewers import Viewers as ViewersCls
from .wrap import Wrap as WrapCls
from .backup import Backup as BackupCls
from .content import Content as ContentCls
from .publish import Publish as PublishCls
from .tailwind import Tailwind as TailwindCls
from .pages import Pages as PagesCls
from .auth import Auth as AuthCls
from .generic import AttrDict
from .authoidc import AuthOidc as AuthOidcCls


def prepare(design=False, migrate=False, trivial=False):
    """Prepares the way for setting up the Flask webapp.

    Several classes are instantiated with a singleton object;
    each of these objects has a dedicated task in the app:

    * `control.config.Config.Settings`: all configuration aspects
    * `control.messages.Messages`: handle all messaging to user and sysadmin
    * `control.mongo.Mongo`: higher-level commands to the MongoDb
    * `control.viewers.Viewers`: support the third party 3D viewers
    * `control.wrap.Wrap`: several lengthy functions to wrap concepts into HTML
    * `control.backup.Backup`: several functions for user-triggered backup operations
    * `control.datamodel.Datamodel`: factory for handling fields, inherited by `Content`
    * `control.content.Content`: retrieve all data that needs to be displayed
    * `control.publish.Publish`: publish an edition as static pages
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
    migrate: boolean, optional False
        If True, overrides the `trivial` parameter.
        It will initialize those objects that are needed for
        the migration of data.
    design: boolean, optional False
        If True, overrides the `trivial` parameter.
        It will initialize those objects that are needed for
        static page generation in the `Published` directory,
        assuming that the project/edition files have already been
        exported.
    trivial: boolean, optional False
        If `design` is False and `trivial` is True, skips the initialization of
        most objects.
        Useful if the pure3d app container should run without doing anything.
        This happens when we just want to start the container and run shell commands
        inside it, for example after a complicated refactoring when the flask app has
        too many bugs.
        The only way to enable this is by setting `trivial = True` in the file
        `src/control/webdavapp.py`, in the function `appFactory()`, where you see
        the statement `trivial = False`.

    Returns
    -------
    AttrDict
        A dictionary keyed by the names of the singleton objects and valued
        by the singleton objects themselves.

    """
    if trivial:
        Settings = AttrDict(dict(secret_key=None))
        return AttrDict(Settings=Settings)

    settingsAtts = dict(migrate=migrate, design=design) if migrate or design else {}
    Settings = ConfigCls(MessagesCls(None), **settingsAtts).Settings
    Messages = MessagesCls(Settings)

    if migrate:
        return AttrDict(Settings=Settings, Messages=Messages)

    Viewers = ViewersCls(Settings, Messages)
    Mongo = MongoCls(Settings, Messages)
    Wrap = WrapCls(Settings, Messages, Viewers)
    Content = ContentCls(Settings, Messages, Viewers, Mongo, Wrap)
    Tailwind = TailwindCls(Settings)
    Handlebars = Compiler()

    if design:

        return AttrDict(
            Settings=Settings,
            Messages=Messages,
            Content=Content,
            Viewers=Viewers,
            Tailwind=Tailwind,
            Handlebars=Handlebars,
        )

    Backup = (
        None if Settings.runMode == "prod" else BackupCls(Settings, Messages, Mongo)
    )
    Publish = PublishCls(
        Settings, Messages, Viewers, Mongo, Content, Tailwind, Handlebars
    )
    Auth = AuthCls(Settings, Messages, Mongo, Content)
    AuthOidc = AuthOidcCls()

    if Backup is not None:
        Backup.addAuth(Auth)

    Wrap.addAuth(Auth)
    Content.addAuth(Auth)
    Wrap.addContent(Content)
    Viewers.addAuth(Auth)

    Pages = PagesCls(Settings, Viewers, Messages, Mongo, Content, Backup, Auth)
    Messages.setFlask()

    return AttrDict(
        Settings=Settings,
        Messages=Messages,
        Mongo=Mongo,
        Viewers=Viewers,
        Wrap=Wrap,
        Backup=Backup,
        Content=Content,
        Publish=Publish,
        Auth=Auth,
        Pages=Pages,
        AuthOidc=AuthOidc,
    )
