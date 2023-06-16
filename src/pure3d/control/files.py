import os
import yaml
import re
from shutil import rmtree, copytree, copy

from control.generic import deepAttrDict


THREE_EXT = {"glb", "gltf"}
THREE_EXT_PAT = "|".join(THREE_EXT)

IMAGE_RE = re.compile(r"""^.*\.(png|jpg|jpeg)$""", re.I)
THREED_RE = re.compile(rf"""^.*\.({THREE_EXT_PAT})$""", re.I)


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
        If True, it returns an empty AttrDict
        otherwise False.

    Returns
    -------
    AttrDict | void
        The data content of the yaml file if it exists.
    """
    if not os.path.isfile(path):
        return None
    with open(path) as fh:
        data = yaml.load(fh, Loader=yaml.FullLoader)
    return deepAttrDict(data)


def dirNm(path):
    """Get the directory part of a file name."""
    return os.path.dirname(path)


def baseNm(path):
    """Get the file part of a file name."""
    return os.path.basename(path)


def fileExists(path):
    """Whether a path exists as file on the file system."""
    return os.path.isfile(path)


def fileRemove(path):
    """Removes a file if it exists as file."""
    if fileExists(path):
        os.remove(path)


def fileCopy(pathSrc, pathDst):
    """Copies a file if it exists as file.

    Wipes the destination file, if it exists.
    """
    if fileExists(pathSrc):
        fileRemove(pathDst)
        copy(pathSrc, pathDst)


def dirExists(path):
    """Whether a path exists as directory on the file system."""
    return os.path.isdir(path)


def dirRemove(path):
    """Removes a directory if it exists as directory."""
    if dirExists(path):
        rmtree(path)


def dirCopy(pathSrc, pathDst):
    """Copies a directory if it exists as directory.

    Wipes the destination directory, if it exists.
    """
    if dirExists(pathSrc):
        dirRemove(pathDst)
        copytree(pathSrc, pathDst)


def dirMake(path):
    """Creates a directory if it does not already exist as directory."""
    if not dirExists(path):
        os.makedirs(path, exist_ok=True)


def listDirs(path):
    """The list of all subdirectories in a directory.

    If the directory does not exist, the empty list is returned.
    """
    if not dirExists(path):
        return []

    subdirs = []

    with os.scandir(path) as dh:
        for entry in dh:
            if entry.is_dir():
                name = entry.name
                subdirs.append(name)

    return subdirs


def listFiles(path, ext):
    """The list of all files in a directory with a certain extension.

    If the directory does not exist, the empty list is returned.
    """
    if not dirExists(path):
        return []

    files = []

    nExt = len(ext)
    with os.scandir(path) as dh:
        for entry in dh:
            name = entry.name
            if name.endswith(ext) and entry.is_file():
                files.append(name[0:-nExt])

    return files


def listFilesAccepted(path, accept, withExt=True):
    """The list of all files in a directory that match a certain accepted header.

    If the directory does not exist, the empty list is returned.
    """
    if not dirExists(path):
        return []

    files = []

    exts = [ext.strip() for ext in accept.split(",")]

    with os.scandir(path) as dh:
        for entry in dh:
            name = entry.name
            for ext in exts:
                nExt = len(ext)
                if name.endswith(ext) and entry.is_file():
                    fileName = name if withExt else name[0:-nExt]
                    files.append(fileName)

    return files


def listImages(path):
    """The list of all image files in a directory.

    If the directory does not exist, the empty list is returned.

    An image is a file with extension .png, .jpg, .jpeg or any of its
    case variants.
    """
    if not dirExists(path):
        return []

    files = []

    with os.scandir(path) as dh:
        for entry in dh:
            name = entry.name
            if IMAGE_RE.match(name) and entry.is_file():
                files.append(name)

    return files


def list3d(path):
    """The list of all 3D files in a directory.

    If the directory does not exist, the empty list is returned.

    An image is a file with extension .gltf, .glb or any of its
    case variants.
    """
    if not dirExists(path):
        return []

    files = []

    with os.scandir(path) as dh:
        for entry in dh:
            name = entry.name
            if THREED_RE.match(name) and entry.is_file():
                files.append(name)

    return files
