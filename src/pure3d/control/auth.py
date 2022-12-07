from control.generic import AttrDict
from control.users import Users


class Auth(Users):
    def __init__(self, Settings, Messages, Mongo, Content):
        """All about authorised data access.

        This class knows users because it is based
        on the Users class.

        This class also knows content,
        and decides whether the current user is authorised to perform certain
        actions on content in question.

        It is instantiated by a singleton object.

        Parameters
        ----------
        Settings: `control.generic.AttrDict`
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        Mongo: object
            Singleton instance of `control.mongo.Mongo`.
        Content: object
            Singleton instance of `control.content.Content`.
        """
        super().__init__(Settings, Messages, Mongo)
        self.Content = Content

    def authorise(self, table, recordId=None, action=None, **masters):
        """Check whether an action is allowed on data.

        If the action is "create", recordId should not be passed, and masters
        are important.

        If the action is anything else, recordId should not be None,
        and masters should not be passed.

        Parameters
        ----------
        table: string
            the relevant table
        recordId: ObjectId
            The id of the record that is being accessed
            Not relevant for "create" actions.
        action: string, optional None
            The action for which permission is asked.
        masters: dict
            Only relevant for "create" actions.
            The master tables and ids of master records
            in them to which the new record will have a link.
            The tables are keys, the ids of the master records in those tables
            are values.

        Returns
        -------
        boolean | set
            For "create" actions: boolean, whether the action is allowed.
            For other actions: if action is passed, boolean whether action is allowed.
            If action is not passed: set of allowed actions.
        """

        isCreate = action == "create"

        if recordId is None and not isCreate or recordId is not None and isCreate:
            return False if action is None else set()
        return self._authoriseCreate(table, masters) if isCreate else self._authorise(table, recordId, action)

    def _authoriseCreate(self, table, masters):
        """Check whether a new record may be created in a table.

        Parameters
        ----------
        table: string
            the table into which a record has to be inserted.
        masters: dict
            The master tables and ids of master records
            in them to which the new record will have a link.
            The tables are keys, the ids of the master records in those tables
            are values.

        Returns
        -------
        boolean
            If `recordId` is None: whether the user is allowed to insert a new
            record in `table`, linked to the given masters.
        """
        Settings = self.Settings
        Mongo = self.Mongo

        User = self.myDetails()
        user = User.sub
        role = User.role

        tableRules = Settings.auth.tableRules
        thisTableRules = tableRules.get(table, AttrDict())
        stateInfo = thisTableRules.state
        initState = stateInfo.init
        theseRules = tableRules[initState]

        permission = "creator" in set(theseRules.get("site", {}).get(role, []))

        if permission:
            return True

        for (masterTable, masterId) in masters.items():
            if masterId is None:
                continue

            masterIdField = f"{masterTable}Id"
            master = {masterIdField: masterId}

            masterCrossTable = f"{masterTable}User"

            crossRecord = Mongo.getRecord(masterCrossTable, user=user, **master)
            if not crossRecord:
                continue
            masterRole = crossRecord.role

            masterRules = tableRules.get(masterTable, AttrDict())
            masterStateInfo = masterRules.state
            masterStateField = masterStateInfo.field
            masterRecord = Mongo.getRecord(masterTable, _id=masterId)
            masterState = masterRecord[masterStateField]
            theseMasterRules = masterRules[masterState]

            permission = permission or "creator" in set(
                theseMasterRules.get(masterTable, {}).get(masterRole, [])
            )
            if permission:
                break

        return permission

    def _authorise(self, table, recordId, action=None):
        """Gather the access conditions for the relevant record or table.

        Parameters
        ----------
        table: string
            the table that is being used
        recordId: ObjectId
            The id of the record that is being accessed
        action: string, optional None
            The action for which permission is asked.

        Returns
        -------
        set | boolean
            If `action` is passed: whether the action is permitted.
            Otherwise: the set of permitted actions.
        """
        Settings = self.Settings
        Mongo = self.Mongo
        datamodel = Settings.datamodel
        masterInfo = datamodel.master
        linkInfo = datamodel.link

        User = self.myDetails()
        user = User.sub
        role = User.role

        tableRules = Settings.auth.tableRules
        thisTableRules = tableRules.get(table, AttrDict())
        stateInfo = thisTableRules.state
        stateField = stateInfo.field

        record = Mongo.getRecord(table, _id=recordId)
        state = record[stateField]

        theseRules = tableRules[state]

        permissions = set(theseRules.get("site", {}).get(role, []))

        for masterTable in masterInfo.get(table, []):
            masterCrossTable = f"{masterTable}User"
            if f"{masterTable}User" not in linkInfo:
                continue

            masterIdField = f"{masterTable}Id"
            masterId = record[masterIdField]
            master = {masterIdField: masterId}

            crossRecord = Mongo.getRecord(masterCrossTable, user=user, **master)
            if not crossRecord:
                continue
            masterRole = crossRecord.role

            masterRules = tableRules.get(masterTable, AttrDict())
            masterStateInfo = masterRules.state
            masterStateField = masterStateInfo.field
            masterRecord = Mongo.getRecord(masterTable, _id=masterId)
            masterState = masterRecord[masterStateField]
            theseMasterRules = masterRules[masterState]

            permissions |= set(
                theseMasterRules.get(masterTable, {}).get(masterRole, [])
            )

        return permissions if action is None else action in permissions

    def makeSafe(self, table, recordId, action):
        """Changes an action into an allowed action if needed.

        This function 'demotes' an action to an allowed action if the
        action itself is not allowed.

        In practice, if the action is `update` or `delete`, but that is not
        allowed, it is changed into `read`.

        If `read` itself is not allowed, None is returned.

        Parameters
        ----------
        table: string
            The table in which the record exists.
        recordId: ObjectId
            The id of the record.
        action: string
            An intended action.

        Returns
        -------
        string or None
            The resulting safe action.
        """
        actions = self.authorise(table, recordId=recordId)
        return action if action in actions else "read" if "read" in actions else None
