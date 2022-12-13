from pymongo import MongoClient
from bson.objectid import ObjectId

from control.generic import deepAttrDict


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
        ObjectId | None
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
        Settings: `control.generic.AttrDict`
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        """
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)
        self.client = None
        self.db = None
        self.database = Settings.database

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
        record: string or ObjectID or AttrDict or None
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

    def getRecord(self, table, warn=True, **criteria):
        """Get a single document from a collection.

        Parameters
        ----------
        table: string
            The name of the collection from which we want to retrieve a single record.
        warn: boolean, optional True
            If True, warn if there is no record satisfying the criteria.
        criteria: dict
            A set of criteria to narrow down the search.
            Usually they will be such that there will be just one document
            that satisfies them.
            But if there are more, a single one is chosen,
            by the mechanics of the built-in MongoDb command `findOne`.

        Returns
        -------
        `control.generic.AttrDict`
            The single document found,
            or an empty `control.generic.AttrDict` if no document
            satisfies the criteria.
        """
        Messages = self.Messages

        result = self.execute(table, "find_one", criteria, {})
        if result is None:
            if warn:
                Messages.warning(logmsg=f"No record in {table} with {criteria}")
            result = {}
        return deepAttrDict(result)

    def getList(self, table, **criteria):
        """Get a list of documents from a collection.

        Parameters
        ----------
        table: string
            The name of the collection from which we want to retrieve records.
        criteria: dict
            A set of criteria to narrow down the search.

        Returns
        -------
        list of `control.generic.AttrDict`
            The list of documents found, empty if no documents are found.
            Each document is cast to an AttrDict.
        """

        result = self.execute(table, "find", criteria, {})
        return [deepAttrDict(record) for record in result]

    def updateRecord(self, table, updates, warn=True, **criteria):
        """Updates a single document from a collection.

        Parameters
        ----------
        table: string
            The name of the collection in which we want to update a single record.
        updates: dict
            The fields that must be updated with the values they must get
        warn: boolean, optional True
            If True, warn if there is no record satisfying the criteria.
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
        return self.execute(
            table,
            "update_one",
            criteria,
            {"$set": updates},
        )

    def insertRecord(self, table, **fields):
        """Inserts a new record in a table.

        Parameters
        ----------
        table: string
            The table in which the record will be inserted.
        **fields: dict
            The field names and their contents to populate the new record with.

        Returns
        -------
        ObjectId
            The id of the newly inserted record, or None if the record could not be
            inserted.
        """
        result = self.execute(table, "insert_one", dict(**fields))
        return result.inserted_id if result else None

    def execute(self, table, command, *args, **kwargs):
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
            )
            result = None

        return result
