def dispatchWebdav(app, webdavPrefix, webdavApp):
    """Leave the url intact after dispatching.

    This is like DispatcherMiddleware,
    but after dispatching the full url is passed to
    the chosen app, instead of removing the prefix that
    corresponds with the selected mount.
    """

    def wsgi_function(environ, start_response):
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
                environ["PATH_INFO"] = f"/no{url}"
                theApp = app
        else:
            theApp = app
        return theApp(environ, start_response)

    return wsgi_function
