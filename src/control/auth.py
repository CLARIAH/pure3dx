from itertools import chain
from .generic import AttrDict
from .users import Users


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
        Settings: AttrDict
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

    def authorise(self, table, record, nameSpace=None, action=None, insertTable=None):
        """Check whether an action is allowed on data.

        The "create" action is a bit special, because we do not have any record
        to start with. In this case `table` and `record` should point to the
        master record, and `insertTable` should have the table that will
        contain the new record.

        If the action is anything else, `table` and `record` refer to
        the relevant record, and `insertTable` should not be passed.

        How do the authorisation rules work?

        First we consider the site-wise role of the user: guest, user, admin, or root.
        If the action is allowed on that basis, we return True.

        If not, we look whether the user has an additional role with regard
        to the record in question, or with any of its master records.

        If so, we apply the rules for those cases and see whether the action is
        permitted.

        Then we have the possibility that a record is in a certain state, e.g.
        projects may be visible or invisible, editions may be published or
        unpublished.

        For each of these states we have separate rules, so we inspect the
        states of the records and master records in order to select the
        appropriate rules.

        Parameters
        ----------
        table: string
            the relevant table; for `create` actions it is the master table
            of the table in which a record will be inserted.
        record: ObjectId | AttrDict
            The id of the record that is being accessed or the record itself;
            for `create` actions it is the master record to which a new record
            will be created as a detail.
        nameSpace: string, optional None
            Authorisation on fields may be nameSpace dependent (fields are organised
            in nameSpace). When you do authorisation for field access, pass the
            nameSpace here. If you do not pass a nameSpace, and the rules encountered
            are nameSpace dependent, nameSpace `''` is assumed.
        action: string, optional None
            The action for which permission is asked.
        insertTable: string
            Only relevant for "create" actions.
            The detail table in which the new record will be inserted.

        Returns
        -------
        boolean | dict
            If an action is passed: boolean whether action is allowed.

            If no action is passed: dict keyed by the allowed actions, the values
            are true.
            Actions with a falsy permission (False or the empty set) are not included
            in the dict.
            So, to test whether any action is allowed, it suffices to test whether
            `action in result`
        """
        Messages = self.Messages
        Content = self.Content
        isCreate = action == "create"

        if (
            insertTable is None
            and isCreate
            or insertTable is not None
            and action is not None
            and not isCreate
        ):
            Messages.error(
                msg="Programming error in calculating authorization",
                logmsg=(
                    f"Wrong call to Auth.authorise with action {action} "
                    f"and insertTable {insertTable}"
                ),
            )
            # this is a programming error
            return False if action is None else set()

        Settings = self.Settings
        Mongo = self.Mongo

        detailMaster = Content.detailMaster

        User = self.myDetails()
        user = User.user
        role = User.role

        # we select the authorisation rules for this table

        auth = Settings.auth
        authRules = auth.authRules
        tableRules = authRules.get(insertTable if isCreate else table, AttrDict())

        # we need the state of the record that we want to apply the action to
        # If the action is create, we have no record.
        # We then use an initial state, given in the data model.
        # For all other actions, we read the state from the record,
        # its field is given in the data model.
        # If there is no state info, we assume there is no state.

        stateInfo = tableRules.state

        state = None

        (recordId, record) = Mongo.get(table, record)

        if recordId is None:
            return {} if action is None else False

        if stateInfo is not None:
            initState = stateInfo.init
            if isCreate:
                state = initState
            else:
                stateField = stateInfo.field
                state = record.get(stateField, None)
                if state is None:
                    state = initState

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
        userCoupled = set(auth.userCoupled)

        # for each of the roles we have to determine whether the role is
        # * site wide (table = site)
        # * associated with a master table
        # * associated with a detail table

        # First we get the tables associated with each role

        allAllowedRoles = {
            role: tableFromRole[role]
            for role in set(
                chain.from_iterable(v.keys() for v in rules.values() if v is not None)
            )
        }

        # Then we determine which of these tables are master, detail, or none of
        # those, with respect to the table we are acting upon.
        # Note that in case of "create" the table we act upon is a detail of
        # what we passed as "table"

        allRelatedTables = (
            {
                relatedTable: (
                    "self"
                    if relatedTable == insertTable
                    else (
                        "detail"
                        if detailMaster[relatedTable] == insertTable
                        else (
                            "master"
                            if detailMaster[insertTable] == relatedTable
                            else ""
                        )
                    )
                )
                for relatedTable in allAllowedRoles.values()
            }
            if isCreate
            else {
                relatedTable: (
                    "self"
                    if relatedTable == table
                    else (
                        "detail"
                        if detailMaster[relatedTable] == table
                        else "master" if detailMaster[table] == relatedTable else ""
                    )
                )
                for relatedTable in allAllowedRoles.values()
            }
        )

        # for each of the relatedTables we compute whether it leads to extra roles
        # for the current user.
        # We look for related records in those tables to which the user is related.

        userRoles = {role}

        for relatedTable, kind in allRelatedTables.items():
            if kind == "":
                continue

            if relatedTable not in userCoupled:
                continue

            relatedIdField = f"{relatedTable}Id"
            relatedCrossTable = f"{relatedTable}User"

            if kind == "self":
                if isCreate:
                    continue

                crossRecord = Mongo.getRecord(
                    relatedCrossTable,
                    {"user": user, relatedIdField: recordId},
                    warn=False,
                )
                extraRole = crossRecord.role

                if extraRole is not None:
                    userRoles.add(extraRole)

            elif kind == "master":
                # if the action is create the given record is the master
                # else we find the masterId in the given record

                if isCreate:
                    masterId = recordId
                else:
                    masterId = record[relatedIdField]

                # we do not need the master record itself,
                # instead we are interested in the coupling record
                # of the relatedTable with the user table
                # because we find a user role there

                crossRecord = Mongo.getRecord(
                    relatedCrossTable,
                    {"user": user, relatedIdField: masterId},
                    warn=False,
                )
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
                detailRecords = Mongo.getList(relatedTable, {idField: recordId})
                detailIds = [detailRecord._id for detailRecord in detailRecords]

                # we need the cross records between these detail records and
                # the user table, and we read the extra roles from those
                # records

                crossRecords = Mongo.getList(
                    relatedCrossTable,
                    {"user": user, relatedIdField: {"$in": detailIds}},
                )

                for crossRecord in crossRecords:
                    extraRole = crossRecord.role
                    if extraRole is not None:
                        userRoles.add(extraRole)

        # Now we have
        # 1. userRoles:
        #    the set of roles that this user has mbt to the given record
        #    and all of its relevant master and detail records
        # 2. rules
        #    a dictionary mapping each possible action to the
        #    roles a user needs to have to perform that action
        #    The roles itself are given as a dict, keyed by the role
        #    and valued by a boolean or a set, depending on the action.
        #    If it is a set (in fact, a list), it is a list of nameSpace,
        #    and the nameSpace parameter that has been passed to this function
        #    will be used.

        # We compute the allowed actions resulting in a dict keyed by the action
        # and valued by a boolean.

        allowedActions = {}

        for act, requiredRoles in rules.items():
            if requiredRoles is None:
                continue

            permission = False

            for presentRole in userRoles:
                permValue = requiredRoles.get(presentRole, False)

                if type(permValue) is not bool:
                    if nameSpace is None:
                        permValue = "" in permValue
                    else:
                        permValue = nameSpace in permValue

                if permValue:
                    permission = True
                    break

            if permission:
                allowedActions[act] = True

        # Finally we return the result.
        #
        # If no action is given, we return the allowedActions straightaway.
        # Otherwise we lookup the given action in allowedActions, get the
        # associated value (or provide a falsy default), and return that.

        return allowedActions if action is None else allowedActions.get(action, False)

    def mayBackup(self, project=None):
        """Whether the current user is allowed to make backups.

        *   Backups are not allowed in production mode, bacause the system and not the
            users are responsible for backups.
        *   Site-wide backups are only allowed for power users.
        *   Project backups are only allowed for project organisers and (power users).

        Parameters
        ----------
        project: AttrDict | ObjectId | string, optional None
            If None, we deal with site-wide backup.
            Otherwise we get the backups of this project.

        Returns
        -------
        boolean
            whether the relevant backup/restore actions are allowed.
        """
        Settings = self.Settings
        runProd = Settings.runProd

        if runProd:
            return False

        User = self.myDetails()

        if User.role in {"admin", "root"}:
            return True

        if project is None:
            return False

        Mongo = self.Mongo
        (projectId, project) = Mongo.get("project", project)
        if projectId is None:
            return False

        user = User.user
        projectUser = Mongo.getRecord(
            "projectUser", dict(user=user, projectId=projectId), warn=False
        )
        return projectUser.role == "organiser"

    def makeSafe(self, table, record, action):
        """Changes an update action into a read action if needed.

        This function 'demotes' an "update: to a "read" if the
        "update" is not allowed.

        If "read" itself is not allowed, None is returned.

        If any other action than "update" or "read" is passed, None is returned.

        Parameters
        ----------
        table: string
            The table in which the record exists.
        record: ObjectId | AttrDict
            The id of the record or the record itself.
        action: string
            An intended action.

        Returns
        -------
        string | void
            The resulting safe action.
        """
        if action not in {"update", "read"}:
            return None

        actions = self.authorise(table, record)
        return action if action in actions else "read" if "read" in actions else None
