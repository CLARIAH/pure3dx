"""Initialize keywords for certain metadata fields in Pure3D.

USAGE

python initkeywords.py [options] source

You have to specify the db where the keywords should be inserted; the keywords
come from the datamodel yaml file.

If there are already keywords in the database, the initial set will be merged in.

Source must be the name of a run mode of Pure3d: test, pilot, custom, or prod.

Keyword addition will be carried out directly in the specified database, except when the
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
from control.files import readYaml


MODES = set(
    """
    test
    pilot
    custom
    prod
    """.strip().split()
)

HELP = """
Insert keywords for certain metadata fields in Pure3D data from one name to another.

USAGE

python insertkeyword.py [--dry] src
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


def insertKeywords(Settings, srcDb, dry):
    (client, allDatabases) = connect(Settings)

    if client is None:
        return False

    if srcDb not in allDatabases:
        print(f"Source db does not exist: {srcDb}")
        return False

    srcConn = client[srcDb]
    dryRep = "(dry run) " if dry else ""

    print(f"\t{dryRep}DB {srcDb}: insert keywords")

    datamodel = Settings.datamodel
    keywordFields = sorted(
        x for x, cfg in datamodel.fields.items() if cfg.get("tp", None) == "keyword"
    )
    keywordFile = "keywords.yml"
    yamlDir = Settings.yamlDir
    keywordPath = f"{yamlDir}/{keywordFile}"
    keywordSets = readYaml(asFile=keywordPath)

    good = True

    for field in keywordFields:
        if field not in keywordSets:
            print(f"No keywords for field '{field}' in {keywordPath}")
            good = False

    if not good:
        return False

    existing = {}
    srcKw = srcConn["keyword"]

    for record in srcKw.find():
        name = record["name"]
        value = record["value"]
        existing.setdefault(name, set()).add(value)

    for field in keywordFields:
        initValues = set(keywordSets[field])
        existingValues = existing.get(field, set())
        newValues = sorted(existingValues | initValues)
        nInit = len(initValues)
        nEx = len(existingValues)
        nNew = len(newValues)
        print(f"\t\t{dryRep}{field} {nInit} x init + {nEx} x existing = {nNew} new")

        if not dry:
            srcKw.delete_many(dict(name=field))
            srcKw.insert_many([dict(name=field, value=val) for val in newValues])

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

    if len(args) != 1:
        print("I need exactly one argument: db")
        return -1

    (db,) = args

    print("Arguments OK: starting keyword addition")

    objects = prepare()

    Settings = objects.Settings
    database = Settings.database
    srcDb = f"{database}_{db}"

    if not insertKeywords(Settings, srcDb, dryRun):
        return 1

    return 0


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
