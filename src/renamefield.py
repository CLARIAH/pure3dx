"""Rename a metadata field Pure3D data

USAGE

python renamefield.py [options] source origfield newfield

You have to specify the db where the renaming has to take place and the original
field name and the new field name.

If there is already a field with the new name, the contents of the old field will be
merged in, assuming that both field values are lists. If the current value(s)
of these fields are strings, they will be converted in 1-element lists on before hand.
The resulting field is always a list, it might be the empty list.

Source must be the name of a run mode of Pure3d: test, pilot, custom, or prod.

Renaming will be carried out directly in the specified database, except when the
--dry parameter is supplied.

If the source does not exist, renaming will fail, obviously.

Options:

--dry
    Report what will be changed, but do not execute the changes.
"""

import sys

from pymongo import MongoClient

from control.environment import var
from control.prepareMigrate import prepare


MODES = set(
    """
    test
    pilot
    custom
    prod
    """.strip().split()
)

HELP = """
Rename a metadata field in Pure3D data from one name to another.

USAGE

python renamefield.py [--dry] src origfield newfield
"""

DRY = "... dry run ..."


def isMode(x):
    return x in MODES


def inContainer():
    host = var("HOSTNAME") or ""
    print(f"HOSTNAME={host}")
    return host.startswith("pure3d")


def connect(Settings):
    inside = inContainer()
    host = Settings.mongoHost if inside else None
    port = Settings.mongoPort if inside else Settings.mongoPortOuter

    try:
        print(f"Connect to MongoDB (in container={inside}, {host}:{port})")
        client = MongoClient(
            host, port, username=Settings.mongoUser, password=Settings.mongoPassword
        )
    except Exception as e:
        print(f"Could not connect to MongoDb ({host}:{port})")
        print(f"{str(e)}")
        return (None, set())

    return (client, set(client.list_database_names()))


def fieldRename(Settings, srcDb, oldField, newField, dry):
    (client, allDatabases) = connect(Settings)

    if client is None:
        return False

    good = True

    if srcDb not in allDatabases:
        print(f"Source db does not exist: {srcDb}")
        return False

    srcConn = client[srcDb]
    dryRep = "(dry run) " if dry else ""

    print(f"\t{dryRep}DB {srcDb}: rename {oldField} to {newField}")

    for table in ("project", "edition"):
        srcTable = srcConn[table]
        records = list(srcTable.find())
        nRecs = len(records)
        plural = "" if nRecs == 1 else "s"
        print(f"\t\t{dryRep} table {table} with {nRecs} record{plural} ...")

        n = 0
        has = 0

        for record in records:
            n += 1

            if "dc" not in record:
                continue

            has += 1
            data = record["dc"]

            if oldField in data:
                old = data[oldField]

                if type(old) is list:
                    msgo = f"[{len(old)}]" if len(old) else "[]"
                else:
                    msgo = "str"
                    old = [old]
            else:
                msgo = "None"
                old = []

            if newField in data:
                new = data[newField]

                if type(new) is list:
                    msgn = f"[{len(new)}]" if len(new) else "[]"
                else:
                    msgn = "str"
                    new = [new]
            else:
                msgn = "None"
                new = []

            newMerged = sorted(set(old) | set(new))
            msgd = f"[{len(newMerged)}]" if len(newMerged) else "[]"

            print(
                f"\t\t\t{oldField}: {msgo} + {newField}: {msgn} => {newField}: {msgd}"
            )

            if not dry:
                srcTable.update_one(
                    {"_id": record["_id"]},
                    {
                        "$set": {f"dc.{newField}": newMerged},
                        "$unset": {f"dc.{oldField}": ""},
                    },
                )

        print(f"\t\t{dryRep} table {table} renamed {has} of {nRecs} record{plural} ...")
    return good


def main(args):
    if "--help" in args:
        print(HELP)
        return 0

    fieldArgs = []
    dryRun = False

    for arg in args:
        if arg == "--dry":
            dryRun = True
        else:
            fieldArgs.append(arg)

    args = fieldArgs

    if len(args) != 3:
        print("I need exactly three arguments: db, old field and new field")
        return -1

    (db, oldField, newField) = args

    print("Arguments OK: starting field renaming")

    objects = prepare()

    Settings = objects.Settings
    database = Settings.database
    srcDb = f"{database}_{db}"

    if not fieldRename(Settings, srcDb, oldField, newField, dryRun):
        return 1

    return 0


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
