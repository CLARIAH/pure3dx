from flask import (
    Flask,
    request,
    redirect,
    abort,
    session,
    render_template,
    make_response,
)


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
    session.pop(name, None)


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
