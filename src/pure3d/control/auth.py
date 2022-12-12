from itertools import chain
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

    def authorise(self, table, record=None, action=None, **masters):
        """Check whether an action is allowed on data.

        If the action is "create", `record` should not be passed, and
        masters are important.

        If the action is anything else, `record` should not be None,
        and masters should not be passed.

        How do the authorisation rules work?

        First we consider the site-wise role of the user: guest, user, or admin.
        If the action is allowed on that basis, we return True.

        If not, we look whether the user has additional roles with regard
        to the record in question, or with any of its master records.

        If so, we apply the rules for those cases and see whether the action is
        permitted.

        The "create" action is a bit special, because we do not have any record
        to start with. But we do have master records specified as arguments,
        and this is the basis for applying additional user roles.

        Then we have the possibility that a record is in a certain state, e.g.
        projects may be visible or invisible, editions may be published or
        unpublished.

        For each of these states we have separate rules, so we inspect the
        states of the records and master records in order to select the
        appropriate rules.

        Parameters
        ----------
        table: string
            the relevant table
        record: ObjectId or AttrDict, optional None
            The id of the record that is being accessed or
            the record itself
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
        boolean | set | dict
            For "assign" actions: set of roles that may be assigned to another user
            for this record.

            For other actions: a boolean whether action is allowed.

            If no action is passed: dict keyed by the allowed actions, the values
            are sets for "assign" actions and booleans for other actions.
            Actions with a falsy permission (False or the empty set) are not included
            in the dict.
            So, to test whether any action is allowed, it suffices to test whether
            `action in result`
        """
        Messages = self.Messages
        isCreate = action == "create"

        if record is None and not isCreate or record is not None and isCreate:
            Messages.error(
                msg="Programming error in calculating authorization",
                logmsg=(
                    f"Wrong call to Auth.authorise with action {action} "
                    f"and record {record} in table {table}"
                ),
            )
            # this is a programming error
            return False if action is None else set()

        Settings = self.Settings
        Mongo = self.Mongo

        User = self.myDetails()
        user = User.sub
        role = User.role

        # we select the authorisation rules for this table

        auth = Settings.auth
        authRules = auth.authRules
        tableRules = authRules.get(table, AttrDict())

        # we need the state of the record that we want to apply the action to
        # If the action is create, we have no record.
        # We then use an initial state, given in the data model.
        # For all other actions, we read the state from the record,
        # its field is given in the data model.
        # If there is no state info, we assume there is no state.

        stateInfo = tableRules.state

        state = None

        if not isCreate:
            (recordId, record) = Mongo.get(table, record)

        if stateInfo is not None:
            if isCreate:
                state = stateInfo.init
            else:
                stateField = stateInfo.field
                record = Mongo.getRecord(table, _id=recordId)
                state = record[stateField]

        # we select the rules for the given state, if any

        rules = {
            act: actInfo[state] if stateInfo else actInfo
            for (act, actInfo) in tableRules.items()
            if act != "state"
        }

        # for each possible action, the rules specify the roles that may perform
        # that action.

        # We collect the set of all possible roles and organize them by table

        tableFromRole = auth.tableFromRole
        masterOf = auth.masterOf
        userCoupled = set(auth.userCoupled)

        # for each of the roles we have to determine whether the role is
        # * site wide (table = site)
        # * associated with a master table
        # * associated with a detail table

        # First we get the tables associated with each role

        allAllowedRoles = {
            role: tableFromRole[role]
            for role in set(chain.from_iterable(v.keys() for v in rules.values()))
        }

        # Then we determine which of these tables are master, detail, or none of
        # those, with respect to the table we are acting upon.

        allRelatedTables = {
            relatedTable: "self"
            if relatedTable == table
            else "master"
            if table in masterOf.get(relatedTable, [])
            else "detail"
            if relatedTable in masterOf.get(table, [])
            else ""
            for relatedTable in allAllowedRoles.values()
        }

        # for each of the relatedTables we compute whether it leads to extra roles
        # for the current user.
        # We look for related records in those tables to which the user is related.

        userRoles = {role}

        for (relatedTable, kind) in allRelatedTables.items():
            if kind == "":
                continue

            if relatedTable not in userCoupled:
                continue

            relatedIdField = f"{relatedTable}Id"
            relatedCrossTable = f"{relatedTable}User"

            if kind == "self":
                if isCreate:
                    continue

                crit = {relatedIdField: recordId}
                crossRecord = Mongo.getRecord(relatedCrossTable, user=user, **crit)
                extraRole = crossRecord.role

                if extraRole is not None:
                    userRoles.add(extraRole)

            elif kind == "master":
                # if recordId is given, we find a masterId in the record
                # else we use a masterId from the masters argument to the function

                if isCreate:
                    masterId = masters.get(relatedTable, None)
                else:
                    masterId = record[relatedIdField]

                # we do not need the master record itself,
                # instead we are interested in the coupling record
                # of the relatedTable with the user table
                # because we find a user role there

                crit = {relatedIdField: masterId}
                crossRecord = Mongo.getRecord(relatedCrossTable, user=user, **crit)
                extraRole = crossRecord.role

                if extraRole is not None:
                    userRoles.add(extraRole)

            elif kind == "detail":
                # only relevant if recordId is given, because
                # if we want to create a record, none of its details are yet there.

                if isCreate:
                    continue

                # look up all detail records in the detail table

                idField = f"{table}Id"
                crit = {idField: recordId}
                detailRecords = Mongo.getList(relatedTable, **crit)
                detailIds = [detailRecord._id for detailRecord in detailRecords]

                # we need the cross records between these detail records and
                # the user table, and we read the extra roles from those
                # records

                crit = {relatedIdField: {"$in": detailIds}}
                crossRecords = Mongo.getList(relatedCrossTable, user=user, **crit)

                extraRoles = {crossRecord.role for crossRecord in crossRecords} - {None}

                userRoles |= extraRoles

        # Now we have
        # 1. userRoles:
        #    the set of roles that this user has mbt to the given record
        #    and all of its relevant master and detail records
        # 2. rules
        #    a dictionary mapping each possible action to the
        #    roles a user needs to have to perform that action
        #    The roles itself are given as a dict, keyed by the role
        #    and valued by a boolean or a set, depending on the action.

        # We compute the allowed actions resulting in a dict keyed by the action
        # and valued by a boolean for most actions and a set for the action "assign"

        allowedActions = {}

        for (act, requiredRoles) in rules.items():
            if act == "assign":
                permission = set()
                for presentRole in userRoles:
                    permission |= set(requiredRoles.get(presentRole, []))
                if permission:
                    allowedActions[act] = permission
            else:
                permission = False
                for presentRole in userRoles:
                    if requiredRoles.get(presentRole, False):
                        permission = True
                        break
                if permission:
                    allowedActions[act] = True

        # Finally we return the result.
        #
        # If no action is given, we return the allowedActions straightaway.
        # Otherwise we lookup the given action in allowedActions, get the
        # associated value (or provide a falsy default), and return that.
        #
        # Note that in the case of the assign action a set of roles is returned,
        # the roles that this user may assign to another user for this record.

        return (
            allowedActions
            if action is None
            else allowedActions.get(action, set() if action == "assign" else False)
        )

    def makeSafe(self, table, record, action):
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
        record: ObjectId or AttrDict
            The id of the record or the record itself.
        action: string
            An intended action.

        Returns
        -------
        string or None
            The resulting safe action.
        """
        actions = self.authorise(table, record=record)
        return action if action in actions else "read" if "read" in actions else None
