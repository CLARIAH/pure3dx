from flask import request, session

from control.mongo import castObjectId
from control.helpers.generic import AttrDict


class Auth:
    def __init__(self, config, Messages, Mongo, Users, Content):
        """All about authorised data access.

        This class knows users and content,
        and decides whether the current user is authorised to perform certain
        actions on content in question.

        It is instantiated by a singleton object.

        Parameters
        ----------
        config: AttrDict
            App-wide configuration data obtained from
            `control.config.Config.config`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        Mongo: object
            Singleton instance of `control.mongo.Mongo`.
        Users: object
            Singleton instance of `control.users.Users`.
        Content: object
            Singleton instance of `control.content.Content`.
        """
        self.config = config
        self.Messages = Messages
        Messages.debugAdd(self)
        self.Mongo = Mongo
        self.Users = Users
        self.Content = Content
        self.user = AttrDict()

    def clearUser(self):
        user = self.user
        user.clear()

    def getUser(self, userId):
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
        config = self.config
        Messages = self.Messages
        self.clearUser()
        if config.testMode:
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
        user = self.user
        return "_id" in user

    def deauthenticate(self):
        Messages = self.Messages
        userId = session.get("userid", None)
        if userId:
            self.clearUser()
            Messages.plain(msg="logged out", logmsg=f"LOGOUT successful: user {userId}")
        else:
            Messages.warning(msg="You were not logged in")

        session.pop("userid", None)

    def authorise(self, action, project=None, edition=None, byName=False):
        config = self.config
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

        if projectId is None:
            projectId = Mongo.getRecord("editions", _id=editionId).projectId

        projectRole = (
            None
            if user._id is None
            else Mongo.getRecord(
                "projectUsers", projectId=projectId, userId=castObjectId(user._id)
            ).role
        )
        projectPub = (
            "published"
            if Mongo.getRecord("projects", _id=projectId).isPublished
            else "unpublished"
        )

        projectRules = config.auth.projectRules[projectPub]
        condition = (
            projectRules[user.role] if user.role in projectRules else projectRules[None]
        ).get(action, False)
        permission = condition if type(condition) is bool else projectRole in condition
        return permission

    def isModifiable(self, projectId, editionId):
        return self.authorise("edit", project=projectId, edition=editionId)

    def checkModifiable(self, projectId, editionId, action):
        if action != "view":
            if not self.isModifiable(projectId, editionId):
                action = "view"
        return action
