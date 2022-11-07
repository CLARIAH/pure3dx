from flask import redirect


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
