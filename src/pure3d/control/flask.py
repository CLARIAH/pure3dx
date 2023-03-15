import re

from flask import (
    Flask,
    current_app,
    request,
    redirect,
    abort,
    session,
    render_template,
    make_response,
    send_file,
    flash,
)

from control.environment import var


PROTOCOL_RE = re.compile(r"""^https?:\/\/""", re.I)


def appInitializing():
    """Whether the flask web app is already running.

    If there is no `current_app`, we are surely initializing.

    But if flask runs in debug mode, two instances of the server will be started.
    When the second one is started, there is a second time that there is no
    `current_app`.
    In that case we alse inspect the environment variable
    `WERKZEUG_RUN_MAIN`. If it is set, we have already had the init stage of the
    first instance.
    """
    return var("WERKZEUG_RUN_MAIN") is None and not current_app


def appMake(*args, **kwargs):
    """Create the Flask app."""
    return Flask(*args, **kwargs)


def renderTemplate(template, **kwargs):
    """Renders a template.

    Parameters
    ----------
    template: string
        The name of the template, without extension.
    kwargs: dict
        The variables with values to fill in into the template.

    Returns
    -------
    object
        The response with as content the filled template.
    """
    return render_template(f"{template}.html", **kwargs)


def flashMsg(*args, **kwargs):
    """Gives user feedback using the Flask flash mechanism."""
    flash(*args, **kwargs)


def response(data, headers=None):
    """Wrap data in a response.

    Parameters
    ----------
    data: any
        The data to be transferred in an HTTP response.
    headers: dict

    Returns
    -------
    object
        The HTTP response
    """
    return make_response(data) if headers is None else make_response(data, headers)


def sendFile(path):
    """Send a file as a response.

    It is assumed that `path` exists as a readable file
    on the file system.
    The function will add headers based on the file
    extension.

    Parameters
    ----------
    path: string
        The file to be transferred in an HTTP response.

    Returns
    -------
    object
        The HTTP response
    """
    return send_file(path)


def redirectStatus(url, good):
    """Redirect.

    Parameters
    ----------
    url: string
        The url to redirect to
    good:
        Whether the redirection corresponds to a normal scenario or is the result of
        an error

    Returns
    -------
    response
        A redirect response with either code 302 (good) or 303 (bad)
    """

    code = 302 if good else 303
    if url == "":
        url = "/"
    return redirect(url, code=code)


def appStop():
    """Stop the request with a 404."""
    abort(404)


def sessionPop(name):
    """Pops a variable from the session.

    Parameters
    ----------
    name: string
        The name of the variable.

    Returns
    -------
    void
    """
    try:
        session.pop(name, None)
    except Exception:
        pass


def sessionGet(name):
    """Gets a variable from the session.

    Parameters
    ----------
    name: string
        The name of the variable.

    Returns
    -------
    string | void
        The value of the variable, if it exists,
        else None.
    """
    return session.get(name, None)


def sessionSet(name, value):
    """Sets a session variable to a value.

    Parameters
    ----------
    name: string
        The name of the variable.
    value: string
        The value that will be assigned to the variable

    Returns
    -------
    void
    """
    session[name] = value


def requestMethod():
    """Get the request method."""
    return request.method


def requestArg(name):
    """Get the value of a request arg.

    Parameters
    ----------
    name: string
        The name of the arg.

    Returns
    -------
    string | void
        The value of the arg, if it is defined,
        else the None.
    """
    return request.args.get(name, None)


def requestData():
    """Get the request data.

    Returns
    -------
    bytes

    Useful for uploaded files.
    """
    return request.get_data(cache=False)


def getReferrer():
    """Get the referrer from the request.

    We strip the root url from the referrer.

    If that is not possible, the referrer is an other site,
    in that case we substitute the home page.

    !!! caution "protocol mismatch"
        It has been observed that in some cases the referrer, as taken from the request,
        and the root url as taken from the request, differ in their protocol part:
        `http:` versus `https:`.
        Therefore we first strip the protocol part from both referrer and root url
        before we remove the prefix.

    Returns
    -------
    string
    """
    rootUrl = request.root_url
    rootUrl = PROTOCOL_RE.sub("", rootUrl)
    referrer = request.referrer
    referrer = PROTOCOL_RE.sub("", referrer)

    path = referrer.removeprefix(rootUrl)

    return "/" if path == referrer else path
