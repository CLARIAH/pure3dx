from pymongo import MongoClient
from bson.objectid import ObjectId

from control.helpers.generic import AttrDict


def castObjectId(value):
    """Try to cast the value as an ObjectId.
    Paramaters
    ----------
    value:string
        The value to cast, normally a string representation of a BSON object id.

    Returns
    -------
    objectId | None
        The corresponding BSON object id if the input is a valid representation of
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
        Settings: AttrDict
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
        client = self.client

        if client:
            client.close()

        self.client = None
        self.mongo = None

    def checkCollection(self, table, reset=False):
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

    def getRecord(self, table, **criteria):
        result = self.execute(table, "find_one", criteria, {})
        if result is None:
            Messages = self.Messages
            Messages.warning(logmsg=f"No record in {table} with {criteria}")
            result = {}
        return AttrDict(result)

    def execute(self, table, command, *args, **kwargs):
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
