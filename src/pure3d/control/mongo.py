from bson import ObjectId, BSON
from bson.json_util import dumps as dumpjs
from pymongo import MongoClient

from control.generic import AttrDict, deepAttrDict
from control.files import dirMake


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

    def collections(self):
        """List the existent collections in the database.

        Returns
        -------
        list
            The names of the collections.
        """
        self.connect()
        db = self.db

        return list(db.list_collection_names())

    def clearCollection(self, table, delete=False):
        """Make sure that a collection exists and that it is empty.

        Parameters
        ----------
        table: string
            The name of the collection.
            If no such collection exists, it will be created.
        delete: boolean, optional False
            If True, and the collection existed before, it will be deleted.
            If False, the collection will be cleared, i.e. all its documents
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
                        msg=f"dropped collection `{table}`",
                        logmsg=f"dropped collection `{table}`",
                    )
                except Exception as e:
                    Messages.error(
                        msg="Database action",
                        logmsg=f"Cannot delete collection: `{table}`: {e}",
                    )
        else:
            if db[table] is None:
                try:
                    db.create_collection(table)
                except Exception as e:
                    Messages.error(
                        msg="Database action",
                        logmsg=f"Cannot create collection: `{table}`: {e}",
                    )
            else:
                try:
                    self.execute(table, "delete_many", {})
                    Messages.plain(
                        msg=f"cleared collection `{table}`",
                        logmsg=f"cleared collection `{table}`",
                    )
                except Exception as e:
                    Messages.error(
                        msg="Database action",
                        logmsg=f"Cannot clear collection: `{table}`: {e}",
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
        """Get a single document from a collection.

        Parameters
        ----------
        table: string
            The name of the collection from which we want to retrieve a single record.
        warn: boolean, optional True
            If True, warn if there is no record satisfying the criteria.
        stop: boolean, optional True
            If the command is not successful, stop after issuing the
            error, do not return control.
        criteria: dict
            A set of criteria to narrow down the search.
            Usually they will be such that there will be just one document
            that satisfies them.
            But if there are more, a single one is chosen,
            by the mechanics of the built-in MongoDb command `findOne`.

        Returns
        -------
        AttrDict
            The single document found,
            or an empty AttrDict if no document
            satisfies the criteria.
        """
        Messages = self.Messages

        result = self.execute(table, "find_one", criteria, {}, stop=stop)
        if result is None:
            if warn:
                Messages.warning(
                    msg=f"Could not find that {table}",
                    logmsg=f"No record in {table} with {criteria}",
                )
            result = {}
        return deepAttrDict(result)

    def getList(self, table, stop=True, **criteria):
        """Get a list of documents from a collection.

        Parameters
        ----------
        table: string
            The name of the collection from which we want to retrieve records.
        stop: boolean, optional True
            If the command is not successful, stop after issuing the
            error, do not return control.
        criteria: dict
            A set of criteria to narrow down the search.

        Returns
        -------
        list of AttrDict
            The list of documents found, empty if no documents are found.
            Each document is cast to an AttrDict.
        """

        result = self.execute(table, "find", criteria, {}, stop=stop)
        return [deepAttrDict(record) for record in result]

    def deleteRecord(self, table, stop=True, **criteria):
        """Updates a single document from a collection.

        Parameters
        ----------
        table: string
            The name of the collection in which we want to update a single record.
        stop: boolean, optional True
            If the command is not successful, stop after issuing the
            error, do not return control.
        criteria: dict
            A set of criteria to narrow down the selection.
            Usually they will be such that there will be just one document
            that satisfies them.
            But if there are more, a single one is chosen,
            by the mechanics of the built-in MongoDb command `updateOne`.

        Returns
        -------
        boolean
            Whether the delete was successful
        """
        result = self.execute(table, "delete_one", criteria, stop=stop)
        n = result.deleted_count
        return n > 0

    def updateRecord(self, table, updates, stop=True, **criteria):
        """Updates a single document from a collection.

        Parameters
        ----------
        table: string
            The name of the collection in which we want to update a single record.
        updates: dict
            The fields that must be updated with the values they must get
        stop: boolean, optional True
            If the command is not successful, stop after issuing the
            error, do not return control.
        criteria: dict
            A set of criteria to narrow down the selection.
            Usually they will be such that there will be just one document
            that satisfies them.
            But if there are more, a single one is chosen,
            by the mechanics of the built-in MongoDb command `updateOne`.

        Returns
        -------
        boolean
            Whether the update was successful
        """
        result = self.execute(
            table, "update_one", criteria, {"$set": updates}, stop=stop
        )
        n = result.modified_count
        return n > 0

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
        result = self.execute(table, "insert_one", dict(**fields), stop=stop)
        return result.inserted_id if result else None

    def execute(self, table, command, *args, stop=True, **kwargs):
        """Executes a MongoDb command and returns the result.

        Parameters
        ----------
        table: string
            The collection on which to perform the command.
        command: string
            The built-in MongoDb command.
            Note that the Python interface requires you to write camelCase commands
            with underscores.
            So the Mongo command `findOne` should be passed as `find_one`.
        args: list
            Any number of additional arguments that the command requires.
        stop: boolean, optional True
            If the command is not successful, stop after issuing the
            error, do not return control.
        kwargs: list
            Any number of additional keyword arguments that the command requires.

        Returns
        -------
        any
            Whatever the MongoDb command returns.
            If the command fails, an error message is issued and
            None is returned.
        """
        Messages = self.Messages

        self.connect()
        db = self.db

        method = getattr(db[table], command, None)
        result = None

        if method is None:
            Messages.error(
                msg="Database action", logmsg=f"Unknown Mongo command: `{method}`"
            )
        try:
            result = method(*args, **kwargs)
        except Exception as e:
            Messages.error(
                msg="Database action",
                logmsg=f"Executing Mongo command db.{table}.{command}: {e}",
                stop=False,
            )
            result = None

        return result

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

        for (k, v) in record.items():
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

    def backup(self, dstBase, asJson=False):
        """Backs up the database as document files in collection folders.

        This function backs up database data in
        [`bson`](https://www.mongodb.com/basics/bson) and/or `json` format.

        Parameters
        ----------
        dst: string
            Destination folder.
            This folder will get subforlders `bson` and/or `json` in which
            the backups are stored.
        asJson: boolean, optional False
            Whether to create a backup in `json` format
        asBson: boolean, optional True
            Whether to create a backup in `bson` format
        """
        Messages = self.Messages
        self.connect()
        db = self.db
        collections = db.list_collection_names()

        dst = {}

        for fmt in ("bson", "json"):
            if fmt == "json" and not asJson:
                continue
            dst[fmt] = f"{dstBase}/{fmt}"
            dirMake(dst[fmt])

        dstb = dst["bson"]
        if asJson:
            dstj = dst["json"]
            jsonOptions = dict(ensure_ascii=False, indent=2, sort_keys=True)

        for collection in collections:
            n = 0
            with open(f"{dstb}/{collection}.bson", "wb") as bh:
                if asJson:
                    jh = open(f"{dstj}/{collection}.json", "w+")
                    jh.write("[\n")

                sep = ""
                for doc in db[collection].find():
                    bh.write(BSON.encode(doc))
                    n += 1
                    if asJson:
                        jh.write(sep)
                        jh.write(dumpjs(doc, **jsonOptions))
                    sep = ",\n"

                if asJson:
                    jh.write("\n]\n")
                    jh.close()

            Messages.info(msg=f"collection {collection} {n} document(s)")
