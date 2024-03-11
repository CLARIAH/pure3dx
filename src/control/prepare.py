from pybars import Compiler

from control.messages import Messages as MessagesCls
from control.config import Config as ConfigCls
from control.mongo import Mongo as MongoCls
from control.viewers import Viewers as ViewersCls
from control.wrap import Wrap as WrapCls
from control.content import Content as ContentCls
from control.publish import Publish as PublishCls
from control.tailwind import Tailwind as TailwindCls
from control.pages import Pages as PagesCls
from control.auth import Auth as AuthCls
from control.generic import AttrDict
from control.authoidc import AuthOidc as AuthOidcCls


def prepare(design=False, trivial=False):
    """Prepares the way for setting up the Flask webapp.

    Several classes are instantiated with a singleton object;
    each of these objects has a dedicated task in the app:

    * `control.config.Config.Settings`: all configuration aspects
    * `control.messages.Messages`: handle all messaging to user and sysadmin
    * `control.mongo.Mongo`: higher-level commands to the MongoDb
    * `control.viewers.Viewers`: support the third party 3D viewers
    * `control.wrap.Wrap`: several lengthy functions to wrap concepts into HTML
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

    Returns
    -------
    AttrDict
        A dictionary keyed by the names of the singleton objects and valued
        by the singleton objects themselves.

    """
    if design:
        Settings = ConfigCls(MessagesCls(None), design=True).Settings
        Messages = MessagesCls(Settings)
        Tailwind = TailwindCls(Settings)

        return AttrDict(
            Settings=Settings, Messages=Messages, Mongo=None, Tailwind=Tailwind
        )

    elif trivial:
        Settings = AttrDict(dict(secret_key=None))
        Messages = None
        Mongo = None
        Viewers = None
        Wrap = None
        Content = None
        Publish = None
        Auth = None
        Pages = None
        AuthOidc = None
    else:
        Settings = ConfigCls(MessagesCls(None)).Settings
        Messages = MessagesCls(Settings)

        Mongo = MongoCls(Settings, Messages)

        Viewers = ViewersCls(Settings, Messages, Mongo)

        Wrap = WrapCls(Settings, Messages, Viewers)
        Tailwind = TailwindCls(Settings)
        Handlebars = Compiler()
        Content = ContentCls(Settings, Viewers, Messages, Mongo, Wrap)
        Publish = PublishCls(Settings, Messages, Mongo, Content, Tailwind, Handlebars)
        Auth = AuthCls(Settings, Messages, Mongo, Content)
        AuthOidc = AuthOidcCls()

        Wrap.addAuth(Auth)
        Content.addAuth(Auth)
        Wrap.addContent(Content)
        Viewers.addAuth(Auth)

        Pages = PagesCls(Settings, Viewers, Messages, Mongo, Content, Auth)
        Messages.setFlask()

    return AttrDict(
        Settings=Settings,
        Messages=Messages,
        Mongo=Mongo,
        Viewers=Viewers,
        Wrap=Wrap,
        Content=Content,
        Publish=Publish,
        Auth=Auth,
        Pages=Pages,
        AuthOidc=AuthOidc,
    )
