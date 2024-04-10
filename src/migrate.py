"""Migrate Pure3D data

USAGE

python migrate.py [options] source destination

You have to specify from where and to where the file and db data must be migrated.

Source and destination can be given as directories in which file data resides
as well as a mongo db export.

But they can also be the name of a run mode of Pure3d: test, pilot, custom, or prod, or
any plain name that starts with exp (this is for testing and debugging).

Moreover, if the source is just `-` then a MongoDb import will be done into the
destination, which must be the name of a run mode of Pure3d.
The import will be done from the `db` directory belonging to the destination

And if the destination is just `-` then a MongoDb export will be done from the source,
which must be the name of a run mode of Pure3d.
The export will be done to the `db` directory belonging to the source.

The operations with `-` prepare for backup/restore operations by other software,
such as [Borg](https://borgbackup.readthedocs.io/en/stable/)

After

```
python migrate.py prod -
```

the directory `/app/data/working/prod` contains the complete production data, its
subdirectory `db` reflects the current content of the `pure3d_prod` database.
So the only thing Borg has to do is to add `/app/data/working/prod` to its backup
repository.

Conversely, when we restore a previous backup to production data, we use a Borg command
to restore a data directory to `/app/data/working/prod`.
After that we do

```
python migrate.py - prod
```

to import the data in the restored `/app/data/working/prod/db` directory into the
`pure3d_prod` database, and the restore is complete.


Migration will not overwrite files or databases, except when called with source or
destination equal to `-`.

In other cases the destination exists and is not empty, the operation will fail.

If the source does not exist, migration will fail too, obviously.

Options:

--dbonly
    Only migrate the database, no file system operations/checks will be performed
--fileonly
    Only migrate the filesystem, no mongodb operations/checks will be performed
"""

import sys

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
    stop = False

    if not dirExists(src):
        print(f"\tSource directory {ux(src)} does not exist.")
        stop = True
    elif src == dst or abspath(dst).startswith(abspath(src)):
        print(f"\tWill not copy {ux(src)} to (part of) itself: {ux(dst)}")
        stop = True
    elif dirExists(dst):
        (files, dirs) = dirContents(dst)
        stop = len(files) or len(dirs)
        if stop:
            print(f"\tWill not copy to an existing non-empty directory: {ux(dst)}")
    if not stop:
        print(f"\tCopy files {ux(src)} => {ux(dst)}")

        if DRY_RUN:
            print(f"\t\t{DRY}")
            return True

        return dirCopy(src, dst, noclobber=False)

    return False


def dbExport(Settings, srcMode, srcDb, srcDbFiles, isExportMode):
    if not srcMode:
        return True

    (client, allDatabases) = connect(Settings)

    if client is None:
        return False

    good = True

    if srcDb not in allDatabases:
        print(f"Source db does not exist: {srcDb}")
        return False

    srcConn = client[srcDb]

    if not DRY_RUN:
        print(f"\tDB export {srcDb} to {ux(srcDbFiles)}")

        if not DRY_RUN:
            if isExportMode:
                dirRemove(srcDbFiles)

            dirMake(srcDbFiles)

        for table in srcConn.list_collection_names():
            records = srcConn[table].find()

            try:
                n = 0

                bh = None if DRY_RUN else open(f"{srcDbFiles}/{table}.bson", "wb")

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


def dbImport(Settings, dstMode, dstDbFiles, dstDb, isImportMode):
    if not dstMode:
        return True

    (client, allDatabases) = connect(Settings)

    if client is None:
        return False

    good = True

    if dstMode:
        if dstDb in allDatabases:
            if isImportMode:
                client.drop_database(dstDb)
            else:
                print(f"Destination db already exists: {dstDb}")
                return False

        if not DRY_RUN:
            dstConn = client[dstDb]

            print(f"\tDB import {ux(dstDbFiles)} into {dstDb}")

            tables = [
                x.removesuffix(".bson")
                for x in dirContents(dstDbFiles)[0]
                if x.endswith(".bson")
            ]

            for table in tables:
                try:
                    with open(f"{dstDbFiles}/{table}.bson", "rb") as f:
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

    if src == "-":
        isImportMode = True
        srcMode = None
    else:
        isImportMode = False

        if isMode(src):
            srcMode = True
        else:
            srcMode = False
            src = abspath(ex(src))

    if dst == "-":
        isExportMode = True
        dstMode = None
    else:
        isExportMode = False

        if isMode(dst):
            dstMode = True
        else:
            dstMode = False
            dst = abspath(ex(dst))

    if isImportMode and isExportMode:
        print("source and destination cannot both be -")
        return -1

    if isImportMode and not dstMode:
        print("if source is - then destination must be a run mode")
        return -1

    if isExportMode and not srcMode:
        print("if destination is - then source must be a run mode")
        return -1

    if (isImportMode or isExportMode) and fileOnly:
        print(
            "source or destination is -, "
            "but database operations are prevented by --fileonly: nothing to do"
        )
        return 0

    if srcMode and dstMode and src == dst:
        print(f"{src} = {dst}: nothing to do")
        return 0

    print("Arguments OK: starting migration")

    objects = prepare(migrate=True)

    Settings = objects.Settings
    database = Settings.database

    if srcMode:
        srcFiles = getDir(Settings, src)
        srcDbFiles = f"{srcFiles}/db"
        srcDb = f"{database}_{src}"
    else:
        srcFiles = src
        srcDbFiles = f"{src}/db"
        srcDb = None

    if dstMode:
        dstFiles = getDir(Settings, dst)
        dstDbFiles = f"{dstFiles}/db"
        dstDb = f"{database}_{dst}"
    else:
        dstFiles = dst
        dstDbFiles = f"{dst}/db"
        dstDb = None

    if not fileOnly:
        if not dbExport(Settings, srcMode, srcDb, srcDbFiles, isExportMode):
            return 1

        if isExportMode:
            return 0

    if not isImportMode:
        if dbOnly:
            if not copyDir(srcDbFiles, dstDbFiles):
                return 1
        else:
            if not copyDir(srcFiles, dstFiles):
                return 1

    if not fileOnly:
        if not dbImport(Settings, dstMode, dstDbFiles, dstDb, isImportMode):
            return 1

    return 0


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
