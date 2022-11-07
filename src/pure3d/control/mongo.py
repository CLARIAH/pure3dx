from pymongo import MongoClient
from bson.objectid import ObjectId

from control.helpers.generic import AttrDict


def castObjectId(value):
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

    try:
        oValue = ObjectId(value)
    except Exception:
        oValue = None
    return oValue


class Mongo:
    def __init__(self, Settings, Messages):
        """CRUD interface to content in the MongoDb database.

        This class has methods to connect to a MongoDb database,
        to query its data, to insert, update and delete data.

        It is instantiated by a singleton object.

        Parameters
        ----------
        Settings: `control.helpers.generic.AttrDict`
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        """
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)
        self.client = None
        self.mongo = None
        self.database = Settings.database

    def connect(self):
        """Make connection with MongoDb if there is no connection yet.

        The connection details come from `control.config.Config.Settings`.

        After a successful connection attempt, the connection handle
        is stored in the `client` and `mongo` members of the Mongo object.

        When a connection handle exists, this method does nothing.
        """
        Settings = self.Settings
        client = self.client
        mongo = self.mongo
        database = self.database

        if mongo is None:
            try:
                client = MongoClient(
                    Settings.mongoHost,
                    Settings.mongoPort,
                    username=Settings.mongoUser,
                    password=Settings.mongoPassword,
                )
                mongo = client[database]
            except Exception as e:
                self.Messages.error(
                    msg="Could not connect to the database",
                    logmsg=f"Mongo connection: `{e}`",
                )
            self.client = client
            self.mongo = mongo

    def disconnect(self):
        """Disconnect from the MongoDB.
        """
        client = self.client

        if client:
            client.close()

        self.client = None
        self.mongo = None

    def checkCollection(self, table, reset=False):
        """Make sure that a collection exists and (optionally) that it is empty.

        Parameters
        ----------
        table: string
            The name of the collection.
            If no such collection exists, it will be created.
        reset: boolean, optional False
            If True, and the collection existed before, it will be cleared.
            Note that the collection will not be deleted, but all its documents
            will be deleted.
        """

        Messages = self.Messages

        self.connect()
        client = self.client
        mongo = self.mongo

        if mongo[table] is None:
            try:
                client.create_collection(table)
            except Exception as e:
                Messages.error(
                    msg="Database action",
                    logmsg=f"Cannot create collection: `{table}`: {e}",
                )
        if reset:
            try:
                self.execute(table, "delete_many", {})
            except Exception as e:
                Messages.error(
                    msg="Database action",
                    logmsg=f"Cannot clear collection: `{table}`: {e}",
                )

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
        `control.helpers.generic.AttrDict`
            The single document found,
            or an empty `control.helpers.generic.AttrDict` if no document
            satisfies the criteria.
        """
        result = self.execute(table, "find_one", criteria, {})
        if result is None:
            if warn:
                Messages = self.Messages
                Messages.warning(logmsg=f"No record in {table} with {criteria}")
            result = {}
        return AttrDict(result)

    def insertItem(self, table, **fields):
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
        mongo = self.mongo

        method = getattr(mongo[table], command, None)
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
