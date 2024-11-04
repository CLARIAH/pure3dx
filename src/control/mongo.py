import os

from bson import ObjectId, BSON, decode_all
from bson.json_util import dumps as dumpjs
from pymongo import MongoClient

from control.flask import appStop
from control.generic import AttrDict, deepAttrDict
from control.files import dirMake, dirExists


class Mongo:
    @staticmethod
    def cast(value):
        """Try to cast the value as an ObjectId.
        Paramaters
        ----------
        value:string
            The value to cast, normally a string representation of a BSON ObjectId.

        Returns
        -------
        ObjectId | void
            The corresponding BSON ObjectId if the input is a valid representation of
            such an id, otherwise `None`.
        """

        if value is None:
            return None

        if isinstance(value, ObjectId):
            return value

        try:
            oValue = ObjectId(value)
        except Exception:
            oValue = None
        return oValue

    @staticmethod
    def isId(value):
        """Test whether a value is an ObjectId

        Parameters
        ----------
        value: any
        The value to test

        Returns
        -------
        boolean
            Whether the value is an objectId
        """
        return isinstance(value, ObjectId)

    def __init__(self, Settings, Messages):
        """CRUD interface to content in the MongoDb database.

        This class has methods to connect to a MongoDb database,
        to query its data, to create, update and delete data.

        It is instantiated by a singleton object.

        !!! note "string versus ObjectId"
            Some functions execute MongoDb statements, based on parameters
            whose values are MongoDb identifiers.
            These should be objects in the class `bson.objectid.ObjectId`.
            However, in many cases these ids enter the app as strings.

            In this module, such strings will be cast to proper ObjectIds,
            provided they are recognizable as values in a field whose name is
            `_id` or ends with `Id`.

        Parameters
        ----------
        Settings: AttrDict
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        """
        self.Settings = Settings
        runMode = Settings.runMode
        self.Messages = Messages
        Messages.debugAdd(self)
        self.client = None
        self.db = None
        self.database = f"{Settings.database}_{runMode}"

    def connect(self):
        """Make connection with MongoDb if there is no connection yet.

        The connection details come from `control.config.Config.Settings`.

        After a successful connection attempt, the connection handle
        is stored in the `client` and `db` members of the Mongo object.

        When a connection handle exists, this method does nothing.
        """
        Messages = self.Messages
        Settings = self.Settings
        client = self.client
        db = self.db
        database = self.database

        if db is None:
            try:
                client = MongoClient(
                    Settings.mongoHost,
                    Settings.mongoPort,
                    username=Settings.mongoUser,
                    password=Settings.mongoPassword,
                )
                db = client[database]
            except Exception as e:
                Messages.error(
                    msg="Could not connect to the database",
                    logmsg=f"Mongo connection: `{e}`",
                )
            self.client = client
            self.db = db

    def disconnect(self):
        """Disconnect from the MongoDB."""
        client = self.client

        if client:
            client.close()

        self.client = None
        self.db = None

    def tables(self):
        """List the existent tables in the database.

        Returns
        -------
        list
            The names of the tables.
        """
        self.connect()
        db = self.db

        return list(db.list_collection_names())

    def clearTable(self, table, delete=False):
        """Make sure that a table exists and that it is empty.

        Parameters
        ----------
        table: string
            The name of the table.
            If no such table exists, it will be created.
        delete: boolean, optional False
            If True, and the table existed before, it will be deleted.
            If False, the table will be cleared, i.e. all its records
            get deleted, but the table remains.
        """
        Messages = self.Messages

        self.connect()
        db = self.db

        if delete:
            if db[table] is not None:
                try:
                    db.drop_collection(table)
                    Messages.plain(
                        msg=f"dropped table `{table}`",
                        logmsg=f"dropped table `{table}`",
                    )
                except Exception as e:
                    Messages.error(
                        msg="Database action",
                        logmsg=f"Cannot delete table: `{table}`: {e}",
                    )
        else:
            if db[table] is None:
                try:
                    db.create_collection(table)
                except Exception as e:
                    Messages.error(
                        msg="Database action",
                        logmsg=f"Cannot create table: `{table}`: {e}",
                    )
            else:
                (good, count) = self.deleteRecords(table, {})
                if good:
                    Messages.plain(
                        msg=f"cleared table `{table} of {count} records`",
                        logmsg=f"cleared table `{table} of {count} records`",
                    )

    def get(self, table, record):
        """Get the record and recordId if only one of them is specified.

        If the record is specified by id, the id maybe an ObjectId or a string,
        which will then be cast to an ObjectId.

        Parameters
        ----------
        table: string
            The table in which the record can be found
        record: string | ObjectID | AttrDict | void
            Either the id of the record, or the record itself.

        Returns
        -------
        tuple
            * ObjectId: the id of the record
            * AttrDict: the record itself

            If `record` is None, both members of the tuple are None
        """

        if record is None:
            return (None, None)

        if type(record) is str:
            record = self.getRecord(table, _id=self.cast(record))
        elif self.isId(record):
            record = self.getRecord(table, _id=record)
        recordId = record._id
        return (recordId, record)

    def getRecord(self, table, warn=True, stop=True, **criteria):
        """Get a single record from a table.

        Parameters
        ----------
        table: string
            The name of the table from which we want to retrieve a single record.
        warn: boolean, optional True
            If True, warn if there is no record satisfying the criteria.
        stop: boolean, optional True
            If the command is not successful, stop after issuing the
            error, do not return control.
        criteria: dict
            A set of criteria to narrow down the search.
            Usually they will be such that there will be just one record
            that satisfies them.
            But if there are more, a single one is chosen,
            by the mechanics of the built-in MongoDb command `findOne`.

        Returns
        -------
        AttrDict
            The single record found,
            or an empty AttrDict if no record
            satisfies the criteria.
        """
        Messages = self.Messages

        (good, result) = self.execute(
            table, "find_one", criteria, {}, warn=False, stop=stop
        )
        if not good or result is None:
            if warn:
                Messages.warning(
                    msg=f"Could not find that {table}",
                    logmsg=f"No record in {table} with {criteria}",
                )
            result = {}
        return deepAttrDict(result)

    def getList(self, table, stop=True, sort=None, asDict=False, **criteria):
        """Get a list of records from a table.

        Parameters
        ----------
        table: string
            The name of the table from which we want to retrieve records.
        stop: boolean, optional True
            If the command is not successful, stop after issuing the
            error, do not return control.
        sort: string | function, optional None
            Sort key. If `None`, the results will not be sorted.
            If a string, it is the name of a field by which the results
            will be sorted in ascending order.
            If a function, the function should take a record as input and return a
            value. The records will be sorted by this value.
        asDict: boolean or string, optional False
            If False, returns a list of records as result. If True or a string, returns
            the same records, but now as dict, keyed by the `_id` field if
            asDict is True, else keyed by the field in dictated by asDict.
        criteria: dict
            A set of criteria to narrow down the search.

        Returns
        -------
        list of AttrDict
            The list of records found, empty if no records are found.
            Each record is cast to an AttrDict.
        """
        (good, result) = self.execute(table, "find", criteria, {}, stop=stop)
        if not good:
            return []

        unsorted = [deepAttrDict(record) for record in result]

        if sort is None:
            result = unsorted
        else:
            sortFunc = (lambda r: r[sort] or "") if type(sort) is str else sort
            result = sorted(unsorted, key=sortFunc)

        return (
            {r[asDict]: r for r in result}
            if type(asDict) is str
            else {r._id: r for r in result}
            if asDict
            else result
        )

    def deleteRecord(self, table, stop=True, **criteria):
        """Deletes a single record from a table.

        Parameters
        ----------
        table: string
            The name of the table from which we want to delete a single record.
        stop: boolean, optional True
            If the command is not successful, stop after issuing the
            error, do not return control.
        criteria: dict
            A set of criteria to narrow down the selection.
            Usually they will be such that there will be just one record
            that satisfies them.
            But if there are more, a single one is chosen,
            by the mechanics of the built-in MongoDb command `updateOne`.

        Returns
        -------
        boolean
            Whether the delete was successful
        """
        (good, result) = self.execute(table, "delete_one", criteria, stop=stop)
        return result.deleted_count > 0 if good else False

    def deleteRecords(self, table, stop=True, **criteria):
        """Delete multiple records from a table.

        Parameters
        ----------
        table: string
            The name of the table from which we want to delete a records.
        stop: boolean, optional True
            If the command is not successful, stop after issuing the
            error, do not return control.
        criteria: dict
            A set of criteria to narrow down the selection.

        Returns
        -------
        boolean, integer
            Whether the command completed successfully and
            how many records have been deleted
        """
        (good, result) = self.execute(table, "delete_many", criteria, stop=stop)
        count = result.deleted_count if good else 0
        return (good, count)

    def updateRecord(self, table, updates, stop=True, **criteria):
        """Updates a single record from a table.

        Parameters
        ----------
        table: string
            The name of the table in which we want to update a single record.
        updates: dict
            The fields that must be updated with the values they must get.
            If the value `None` is specified for a field, that field will be set to
            null.
        stop: boolean, optional True
            If the command is not successful, stop after issuing the
            error, do not return control.
        criteria: dict
            A set of criteria to narrow down the selection.
            Usually they will be such that there will be just one record
            that satisfies them.
            But if there are more, a single one is chosen,
            by the mechanics of the built-in MongoDb command `updateOne`.

        Returns
        -------
        boolean
            Whether the update was successful
        """
        (good, result) = self.execute(
            table, "update_one", criteria, {"$set": updates}, stop=stop
        )
        return result.modified_count > 0 if good else False

    def insertRecord(self, table, stop=True, **fields):
        """Inserts a new record in a table.

        Parameters
        ----------
        table: string
            The table in which the record will be inserted.
        stop: boolean, optional True
            If the command is not successful, stop after issuing the
            error, do not return control.
        **fields: dict
            The field names and their contents to populate the new record with.

        Returns
        -------
        ObjectId
            The id of the newly inserted record, or None if the record could not be
            inserted.
        """
        (good, result) = self.execute(table, "insert_one", dict(**fields), stop=stop)
        return result.inserted_id if good else None

    def execute(self, table, command, *args, warn=True, stop=True, **kwargs):
        """Executes a MongoDb command and returns the result.

        Parameters
        ----------
        table: string
            The table on which to perform the command.
        command: string
            The built-in MongoDb command.
            Note that the Python interface requires you to write camelCase commands
            with underscores.
            So the Mongo command `findOne` should be passed as `find_one`.
        args: list
            Any number of additional arguments that the command requires.
        warn: boolean, optional True
            If True, warn if there is an error.
        stop: boolean, optional True
            If the command is not successful, stop after issuing the
            error, do not return control.
        kwargs: list
            Any number of additional keyword arguments that the command requires.

        Returns
        -------
        boolean, any
            The `boolean` is whether an error occurred.

            The `any` is whatever the MongoDb command returns.
            If the command fails, an error message is issued and
            `any=None` is returned.
        """
        Messages = self.Messages

        self.connect()
        db = self.db

        method = getattr(db[table], command, None)
        result = None
        good = True

        if method is None:
            if warn:
                Messages.error(
                    msg="Database action", logmsg=f"Unknown Mongo command: `{method}`"
                )
            good = False
        try:
            result = method(*args, **kwargs)
        except Exception as e:
            if warn:
                Messages.error(
                    msg="Database action",
                    logmsg=f"Executing Mongo command db.{table}.{command}: {e}",
                    stop=stop,
                )
            else:
                if stop:
                    appStop()
            good = False
            result = None

        return (good, result)

    def consolidate(self, record):
        """Resolves all links in a record to title values of linked records.

        The `_id` field of the record will be removed.
        Values of fields with names like `xxxId` will be looked up in table `xxx`,
        and will be replaced by the value of the `title` field of the found record.

        Parameters
        ----------
        record: dict or AttrDict
            The record data to consolidate.

        Returns
        -------
        dict
            All AttrDict values will be recursively transformed in ordinary dict values.
        """
        newRecord = AttrDict()

        for k, v in record.items():
            if k == "_id":
                continue
            if k.endswith("Id"):
                table = k.removesuffix("Id")
                linkedRecord = self.getRecord(table, _id=v, warn=False, stop=False)
                v = linkedRecord.title
                if v is not None:
                    newRecord[table] = v
            else:
                newRecord[k] = v

        return newRecord.deepdict()

    def mkBackup(self, dstBase, project=None, asJson=False):
        """Backs up data as record files in table folders.

        We do site-wide backups and project-specific backups.

        See also `control.backup.Backup.mkBackup`

        This function backs up database data in
        [`bson`](https://www.mongodb.com/basics/bson) and/or `json` format.

        Inspired by this
        [gist](https://gist.github.com/Lh4cKg/939ce683e2876b314a205b3f8c6e8e9d).

        Parameters
        ----------
        dstBase: string
            Destination folder.
            This folder will get subfolders `bson` and/or `json` in which
            the backups are stored.
        project: string, optional None
            If given, only backs up the given project.
        asJson: boolean, optional False
            Whether to create a backup in `json` format
        asBson: boolean, optional True
            Whether to create a backup in `bson` format

        Returns
        -------
        boolean
            Whether the operation was successful.
        """
        Messages = self.Messages
        self.connect()
        db = self.db
        tables = db.list_collection_names()

        dstb = f"{dstBase}/bson"
        dirMake(dstb)
        dstj = None
        jOpts = {}

        if asJson:
            dstj = f"{dstBase}/json"
            dirMake(dstj)
            jOpts = dict(ensure_ascii=False, indent=2, sort_keys=True)

        if project is None:
            for table in tables:
                records = db[table].find()
                n = self.writeRecords(table, records, dstb, dstj=dstj, jOpts=jOpts)
                plural = "" if n == 1 else ""
                Messages.info(msg=f"table {table} {n} record{plural}")
            return True

        (projectId, project) = self.get("project", project)
        records = db.project.find(dict(_id=projectId))
        n = self.writeRecords("project", records, dstb, dstj=dstj, jOpts=jOpts)
        records = db.edition.find(dict(projectId=projectId))
        n = self.writeRecords("edition", records, dstb, dstj=dstj, jOpts=jOpts)
        return True

    def writeRecords(self, table, records, dstb, dstj=None, jOpts={}):
        """Writes records to bson and possibly json file.

        If the destination file already exists, it will be wiped.

        Parameters
        ----------
        table: string
            Table that contains the record. Will be used as file name
            for the record to be written to.
        record: dict
            The record as it is retrieved from MongoDb
        dstb: string
            Destination folder for the bson file.
        dstj: string, optional None
            Destination folder for the json file.
            If `None`, no json file will be written.
        jOpts: dict, optional {}
            Format options for writing the json file.
        first

        Returns
        -------
        integer
            The number of records written
        """
        asJson = dstj is not None

        n = 0
        with open(f"{dstb}/{table}.bson", "wb") as bh:
            if asJson:
                jh = open(f"{dstj}/{table}.json", "w")
                jh.write("[\n")

            sep = ""
            for record in records:
                bh.write(BSON.encode(record))
                n += 1
                if asJson:
                    jh.write(sep)
                    jh.write(dumpjs(record, **jOpts))
                sep = ",\n"

            if asJson:
                jh.write("\n]\n")
                jh.close()

        return n

    def restoreBackup(self, src, project=None, clean=True):
        """Restores the database from record files in table folders.

        We do site-wide restores or project-specific restores.

        See also `control.backup.Backup.restoreBackup`

        This function restores database data given in
        [`bson`](https://www.mongodb.com/basics/bson).

        Inspired by this
        [gist](https://gist.github.com/Lh4cKg/939ce683e2876b314a205b3f8c6e8e9d).

        Parameters
        ----------
        src: string
            Source folder.
        project: string, optional None
            If given, only restores the given project.
        clean: boolean, optional True
            Whether to delete records from a table before
            restoring records to it.
            If `clean=True` then, in case of site-wide restores, all records
            will be cleaned. In case of project restores, only the relevant
            project/edition records will be cleaned.

        Returns
        -------
        boolean
            Whether the operation was successful.
        """
        Messages = self.Messages
        self.connect()
        db = self.db

        if not dirExists(src):
            Messages.warning(
                msg="Source directory not found",
                logmsg=f"Source directory {src} not found",
            )
            return False

        good = True

        if project is None:
            with os.scandir(src) as dh:
                for entry in dh:
                    name = entry.name
                    if not (entry.is_file() and name.endswith(".bson")):
                        continue

                    table = name.rsplit(".", 1)[0]

                    with open(f"{src}/{name}", "rb") as f:
                        records = decode_all(f.read())

                    Messages.info(msg=f"table {table} {len(records)} record(s)")
                    if db[table] is not None and clean:
                        (thisGood, count) = self.deleteRecords(table, {})
                        if not thisGood:
                            good = False

                    db[table].insert_many(records)
            return good

        (projectId, project) = self.get("project", project)

        with os.scandir(src) as dh:
            for entry in dh:
                name = entry.name
                if not (entry.is_file() and name.endswith(".bson")):
                    continue

                table = name.rsplit(".", 1)[0]

                if table not in {"project", "edition"}:
                    continue

                with open(f"{src}/{name}", "rb") as f:
                    records = decode_all(f.read())

                thisGood = True

                if table == "project":
                    records = [r for r in records if r._id == projectId]
                    nRecords = len(records)
                    if nRecords == 0:
                        Messages.warning(
                            msg=f"No {table} records found! Restore skipped.",
                            logmsg=(
                                f"Project restore {projectId}: "
                                f"No {table} records found! Skipped."
                            ),
                        )
                        continue
                    elif nRecords > 1:
                        Messages.warning(
                            msg=f"Multiple {table} records found. Will restore first.",
                            logmsg=(
                                f"Project restore {projectId}: "
                                f"Multiple ({nRecords}) {table} records found."
                            ),
                        )

                    record = records[0]

                    Messages.info(msg=f"Restoring {table} record ...")
                    if db[table] is not None and clean:
                        (thisGood, count) = self.deleteRecords(
                            table, {"_id": projectId}
                        )
                    if thisGood:
                        db[table].insert_one(record)
                    else:
                        good = False

                elif table == "edition":
                    records = [r for r in records if r.projectId == projectId]
                    nRecords = len(records)
                    if nRecords == 0:
                        Messages.info(
                            msg=f"No {table} records found.",
                            logmsg=(
                                f"Project restore {projectId}: "
                                f"No {table} records found."
                            ),
                        )
                        continue

                    Messages.info(msg=f"Restoring {table} records ...")
                    if db[table] is not None and clean:
                        (thisGood, count) = self.deleteRecords(
                            table, {"_id": projectId}
                        )
                    if thisGood:
                        db[table].insert_many(records)
                    else:
                        good = False
                else:
                    Messages.warning(
                        msg=f"Skipping {name} as it is not legal in a project backup",
                        logmsg=(
                            f"Skipping {name} as it is not legal in a project backup"
                        ),
                    )

        return good
