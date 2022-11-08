from flask import Flask, request, redirect, abort, session


def redirectResult(url, good):
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


def method():
    """Get the request method."""
    return request.method


def makeFlask(*args, **kwargs):
    """Create the Flask app."""
    return Flask(*args, **kwargs)


def arg(name):
    """Get the value of a request arg.

    Parameters
    ----------
    name: string
        The name of the arg.

    Returns
    -------
    string
        The value of the arg, if it is defined,
        else the empty string.
    """
    return request.args.get(name, "")


def sessionPop(name):
    """Pops a variable from the session.
    """
    session.pop(name, None)


def sessionSet(name, value):
    """Sets a session variable to a value.
    """
    session[name] = value
