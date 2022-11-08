import os


def var(name):
    """Retrieves the value of an environment variable.

    Parameters
    ----------
    name: string
        The name of the environment variable

    Returns
    -------
    string
        If the variable does not exist, the empty string is returned.
    """
    return os.environ.get(name, "")
