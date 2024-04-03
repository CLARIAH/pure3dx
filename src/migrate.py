"""Migrate Pure3D data

USAGE

python migrate.py [options] source destination

You have to specify from where and to where the file and db data must be migrated.

Source and destination can be given as directories in which file data resides
as well as a mongo db export.

But they can also be the name of a run mode of Pure3d: test, pilot, custom, or prod, or
any plain name that starts with exp (this is for testing and debugging).

Migration will never overwrite files or databases.
If the destination exists and is not empty, the operation will fail.

If the source does not exist, migration will fail too, obviously.

Options:

--dbonly
    Only migrate the database, no file system operations/checks will be performed
--fileonly
    Only migrate the filesystem, no mongodb operations/checks will be performed
"""

import sys
from tempfile import mkdtemp

from bson import BSON, decode_all
from pymongo import MongoClient

from control.environment import var
from control.files import (
    expanduser as ex,
    unexpanduser as ux,
    abspath,
    dirExists,
    dirMake,
    dirRemove,
    dirCopy,
    dirContents,
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

DRY_RUN = False
DRY = "... dry run ..."


def isMode(x):
    return x in MODES or "/" not in x and x.startswith("exp")


def inContainer():
    host = var("HOSTNAME") or ""
    return host.startswith("pure3d")


def connect(Settings):
    host = Settings.mongoHost if inContainer() else None
    port = Settings.mongoPort if inContainer() else Settings.mongoPortOuter

    try:
        print(f"Connect to MongoDB ({host}:{port})")
        client = MongoClient(
            host, port, username=Settings.mongoUser, password=Settings.mongoPassword
        )
    except Exception as e:
        print(f"Could not connect to MongoDb ({host}:{port})")
        print(f"{str(e)}")
        return (None, set())

    return (client, set(client.list_database_names()))


def copyDir(src, dst):
    if not dirExists(src):
        print(f"\tSource directory {ux(src)} does not exist.")
    elif src == dst or abspath(dst).startswith(abspath(src)):
        print(f"\tWill not copy {ux(src)} to (part of) itself: {ux(dst)}")
    elif dirExists(dst):
        print(f"\tWill not copy to an existing directory: {ux(dst)}")
    else:
        print(f"\tCopy files {ux(src)} => {ux(dst)}")

        if DRY_RUN:
            print(f"\t\t{DRY}")
            return True

        return dirCopy(src, dst, noclobber=True)

    return False


def copyDb(Settings, srcMode, srcDb, dstMode, dstDb):
    if srcMode or dstMode:
        (client, allDatabases) = connect(Settings)

        if client is None:
            return 1

        if srcMode:
            if srcDb not in allDatabases:
                print(f"Source db does not exist: {srcDb}")
                return False

            srcConn = client[srcDb]

        if dstMode:
            if dstDb in allDatabases:
                print(f"Destination db already exists: {dstDb}")
                return False

            if not DRY_RUN:
                dstConn = client[dstDb]

    if srcMode and dstMode:
        if not DRY_RUN:
            dbdir = mkdtemp()

        if exportDb(srcDb, srcConn, dbdir):
            good = importDb(dbdir, dstDb, dstConn)

        if not DRY_RUN:
            dirRemove(dbdir)

    elif srcMode:
        good = exportDb(srcDb, srcConn, dstDb)
    elif dstMode:
        good = importDb(srcDb, dstDb, dstConn)
    else:
        good = copyDir(srcDb, dstDb)

    if good:
        print("Migration successful")

    return 0 if good else 1


def importDb(src, dstDb, dstConn):
    print(f"\tDB import {ux(src)} into {dstDb}")

    good = True
    tables = [
        x.removesuffix(".bson") for x in dirContents(src)[0] if x.endswith(".bson")
    ]

    for table in tables:
        try:
            with open(f"{src}/{table}.bson", "rb") as f:
                records = decode_all(f.read())

            print(f"\t\ttable {table} {len(records)} record(s)")

            if DRY_RUN:
                print(f"\t\t{DRY}")
            else:
                dstConn[table].insert_many(records)
        except Exception as e:
            print(f"\tCould not import table {table}: {str(e)}")
            good = False

    return good


def exportDb(srcDb, srcConn, dst):
    print(f"\tDB export {srcDb} to {ux(dst)}")

    good = True

    if not DRY_RUN:
        dirMake(dst)

    for table in srcConn.list_collection_names():
        records = srcConn[table].find()

        try:
            n = 0

            bh = None if DRY_RUN else open(f"{dst}/{table}.bson", "wb")

            for record in records:
                if not DRY_RUN:
                    bh.write(BSON.encode(record))
                n += 1

            if not DRY_RUN:
                bh.close()

            plural = "" if n == 1 else "s"
            print(f"\t\t{DRY if DRY_RUN else ''} table {table} {n} record{plural}")
        except Exception as e:
            print(f"\tCould not export table {table}: {str(e)}")
            good = False

    return good


def getDir(Settings, mode):
    workingParent = Settings.workingParent
    return f"{workingParent}/{mode}"


def main(args):
    if "--help" in args:
        print(HELP)
        return 0

    newargs = []
    fileOnly = False
    dbOnly = False

    for arg in args:
        if arg == "--dbonly":
            dbOnly = True
        elif arg == "--fileonly":
            fileOnly = True
        else:
            newargs.append(arg)

    args = newargs

    if len(args) != 2:
        print("I need exactly two arguments: source and destination")
        return -1

    (src, dst) = args

    if isMode(src):
        srcMode = True
    else:
        srcMode = False
        src = abspath(ex(src))

    if isMode(dst):
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
    database = Settings.database

    if srcMode:
        srcFiles = getDir(Settings, src)
        srcDb = f"{database}_{src}"
    else:
        srcFiles = f"{src}/files"
        srcDb = f"{src}/db"

    if dstMode:
        dstFiles = getDir(Settings, dst)
        dstDb = f"{database}_{dst}"
    else:
        dstFiles = f"{dst}/files"
        dstDb = f"{dst}/db"

    if not dbOnly:
        if not copyDir(srcFiles, dstFiles):
            return 1

    if not fileOnly:
        if not copyDb(Settings, srcMode, srcDb, dstMode, dstDb):
            return 1

    return 0


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
