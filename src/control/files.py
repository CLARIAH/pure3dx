import os
import yaml
import json
import re
from shutil import rmtree, copytree, copy

from control.generic import deepAttrDict


THREE_EXT = {"glb", "gltf"}
THREE_EXT_PAT = "|".join(THREE_EXT)

IMAGE_RE = re.compile(r"""^.*\.(png|jpg|jpeg)$""", re.I)
THREED_RE = re.compile(rf"""^.*\.({THREE_EXT_PAT})$""", re.I)

DS_STORE = ".DS_Store"


def str_presenter(dumper, data):
    """configures yaml for dumping multiline strings
    Ref: https://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data
    """
    if data.count("\n") > 0:  # check for multiline string
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")

    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, str_presenter)
yaml.representer.SafeRepresenter.add_representer(str, str_presenter)


def normpath(path):
    if path is None:
        return None
    norm = os.path.normpath(path)
    return "/".join(norm.split(os.path.sep))


_tildeDir = normpath(os.path.expanduser("~"))
_homeDir = _tildeDir


scanDir = os.scandir
walkDir = os.walk
splitExt = os.path.splitext
mTime = os.path.getmtime


def abspath(path):
    return normpath(os.path.abspath(path))


def expanduser(path):
    nPath = normpath(path)
    if nPath.startswith("~"):
        return f"{_homeDir}{nPath[1:]}"

    return nPath


def unexpanduser(path):
    nPath = normpath(path)

    return nPath.replace(_homeDir, "~")


def prefixSlash(path):
    """Prefix a / before a path if it is non-empty and not already starts with it."""
    return f"/{path}" if path and not path.startswith("/") else path


def dirEmpty(target):
    target = normpath(target)
    return not os.path.exists(target) or not os.listdir(target)


def clearTree(path):
    """Remove all files from a directory, recursively, but leave subdirectories.

    Reason: we want to inspect output in an editor.
    But if we remove the directories, the editor looses its current directory
    all the time.

    Parameters
    ----------
    path:
        The directory in question. A leading `~` will be expanded to the user's
        home directory.
    """

    subdirs = []
    path = expanduser(path)

    with os.scandir(path) as dh:
        for i, entry in enumerate(dh):
            name = entry.name
            if name.startswith("."):
                continue
            if entry.is_file():
                os.remove(f"{path}/{name}")
            elif entry.is_dir():
                subdirs.append(name)

    for subdir in subdirs:
        clearTree(f"{path}/{subdir}")


def initTree(path, fresh=False, gentle=False):
    """Make sure a directory exists, optionally clean it.

    Parameters
    ----------
    path:
        The directory in question. A leading `~` will be expanded to the user's
        home directory.

        If the directory does not exist, it will be created.

    fresh: boolean, optional False
        If True, existing contents will be removed, more or less gently.

    gentle: boolean, optional False
        When existing content is removed, only files are recursively removed, not
        subdirectories.
    """

    path = expanduser(path)
    exists = os.path.exists(path)
    if fresh:
        if exists:
            if gentle:
                clearTree(path)
            else:
                rmtree(path)

    if not exists or fresh:
        os.makedirs(path, exist_ok=True)


def dirNm(path, up=1):
    """Get the directory part of a file name.

    Parameters
    ----------
    up: int, optional 1
        The number of levels to go up. Should be 1 or higher.
        If not passed, the parent directory is returned.
        If it is 0 or lower, the `path` itself is returned.
    """
    return path if up < 1 else os.path.dirname(dirNm(path, up - 1))


def fileNm(path):
    """Get the file part of a file name."""
    return os.path.basename(path)


def stripExt(path):
    """Strip the extension of a file name, if there is one."""
    (d, f) = (dirNm(path), fileNm(path))
    sep = "/" if d else ""
    return f"{d}{sep}{f.rsplit('.', 1)[0]}"


def splitPath(path):
    """Split a file name in a directory part and a file part."""
    return os.path.split(path)


def isFile(path):
    """Whether path exists and is a file."""
    return os.path.isfile(path)


def isDir(path):
    """Whether path exists and is a directory."""
    return os.path.isdir(path)


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


def fileMove(pathSrc, pathDst):
    """Moves a file if it exists as file.

    Wipes the destination file, if it exists.
    """
    if fileExists(pathSrc):
        fileRemove(pathDst)
    os.rename(pathSrc, pathDst)


def dirExists(path):
    """Whether a path exists as directory on the file system."""
    return (
        False
        if path is None
        else True
        if path == ""
        else os.path.isdir(path)
        if path
        else True
    )


def dirRemove(path):
    """Removes a directory if it exists as directory."""
    if dirExists(path):
        rmtree(path)


