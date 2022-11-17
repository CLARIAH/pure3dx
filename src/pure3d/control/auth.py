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
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)
        self.Mongo = Mongo
        self.Content = Content

    def authorise(self, action, projectId=None, editionId=None):
        """Authorise the current user to access a piece of content.

        !!! note "Requests may come from different senders"
            When 3D viewers are active, they may fire their own requests to
            this app. These 3D viewers do not know about MongoDb ids, all they
            know are the names of files and directories.

        Parameters
        ----------
        action: string
            The kind of access: `view`, `edit`, etc.
        projectId: ObjectId
            The project that is being accessed, if any.
        editionId: ObjectId
            The edition that is being accessed, if any.

        Returns
        -------
        boolean
            Whether the current user is authorised.
        """
        Settings = self.Settings
        Mongo = self.Mongo

        User = self.whoami()

        if projectId is None and editionId is not None:
            projectId = Mongo.getRecord("editions", _id=editionId).projectId

        projectRole = (
            None
            if projectId is None or User._id is None
            else Mongo.getRecord(
                "projectUsers", warn=False, projectId=projectId, userId=User._id
            ).role
        )
        projectPub = (
            None
            if projectId is None
            else "published"
            if Mongo.getRecord("projects", _id=projectId).isPublished
            else "unpublished"
        )

        projectRules = Settings.auth.projectRules[projectPub]
        condition = (
            projectRules[User.role] if User.role in projectRules else projectRules[None]
        ).get(action, False)
        permission = condition if type(condition) is bool else projectRole in condition
        return permission

    def isModifiable(self, projectId, editionId):
        """Whether the current user may modify content.

        The content may be outside any project
        (both `projectId` and `editionId` are None),
        within a project but outside any edition (`editionId` is None),
        or within an edition (`editionId` is not None).

        Parameters
        ----------
        projectId: ObjectId or None
            MongoDB id of the project in question.
        editionId: ObjectId or None
            MongoDB id of the edition in question.
        """
        return self.authorise("edit", projectId=projectId, editionId=editionId)

    def checkModifiable(self, projectId, editionId, action):
        """Like `isModifiable()`, but returns an allowed action.

        This function "demotes" an action to an allowed action if the
        action itself is not allowed.

        Parameters
        ----------
        action: string
            An intended action.

        Returns
        -------
        string
            If the action is a modifying action, but the content is not modifiable,
            it returns `view`.
            Otherwise it returns the action itself.
        """
        if action is None:
            return "view"

        if action != "view":
            if not self.isModifiable(projectId, editionId):
                action = "view"
        return action
