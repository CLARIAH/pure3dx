from wsgidav.wsgidav_app import WsgiDAVApp

from .prepare import prepare
from .app import appFactory as appFactoryMain
from .flask import appMake


def getWebdavApp(objects):
    """Configure a webapp that provides WebDAV.

    We get the WebDAV app ready-made from
    [WsgiDav](https://wsgidav.readthedocs.io/en/latest/),
    and configure it here.
    """
    Settings = objects.Settings

    webdavConfig = {
        "provider_mapping": {
            "/webdav/": {
                "root": Settings.workingDir,
                "readonly": False,
            },
        },
        "simple_dc": {"user_mapping": {"*": True}},
        "verbose": 1,
    }

    return WsgiDAVApp(webdavConfig)


def dispatchWebdav(app, webdavPrefix, webdavApp):
    """Combines the main app with the webdavapp.

    A WSGI app is essentially a function that takes a request
    environment and a start-response function and produces a response.

    We combine two wsgi apps by defining a new WSGI function
    out of the WSGI functions of the component apps.
    We call this function the dispatcher.

    The combined function works so that requests with urls starting
    with a certain prefix are dispatched to the webdav app,
    while all other requests are handled by the main app.

    However, we must do proper authorisation for the calls that
    are sent to the webdav app. But the business-logic for
    authorisation is in the main app, while we want to leave
    the code of the webdav app untouched.

    We solve this by making the dispatcher so that it
    feeds every WebDAV request to the main app first.
    We mark those requests by prepending `/auth` in front of the
    original url.

    The main app is programmed to react to such requests by
    returning a boolean to the dispatcher, instead of sending a
    response to the client.
    See `control.pages.Pages.authWebdav`.
    The dispatcher interprets this boolean as telling whether the
    request is authorized.
    If so, it sends the original request to the webdav app.
    If not, it prepends `/cannot` to the original url and sends
    the request to the main app, which is programmed to
    respond with a 404 to such requests.

    Parameters
    ----------
    app: object
        The original flask app.
    webdavPrefix: string
        Initial part of the url that is used as trigger to divert to the WEBDav app.
    webdavApp:
        A WEBDav server.
    """

    def wsgi_function(environ, start_response):
        """Internal function for to deliver as result.
        """
        url = environ.get("PATH_INFO", "")
        aimedAtWebdav = url.startswith(webdavPrefix)

        if aimedAtWebdav:
            theApp = webdavApp
            environ["PATH_INFO"] = f"/auth{url}"
            with app.request_context(environ) as ctx:
                ctx.push()
                authorized = app.dispatch_request()
                ctx.pop()
            if authorized:
                environ["PATH_INFO"] = url
                theApp = webdavApp
            else:
                environ["PATH_INFO"] = f"/cannot{url}"
                theApp = app.wsgi_app
        else:
            theApp = app.wsgi_app
        return theApp(environ, start_response)

    return wsgi_function


def appFactoryMaster():
    """Factory function for the master flask app.
    """
    app = appMake(__name__)
    # At the setting below does not seem to have any effect
    # app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    return app


def appFactory():
    """Make a WebDAV enabled app.

    * Combine the main app with an other wsgi app that can handle
    WebDAV requests.

    There is a Python module that offers a wsgi app out of the box
    that can talk WebDAV, we configure it in `getWebdavApp()`.

    The `dispatchWebdav()` function combines the current app with this
    WebDAV app at a deep level, before requests are fed to either app.

    !!! note "Authorisation"
        Authorisation of WebDAV requests happens in the main app.
        See `dispatchWebdav()`.

    !!! caution "Requirements for the server"
        When this Flask app runs and the Voyager software is run in edit mode,
        the client will fire a sequence  of webdav requests to the server.

        When the app is served by the default Flask development server, these
        requests will almost surely block the whole application.

        The solution is to run the app through a task runner like Gunicorn.
        However, the app does not run in debug mode then, so tracing errors becomes
        more difficult then.
    """

    trivial = False

    objects = prepare(trivial=trivial)

    if trivial:
        app = appFactoryMain(objects)
    else:
        origApp = appFactoryMain(objects)
        app = appFactoryMaster()
        objects.Messages.addApp(app)

        app.wsgi_app = dispatchWebdav(origApp, "/webdav/", getWebdavApp(objects))

    return app