def dirMove(pathSrc, pathDst):
    """Moves a directory if it exists as directory.

    Refuses the operation in the target exists.
    """
    if not dirExists(pathSrc) or dirExists(pathDst):
        return False
    os.rename(pathSrc, pathDst)
    return True


def dirCopy(pathSrc, pathDst, noclobber=False):
    """Copies a directory if it exists as directory.

    Wipes the destination directory, if it exists.
    """
    if dirExists(pathSrc):
        if dirExists(pathDst):
            if noclobber:
                return False
        dirRemove(pathDst)
        copytree(pathSrc, pathDst)
        return True
    else:
        return False


def dirUpdate(pathSrc, pathDst, force=False, delete=True, level=-1, conservative=False):
    """Makes a destination dir equal to a source dir by copying newer files only.

    Files of the source dir that are missing or older in the destination dir are
    copied from the source to the destination.
    Files and directories in the destination dir that do not exist in the source
    dir are deleted, but this can be prevented.

    Parameters
    ----------
    pathSrc: string
        The source directory. It does not matter whether the directory ends with
        a slash or not, unless the directory is the root.
    pathDst: string
        The destination directory. It does not matter whether the directory ends with
        a slash or not, unless the directory is the root.
    force: boolean, optional False
        If True, files that are older in the source than in the destination will also
        be copied.
    delete: boolean, optional False
        Whether to delete items from the destination that do not exist in the source.
    level: integer, optional -1
        Whether to merge recursively and to what level. At level 0 we do not merge,
        but copy each item from source to destination.

        If we start with a negative level, we never reach level 0, so we apply merging
        always.

        If we start with level 0, we merge the files, but we copy the subdirectories.

        If we start with a positive level, we merge that many levels deep, after which
        we switch to copying.
    conservative: boolean, optional False
        If we are at level 0 and in the situation that we should copy a directory,
        we assume that if there is already a corresponding directory at the destination,
        it has the right contents, so we do not do the copying.
        For example, if we are copying versioned directories of software, we assume
        that directories with the same version names are the same

    Returns
    -------
    tuple
        *   boolean: whether the action was successful;
        *   integer: the amount of copy actions to destination directory
        *   integer: the amount of delete actions in the destination directory

    """

    if not dirExists(pathSrc):
        return (False, 0, 0)

    srcPath = pathSrc.rstrip("/")
    dstPath = pathDst.rstrip("/")

    if not dirExists(pathDst):
        if fileExists(pathDst):
            if not delete:
                return (False, 0, 0)

            fileRemove(pathDst)

        return (dirCopy(pathSrc, pathDst), 1, 0)

    (good, cActions, dActions) = (True, 0, 0)
    (srcFiles, srcDrs) = dirContents(pathSrc, asSet=True)
    (dstFiles, dstDirs) = dirContents(pathDst, asSet=True)

    level -= 1

    for file in srcFiles:
        if file == DS_STORE:
            continue

        src = f"{srcPath}/{file}"
        dst = f"{dstPath}/{file}"

        if file in dstDirs:
            if delete:
                dirRemove(dst)
                dActions += 1
            else:
                good = False
                continue

        if file not in dstFiles or force or mTime(src) > mTime(dst):
            fileCopy(src, dst)
            cActions += 1

    for file in dstFiles:
        dst = f"{dstPath}/{file}"

        if file == DS_STORE:
            fileRemove(dst)
            continue

        src = f"{srcPath}/{file}"

        if delete and file not in srcFiles:
            fileRemove(dst)
            dActions += 1

    # if level == 0:
    #   return (good, cActions, dActions)

    for dr in srcDrs:
        src = f"{srcPath}/{dr}"
        dst = f"{dstPath}/{dr}"

        if dr in dstFiles:
            if delete:
                fileRemove(dst)
                dActions += 1
            else:
                good = False
                continue

        if level == 0:
            if not (conservative and dirExists(dst)):
                dirCopy(src, dst)
                cActions += 1

            thisGood = True
        else:
            (thisGood, thisC, thisD) = dirUpdate(
                src,
                dst,
                force=force,
                delete=delete,
                level=level,
                conservative=conservative,
            )
            cActions += thisC
            dActions += thisD

        if not thisGood:
            good = False

    for dr in dstDirs:
        src = f"{srcPath}/{dr}"
        dst = f"{dstPath}/{dr}"

        if delete and dr not in srcDrs:
            dirRemove(dst)
            dActions += 1

    return (good, cActions, dActions)


def dirMake(path):
    """Creates a directory if it does not already exist as directory."""
    if not dirExists(path):
        os.makedirs(path, exist_ok=True)


