import os
import yaml
import re

from control.helpers.generic import AttrDict


IMAGE_RE = re.compile(r"""^.*\.(png|jpg|jpeg)$""", re.I)


def readPath(filePath):
    """Reads the (textual) contents of a file.

    !!! note "Not for binary files"
        The file will not be opened in binary mode.
        Use this only for files with textual content.

    Parameters
    ----------
    filePath: string
        The path of the file on the file system.

    Returns
    -------
    string
        The contents of the file as unicode.
        If the file does not exist, the empty string is returned.
    """

    if os.path.isfile(filePath):
        with open(filePath) as fh:
            text = fh.read()
        return text
    return ""


def readYaml(path, defaultEmpty=False):
    """Reads a yaml file.

    Parameters
    ----------
    filePath: string
        The path of the file on the file system.
    defaultEmpty: boolean, optional False
        What to do if the file does not exist.
        If True, it returns an empty AttrDict,
        otherwise False.

    Returns
    -------
    AttrDict or None
        The data content of the yaml file if it exists.
    """
    if not os.path.isfile(path):
        return None
    with open(path) as fh:
        data = yaml.load(fh, Loader=yaml.FullLoader)
    return AttrDict(data)


def fileExists(path):
    """Whether a path exists as file on the file system.
    """
    return os.path.isfile(path)


def dirExists(path):
    """Whether a path exists as directory on the file system.
    """
    return os.path.isdir(path)


def listFiles(path, ext):
    """The list of all files in a directory with a certain extension.

    If the directory does not exist, the empty list is returned.
    """
    if not os.path.isdir(path):
        return []

    files = []

    nExt = len(ext)
    with os.scandir(path) as dh:
        for entry in dh:
            name = entry.name
            if name.endswith(ext) and entry.is_file():
                files.append(name[0:-nExt])

    return files


def listImages(path):
    """The list of all image files in a directory.

    If the directory does not exist, the empty list is returned.

    An image is a file with extension .png, .jpg, .jpeg or any of its
    case variants.
    """
    if not os.path.isdir(path):
        return []

    files = []

    with os.scandir(path) as dh:
        for entry in dh:
            name = entry.name
            if IMAGE_RE.match(name) and entry.is_file():
                files.append(name)

    return files
