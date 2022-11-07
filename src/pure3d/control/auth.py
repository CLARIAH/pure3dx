from flask import request, session

from control.mongo import castObjectId
from control.helpers.generic import AttrDict


class Auth:
    def __init__(self, Settings, Messages, Mongo, Users, Content):
        """All about authorised data access.

        This class knows users and content,
        and decides whether the current user is authorised to perform certain
        actions on content in question.

        It is instantiated by a singleton object.
        This object has a member `user` that contains the data of the current
        user if there is a current user.

        Parameters
        ----------
        Settings: `control.helpers.generic.AttrDict`
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        Mongo: object
            Singleton instance of `control.mongo.Mongo`.
        Users: object
            Singleton instance of `control.users.Users`.
        Content: object
            Singleton instance of `control.content.Content`.
        """
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)
        self.Mongo = Mongo
        self.Users = Users
        self.Content = Content
        self.user = AttrDict()
        """Data of the current user.

        If there is no current user, it is has no members.

        Otherwise, it has member `_id`, the mongodb id of the current user.
        It may also have additional members, such as `name` and `role`.
        """

    def clearUser(self):
        """Clear current user.

        The `user` member of Auth is cleard.
        Note that it is not deleted, only its members are removed.
        """
        user = self.user
        user.clear()

    def getUser(self, userId):
        """Get user data.

        Parameters
        ----------
        userId: ObjectId
            The id of a user in the users table of the MongoDb database.

        Returns
        -------
        boolean
            Whether a user with that id has been found.
            The data of the user record that has been found is stored
            in the `user` member of Auth.
        """
        Messages = self.Messages
        Mongo = self.Mongo
        user = self.user

        user.clear()
        record = Mongo.getRecord("users", _id=castObjectId(userId))
        if record:
            user._id = userId
            user.name = record.name
            user.role = record.role
            result = True
        else:
            Messages.warning(msg="Unknown user", logmsg=f"Unknown user {userId}")
            result = False
        return result

    def checkLogin(self):
        """Get user data.

        Retrieves a user id from the current session, looks up the corresponding
        user, and fills the `user` member of Auth accordingly.

        In test mode, the user id is obtained from the query string.
        There is a list of test user buttons on the interface, and they
        all pass a user id in the querystring of their `href` attribute.

        In production mode, the current session will be inspected for data
        that corresponds with the logged in user.

        Returns
        -------
        boolean
            Whether a user with a valid id has been found in the current session.
        """
        Settings = self.Settings
        Messages = self.Messages
        self.clearUser()
        if Settings.testMode:
            userId = request.args.get("userid", None)
            result = self.getUser(userId)
            userName = self.user.name
            if result:
                Messages.plain(msg=f"LOGIN successful: user {userName}")
            else:
                Messages.warning(msg=f"LOGIN: user {userId} does not exist")
            return result

        Messages.warning(msg="User management is only available in test mode")
        return False

    def authenticate(self, login=False):
        """Authenticates the current user.

        Checks whether there is a current user and whether that user is fully known,
        i.e. in the users collection of the mongoDb.

        If there is a current user unknown in the database, the current user
        will be cleared.

        Parameters
        ----------
        login: boolean, optional False
            Use True to deal with a user that has just logged in.
            It will retrieve the corresponding user data from MongoDb
            and populate the `user` member of Auth.

        Returns
        -------
        boolean
            Whether the current user is authenticated.
        """
        user = self.user

        if login:
            session.pop("userid", None)
            if self.checkLogin():
                session["userid"] = user._id
                return True
            return False

        userId = session.get("userid", None)
        if userId:
            if not self.getUser(userId):
                self.clearUser()
                return False
            return True

        self.clearUser()
        return False

    def authenticated(self):
        """Cheap check whether there is a current authenticated user.

        The `user` member of Auth is inspected: does it contain an id?
        If so, that is taken as proof that we have a valid user.

        !!! hint "auhtenticate versus authenticated"
            We try to enforce at all times that if there is data in the
            `user` member of Auth, it is the correct data of an authenticated
            user.
            But there may arise edge cases,
            e.g. when a user is successfully authenticated,
            but then removed from the database by an admin.

            Good practice is: in every request that needs an authenticated user:

            * call `Auth.authenticate()` the first time
            * call `authenticated` after that.

            With this practice, we can shield a lot of code with the
            cheaper `Auth.authenticated()` function.
        """
        user = self.user
        return "_id" in user

    def deauthenticate(self):
        """Logs off the current user.

        That means that the `user` memebr of Auth is cleared, and the current
        session is popped.
        """
        Messages = self.Messages
        userId = session.get("userid", None)
        if userId:
            self.clearUser()
            Messages.plain(msg="logged out", logmsg=f"LOGOUT successful: user {userId}")
        else:
            Messages.warning(msg="You were not logged in")

        session.pop("userid", None)

    def authorise(self, action, project=None, edition=None, byName=False):
        """Authorise the current user to access a piece of content.

        !!! note "Requests may come from different senders"
            When 3D viewers are active, they may fire their own requests to
            this app. These 3D viewers do not know about MongoDb ids, all they
            know are the names of files and directories.

        Parameters
        ----------
        action: string
            The kind of access: `view`, `edit`, etc.
        project: string or ObjectId
            The project that is being accessed, if any.
        edition: string or ObjectId
            The edition that is being accessed, if any.
        byName: boolean, optional False
            Whether the project and edition parameters contain an ObjectId.
            If not, it is assumed they contain a name.
            Sometimes we know projects and editions by their id, especially
            when we have retrieved them from MongoDb.
            But some routes access projects and editions on the file system,
            and then we have only their names.
            This happens in case the 3D viewers access the file system directly.

        Returns
        -------
        boolean
            Whether the current user is authorised.
        """
        Settings = self.Settings
        Mongo = self.Mongo

        user = self.user

        if project:
            projectId = (
                Mongo.getRecord("projects", name=project)._id
                if byName
                else project or None
            )
        else:
            projectId = None

        if edition:
            editionId = (
                Mongo.getRecord("editions", name=edition)._id
                if byName
                else edition or None
            )
        else:
            editionId = None

        if projectId is None and editionId is not None:
            projectId = Mongo.getRecord("editions", _id=editionId).projectId

        projectRole = (
            None
            if projectId is None or user._id is None
            else Mongo.getRecord(
                "projectUsers",
                warn=False,
                projectId=projectId,
                userId=castObjectId(user._id),
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
            projectRules[user.role] if user.role in projectRules else projectRules[None]
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
        return self.authorise("edit", project=projectId, edition=editionId)

    def checkModifiable(self, projectId, editionId, action):
        """Like `Auth.isModifiable()`, but returns an allowed action.

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
        if action != "view":
            if not self.isModifiable(projectId, editionId):
                action = "view"
        return action
