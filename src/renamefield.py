import sys

from pymongo import MongoClient

from control.environment import var
from control.prepareMigrate import prepare


HELP = """\
Rename a metadata field Pure3D data or remove it.

USAGE

python renamefield.py [options] source table pl/sg origfield newfield
python renamefield.py [options] source table pl/sg origfield -

The first version moves/merges values of a field into another field.
The second version removes a field altogether.

You have to specify the db where the renaming has to take place, the table in
that db, whether the field can have multiple values, and the original field
name and the new field name.

For single-value fields, the value in the old field will overwrite the value in then
new field.

For multiple values, the values in the old field will be merged into the values of
the new field.
If the current values of old or new fields are strings, they will be converted
in 1-element lists on before hand.  The resulting field is always a list, it
might be the empty list.

Source must be the name of a run mode of Pure3d: test, pilot, custom, or prod.

Renaming will be carried out directly in the specified database, except when the
--dry parameter is supplied.

If the source does not exist, renaming will fail, obviously.

Options:

--dry
    Report what will be changed, but do not execute the changes.

Examples

./renamefield.sh prod edition pl dc.subject dc.keyword --dry
./renamefield.sh prod edition sg lastPublished dc.datePublished --dry
./renamefield.sh prod site sg dc.title - --dry
./renamefield.sh prod site sg dc.abstract - --dry
./renamefield.sh prod site sg dc.description - --dry
./renamefield.sh prod site sg dc.provenance - --dry
"""

MODES = set(
    """
    test
    pilot
    custom
    prod
    """.strip().split()
)

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


def logical(record, path):
    fields = path.split(".")
    dataSource = record

    for field in fields[0:-1]:
        dataSource = dataSource.get(field, None)
        if dataSource is None:
            break

    return None if dataSource is None else dataSource.get(fields[-1], None)


def fieldRename(Settings, srcDb, table, mult, oldField, newField, dry):
    (client, allDatabases) = connect(Settings)

    if client is None:
        return False

    good = True

    if srcDb not in allDatabases:
        print(f"Source db does not exist: {srcDb}")
        return False

    srcConn = client[srcDb]
    dryRep = "(dry run) " if dry else ""

    doRemove = newField == "-"
    actionRep = "remove" if doRemove else "rename"
    paramRep = "" if doRemove else f" to {newField}"

    print(f"\t{dryRep}DB {srcDb}: {actionRep} {oldField} {paramRep}")

    srcTable = srcConn[table]
    records = list(srcTable.find())
    nRecs = len(records)
    plural = "" if nRecs == 1 else "s"
    print(f"\t\t{dryRep} table {table} with {nRecs} record{plural} ...")

    has = 0

    for record in records:
        old = logical(record, oldField)

        if doRemove:
            if old is None:
                msgo = "None"
            elif type(old) is list:
                msgo = f"[{len(old)}]" if len(old) else "[]"
            else:
                msgo = "str"

            has += 1
            print(f"\t\t\t{oldField}: {msgo} => Z")

            if not dry:
                srcTable.update_one({"_id": record["_id"]}, {"$unset": {oldField: ""}})

        else:
            new = logical(record, newField)

            if mult:
                if type(old) is list and not len(old) and type(new) is list:
                    continue
                else:
                    if old is None:
                        old = []
                        msgo = "None"
                    else:
                        if type(old) is list:
                            msgo = f"[{len(old)}]" if len(old) else "[]"
                        else:
                            msgo = "str"
                            old = [old]

                    if new is None:
                        msgn = "None"
                        new = []
                    else:
                        if type(new) is list:
                            msgn = f"[{len(new)}]" if len(new) else "[]"
                        else:
                            msgn = "str"
                            new = [new]
            else:
                if old is None:
                    msgo = "None"
                else:
                    msgo = "str"

                if new is None:
                    msgn = "None"
                else:
                    msgn = "str"

            has += 1
            newMerged = (
                sorted(set(old) | set(new)) if mult else (new if old is None else old)
            )
            msgd = (f"[{len(newMerged)}]" if len(newMerged) else "[]") if mult else "str"
            print(f"\t\t\t{oldField}: {msgo} + {newField}: {msgn} => {newField}: {msgd}")

            if not dry:
                srcTable.update_one(
                    {"_id": record["_id"]},
                    {
                        "$set": {newField: newMerged},
                        "$unset": {oldField: ""},
                    },
                )

    print(f"\t\t{dryRep} table {table} {actionRep} {has} of {nRecs} record{plural} ...")
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

    if len(args) != 5:
        print(
            "I need exactly five arguments: db, table, sg/pl, old field and new field"
        )
        return -1

    (db, table, mult, oldField, newField) = args

    if not isMode(db):
        print("DB argument must be one of test pilot custom prod")
        return -1

    if mult == "sg":
        mult = False
    elif mult == "pl":
        mult = True
    else:
        print("sg/pl argument must be one of sg pl")
        return -1

    actionRep = "removing" if newField == "-" else "renaming"

    print(f"Arguments OK: starting field {actionRep}")

    objects = prepare()

    Settings = objects.Settings
    database = Settings.database
    srcDb = f"{database}_{db}"

    if not fieldRename(Settings, srcDb, table, mult, oldField, newField, dryRun):
        return 1

    return 0


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