def dirContents(path, asSet=False):
    """Gets the contents of a directory.

    Only the direct entries in the directory (not recursively), and only real files
    and folders.

    The list of files and folders will be returned separately.
    There is no attempt to sort the files.

    Parameters
    ----------
    path: string
        The path to the directory on the file system.
    asSet: boolean, optional False
        If True, the files and directories will be delivered as sets, otherwise
        as tuples.

    Returns
    -------
    tuple of tuple
        The files and the subdirectories.
        These are given as names relative to the directory `path`,
        so `path` is not prepended to these names.
    """
    if not dirExists(path):
        return (set(), set()) if asSet else ((), ())

    files = []
    dirs = []

    for entry in os.listdir(path):
        if os.path.isfile(f"{path}/{entry}"):
            files.append(entry)
        elif os.path.isdir(f"{path}/{entry}"):
            dirs.append(entry)

    return (set(files), set(dirs)) if asSet else (tuple(files), tuple(dirs))


def dirAllFiles(path, ignore=None):
    """Gets all the files found by `path`.

    The result is just `[path]` if `path` is a file, otherwise the list of files under
    `path`, recursively.

    The files are sorted alphabetically by path name.

    Parameters
    ----------
    path: string
        The path to the file or directory on the file system.
    ignore: set
        Names of directories that must be skipped

    Returns
    -------
    tuple of string
        The names of the files under `path`, starting with `path`, followed
        by the bit relative to `path`.
    """
    if fileExists(path):
        return [path]

    if not dirExists(path):
        return []

    files = []

    if not ignore:
        ignore = set()

    for entry in os.listdir(path):
        name = f"{path}/{entry}"

        if os.path.isfile(name):
            files.append(name)
        elif os.path.isdir(name):
            if entry in ignore:
                continue
            files.extend(dirAllFiles(name, ignore=ignore))

    return tuple(sorted(files))


def getCwd():
    """Get current directory.

    Returns
    -------
    string
        The current directory.
    """
    return os.getcwd()


def chDir(directory):
    """Change to other directory.

    Parameters
    ----------
    directory: string
        The directory to change to.
    """
    return os.chdir(directory)


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


def readJson(text=None, plain=False, asFile=None, preferTuples=False):
    if asFile is None:
        cfg = json.loads(text)
    else:
        if fileExists(asFile):
            with open(asFile, encoding="utf8") as fh:
                cfg = json.load(fh)
        else:
            cfg = {}

    return cfg if plain else deepAttrDict(cfg, preferTuples=preferTuples)


def writeJson(data, asFile=None):
    if asFile is None:
        return json.dumps(data, ensure_ascii=False)

    with open(asFile, "w", encoding="utf8") as fh:
        json.dump(data, fh, ensure_ascii=False)


def readYaml(
    text=None,
    asFile=None,
    plain=False,
    preferTuples=True,
    defaultEmpty=True,
    ignore=False,
):
    """Reads a yaml file.

    Parameters
    ----------
    text: string, optional None
        The input text, should be valid YAML, but see `ignore`.
        If not given, the text is read from the file whose path is
        given in `asFile`
    asFile: string, optional None
        The path of the file on the file system from which the YAML is read.
        If not given, `text` is used. See also `ignore`.
    plain: boolean, optional False
        If True, the result is (recursively) converted to an AttrDict
    preferTuples: optional True
        When converting to an AttrDict, values of type lists are replaced by
        tuples.
        Has only effect if `plain` is False.
    defaultEmpty: boolean, False
        If True, when the yaml text is None or the file named by `asFile` does
        not exist, it returns an empty dict or AttrDict.
        If False, `None` is returned in such cases.
    ignore: boolean, False
        If the text is not valid YAML, do not raise an exception, but
        return the text itself.

    Returns
    -------
    AttrDict | void | string
        The data content of the yaml file if it exists.
    """
    if asFile is None:
        yamlText = text
    else:
        if fileExists(asFile):
            with open(asFile, encoding="utf8") as fh:
                yamlText = fh.read()
        else:
            yamlText = None

    if yamlText is None:
        cfg = {} if defaultEmpty else None
    else:
        try:
            cfg = yaml.load(yamlText, Loader=yaml.FullLoader)
        except Exception as e:
            if ignore:
                cfg = text
            else:
                cfg = None
                raise e

    return (
        cfg
        if plain
        else None
        if cfg is None
        else deepAttrDict(cfg, preferTuples=preferTuples)
    )


def writeYaml(data, asFile=None):
    if asFile is None:
        return yaml.dump(data, allow_unicode=True)

    with open(asFile, "w", encoding="utf8") as fh:
        yaml.dump(data, fh, allow_unicode=True, line_break=None)


def extNm(path):
    """Get the extension part of a file name.

    The dot is not included.
    If there is no extension, the empty string is returned.
    """
    parts = fileNm(path).rsplit(".", 1)
    return "" if len(parts) == 0 else parts[-1]


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
