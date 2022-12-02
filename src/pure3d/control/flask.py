import re

from flask import (
    Flask,
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


PROTOCOL_RE = re.compile(
    r"""^https?:\/\/""", re.I
)


def initializing():
    """Whether the flask web app is already running.

    It is False during the initialization code in the app factory
    before the flask app is delivered.
    """
    return var("WERKZEUG_RUN_MAIN") is None


def make(*args, **kwargs):
    """Create the Flask app."""
    return Flask(*args, **kwargs)


def template(template, **kwargs):
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
    flash(*args, **kwargs)


def response(data):
    """Wrap data in a response.

    Parameters
    ----------
    data: any
        The data to be transferred in an HTTP response.

    Returns
    -------
    object
        The HTTP response
    """
    return make_response(data)


def send(path):
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


def stop():
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
    string or None
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


def method():
    """Get the request method."""
    return request.method


def arg(name):
    """Get the value of a request arg.

    Parameters
    ----------
    name: string
        The name of the arg.

    Returns
    -------
    string or None
        The value of the arg, if it is defined,
        else the None.
    """
    return request.args.get(name, None)


def data():
    """Get the request data.

    Returns
    -------
    bytes

    Useful for uploaded files.
    """
    return request.get_data(cache=False)


def values():
    return request.values


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
