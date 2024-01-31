import os
import json
import yaml

from shutil import rmtree, copytree, copy

from generic import deepAttrDict


def str_presenter(dumper, data):
    """configures yaml for dumping multiline strings
    Ref: https://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data
    """
    if data.count('\n') > 0:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


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


def dirNm(path):
    """Get the directory part of a file name."""
    return os.path.dirname(path)


def baseNm(path):
    """Get the file part of a file name."""
    return os.path.basename(path)


def stripExt(path):
    """Strip the extension of a file name, if there is one."""
    (d, f) = (dirNm(path), baseNm(path))
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


def dirUpdate(pathSrc, pathDst, force=False, delete=True, recursive=True):
    """Makes a destination dir equal to a source dir by copying newer files only.

    Files of the source dir that are missing or older in the destination dir are
    copied from the source to the destination.
    Files and directories in the destination dir that do not exist in the source
    dir are deleted.

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
    recursive: boolean, optional True
        Whether to perform the action recursively.
        If it is False, only the files in the source and destination are compared
        and, if needed, copied or deleted.
    """

    if not dirExists(pathSrc):
        return (False, 0, 0)

    srcPath = pathSrc.rstrip("/")
    dstPath = pathDst.rstrip("/")

    if not dirExists(pathDst):
        if recursive:
            return (dirCopy(pathSrc, pathDst), 1, 0)
        else:
            if fileExists(pathDst):
                return (False, 0, 0)
            dirMake(pathDst)

            for item in dirContents(pathSrc)[0]:
                fileCopy(f"{pathSrc}/{item}", f"{pathDst}/{item}")
            return (True, 1, 0)

    (good, cActions, dActions) = (True, 0, 0)
    (srcFiles, srcDirs) = dirContents(pathSrc, asSet=True)
    (dstFiles, dstDirs) = dirContents(pathDst, asSet=True)

    for item in srcFiles:
        src = f"{srcPath}/{item}"
        dst = f"{dstPath}/{item}"

        if delete and item in dstDirs:
            if dirExists(dst):
                dirRemove(dst)

        if item not in dstFiles or force or mTime(src) > mTime(dst):
            if item in dstDirs:
                if dirExists(dst):
                    dirRemove(dst)
            fileCopy(src, dst)
            cActions += 1

    for item in dstFiles:
        src = f"{srcPath}/{item}"
        dst = f"{dstPath}/{item}"

        if delete and item not in srcFiles:
            if fileExists(dst):
                fileRemove(dst)
                dActions += 1

    if not recursive:
        return (good, cActions, dActions)

    for item in srcDirs:
        src = f"{srcPath}/{item}"
        dst = f"{dstPath}/{item}"

        (thisGood, thisC, thisD) = dirUpdate(src, dst, force=force, delete=delete)

        if not thisGood:
            good = False
        cActions += thisC
        dActions += thisD

    for item in dstDirs:
        src = f"{srcPath}/{item}"
        dst = f"{dstPath}/{item}"

        if delete and item not in srcDirs:
            if dirExists(dst):
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
        The subdirectories and the files.
        These are given as names relative to the directory `path`,
        sp `path` is not prepended to these names.
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


def readYaml(text=None, plain=False, asFile=None, preferTuples=True):
    if asFile is None:
        cfg = yaml.load(text, Loader=yaml.FullLoader)
    else:
        if fileExists(asFile):
            with open(asFile, encoding="utf8") as fh:
                cfg = yaml.load(fh, Loader=yaml.FullLoader)
        else:
            cfg = {}

    return cfg if plain else deepAttrDict(cfg, preferTuples=preferTuples)


def writeYaml(data, asFile=None):
    if asFile is None:
        return yaml.dump(data, allow_unicode=True)

    with open(asFile, "w", encoding="utf8") as fh:
        yaml.dump(data, fh, allow_unicode=True, line_break=None)
