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
        Settings: `control.helpers.generic.AttrDict`
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

    def authorise(
        self, table, recordId=None, projectId=None, action=None
    ):
        """Gather the access conditions for the relevant record or table.

        Parameters
        ----------
        table: string, optional None
            the table that is being used
        recordId: ObjectId
            The id of the record that is being accessed, if any.
        projectId: ObjectId
            Only relevant if recordId is None.
            If passed, the new record to be created will belong to this project
        action: string, optional None
            If None, returns all permitted actions on the record in question,
            otherwise whether the indicated action is permitted.
            If recordId is None, it is assumed that the action is `create`,
            and a boolean is returned.

        Returns
        -------
        set | boolean
            If `recordId` is None: whether the user is allowed to insert a new
            record in `table`.
            Otherwise: if `action` is passed: whether the user is allowed to
            perform that action on the record in question.
            Otherwise: the set of actions that the user may perform on this record.
        """
        Settings = self.Settings
        Mongo = self.Mongo

        User = self.myDetails()
        user = User.sub
        role = User.role

        if recordId is not None:
            record = Mongo.getRecord(table, _id=recordId)
            projectId = record._id if table == "projects" else record.projectId
        else:
            tableRules = Settings.auth.createRules.get(table, set())

        if projectId is not None:
            # we are inside a project
            projectPub = (
                True
                if Mongo.getRecord("projects", _id=projectId).isPublished
                else False
            )
            projectRole = (
                None
                if user is None
                else Mongo.getRecord(
                    "projectUsers", warn=False, projectId=projectId, user=user
                ).role
            )
            actualRole = projectRole or role
            if recordId is not None:
                # we are dealing with an existing record
                actions = Settings.auth.projectRules[projectPub].get(actualRole, [])
                permission = actions if action is None else action in actions
            else:
                # we wonder whether we may insert a record
                permission = actualRole in tableRules
        else:
            # we are outside any project
            if recordId is not None:
                # we are dealing with an existing record
                actions = Settings.auth.recordRules.get(table, {}).get(role, [])
                permission = actions if action is None else action in actions
            else:
                # we wonder whether we may insert a record
                permission = role in tableRules
        return permission

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
