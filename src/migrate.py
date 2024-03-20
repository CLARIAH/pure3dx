"""Migrate Pure3D data

USAGE

python migrate.py source destination

You have to specify from where and to where the file and db data must be migrated.

Source and destination can be given as directories in which file data resides
as well as a mongo db export.

But they can also be the name of a run mode of Pure3d: test, pilot, custom, or prod.

Migration will never overwrite files.
If the destination exists and is not empty, the operation will fail.
"""

import sys
from tempfile import mkdtemp

from control.files import (
    expanduser as ex,
    unexpanduser as ux,
    abspath,
    dirRemove,
    dirCopy,
)
from control.prepare import prepare


MODES = set(
    """
    test
    pilot
    custom
    prod
    """.strip().split()
)

HELP = """
Migrate Pure3D data from one place or mode to another.

USAGE

python migrate.py src dst
"""


def copyDir(src, dst):
    if src == dst:
        print(f"\tCopy dir not needed because src == dst {src}")
        return True

    print(f"\tCopy files {ux(src)} => {ux(dst)}")
    return True
    return dirCopy(src, dst, noClobber=True)


def importDb(Mongo, src, mode):
    print(f"\tDB import {ux(src)} into {mode}")
    return True


def exportDb(Mongo, mode, dst):
    print(f"\tDB export {mode} to {ux(dst)}")
    return True


def getDir(Settings, mode):
    workingParent = Settings.workingParent
    return f"{workingParent}/{mode}"


def main(args):
    good = True

    if "--help" in args:
        print(HELP)
        return 0

    if len(args) != 2:
        print("I need exactly two arguments: source and destination")
        return -1

    (src, dst) = args

    if src in MODES:
        srcMode = True
    else:
        srcMode = False
        src = abspath(ex(src))

    if dst in MODES:
        dstMode = True
    else:
        dstMode = False
        dst = abspath(ex(dst))

    if srcMode and dstMode and src == dst:
        print(f"{src} = {dst}: nothing to do")
        return 0

    print("Arguments OK: starting migration")

    objects = prepare(migrate=True)

    Settings = objects.Settings
    Mongo = objects.Mongo

    if srcMode:
        srcFiles = getDir(Settings, src)
        srcDb = src
    else:
        srcFiles = f"{src}/files"
        srcDb = f"{src}/db"

    if dstMode:
        dstFiles = getDir(Settings, dst)
        dstDb = dst
    else:
        dstFiles = f"{dst}/files"
        dstDb = f"{dst}/db"

    if not copyDir(srcFiles, dstFiles):
        return 1

    if srcMode and dstMode:
        dbdir = mkdtemp()

        if exportDb(Mongo, srcDb, dbdir):
            good = importDb(Mongo, dbdir, dstDb)

        dirRemove(dbdir)

    elif srcMode:
        good = exportDb(Mongo, srcDb, dstDb)
    elif dstMode:
        good = importDb(Mongo, srcDb, dstDb)
    else:
        good = copyDir(srcFiles, dstFiles) and copyDir(srcDb, dstDb)

    if good:
        print("Migration successful")

    return 0 if good else 1


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
