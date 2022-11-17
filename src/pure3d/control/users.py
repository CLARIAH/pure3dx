from control.generic import AttrDict
from control.flask import arg, sessionPop, sessionGet, sessionSet


class Users:
    def __init__(self, Settings, Messages, Mongo):
        """All about users and the current user.

        This class has methods to login/logout a user,
        to retrieve the data of the currently logged in user,
        and to query the users table in MongoDb.

        It is instantiated by a singleton object.

        This object has a member `__User` that contains the data of the current
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
        """
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)
        self.Mongo = Mongo
        self.__User = AttrDict()
        """Data of the current user.

        If there is no current user, it has no members.

        Otherwise, it has member `_id`, the mongodb id of the current user.
        It may also have additional members, such as `name` and `role`.
        """

    def wrapTestUsers(self, userActive):
        """Generate HTML for login buttons for test users.

        Only produces a non-empty result if the app is in test mode.

        Parameters
        ----------
        userActive: ObjectId
            The id of the user that is currently logged in.
            The button for this users will be rendered as the active one.

        Returns
        -------
        string
            HTML of the list of buttons for test users, with the button
            for the current user styled as active.
        """
        Settings = self.Settings
        Mongo = self.Mongo

        if not Settings.testMode:
            return ""

        def wrap(title, href, cls, text):
            return (
                f'<a title="{title}" href="{href}" class="button small {cls}">'
                f"{text}</a>"
            )

        active = "active" if userActive is None else ""

        html = []
        html.append(wrap("if not logged in", "/logout", active, "logged out"))

        for user in sorted(Mongo.execute("users", "find"), key=lambda r: r["name"]):
            user = AttrDict(user)

            active = "active" if user._id == userActive else ""
            html.append(wrap(user.role, f"/login?userid={user._id}", active, user.name))

        return "\n".join(html)

    def login(self):
        """Logs in a user.

        The fact that a user has changed is triggered by the `/login` url,
        the new user id is expected in the session.

        In test mode, the new userid may also be present as a request argument.

        It is possible that we find a user id for which there is no corresponding
        entry in the users table in MongoDb.

        Then we remove the user id from the session, and we do not log in any user.
        """
        Messages = self.Messages

        userId = self.__recallUser()

        if self.__retrieveUserAttributes(userId):
            self.__rememberUser(userId)
            userName = self.__User.name
            Messages.plain(
                logmsg=f"LOGIN successful: user {userName} {userId}",
                msg=f"LOGIN successful: user {userName}",
            )
            return True
        else:
            Messages.warning(
                logmsg=f"LOGIN: user {userId} does not exist",
                msg="LOGIN: user does not exist",
            )
            self.__forgetUser()
            self.__clearUserAttributes()
            return False

    def logout(self):
        """Logs off the current user.

        That means that the `__User` member of Auth is cleared, and the current
        session is popped.
        """
        Messages = self.Messages

        userId = self.__recallUser()
        userName = self.__User.name

        if userId is None:
            Messages.warning(
                logmsg=f"LOGOUT when no user was logged in: user {userName} {userId}",
                msg="You were not logged in",
            )
        else:
            Messages.plain(
                logmsg=f"LOGOUT successful: user {userName} {userId}",
                msg=f"{userName} logged out",
            )
        self.__clearUserAttributes()
        self.__forgetUser()

    def identify(self):
        """Make sure who is the current user.

        Checks whether there is a current user and whether that user is fully known,
        i.e. in the users collection of the mongoDb.

        If there is a current user that is unknown to the database, the current user
        will be cleared.
        """
        userId = self.__recallUser()

        if userId is None or not self.__retrieveUserAttributes(userId):
            self.__clearUserAttributes()
            self.__forgetUser()

    def whoami(self):
        """Who is the currently authenticated user?

        The `__User` member is inspected: does it contain an id?
        If so, that is taken as proof that we have a valid user.

        Returns
        -------
        boolean or dict
            If there is on `_id` member in the current user, False is returned.
            Otherwise a copy of the complete __User record is returned.
        """
        User = self.__User
        return AttrDict(**User) if "_id" in User else AttrDict({})

    def __rememberUser(self, userId):
        """Stores the user id in the current session.

        Parameters
        ----------
        userId: ObjectId
            The user id to remember.
            It will be stored as string.
        """

        try:
            sessionSet("userid", str(userId))
        except Exception:
            pass

    def __forgetUser(self):
        """Removes the current user id from the current session."""

        try:
            sessionPop("userid")
        except Exception:
            pass

    def __recallUser(self):
        """Retrieves the current user id from the current session.

        Returns
        -------
        ObjectId or None
            The user id stored in the current session in MongoDb format,
            if there is a user id, else None.
        """
        Settings = self.Settings
        Mongo = self.Mongo

        testMode = Settings.testMode

        try:
            sessionUserId = sessionGet("userid")
        except Exception:
            sessionUserId = None

        if testMode:
            try:
                testUserId = arg("userid")
            except Exception:
                testUserId = None

            userId = testUserId if testUserId is not None else sessionUserId
            self.debug(f"RECALL {sessionUserId=} {testUserId=} {userId=}")
        else:
            userId = sessionUserId

        return Mongo.cast(userId)

    def __clearUserAttributes(self):
        """Clear current user.

        The `__User` member is cleared.
        Note that it is not deleted, only its members are removed.
        """
        self.__User.clear()

    def __retrieveUserAttributes(self, userId):
        """Get user data.

        Parameters
        ----------
        userId: ObjectId
            The id of a user in the users table of the MongoDb database.

        Returns
        -------
        boolean
            Whether a user with id = `userId` has been found.
            If so, the data of that user record is stored
            in the `__User` member.
        """
        Messages = self.Messages
        Mongo = self.Mongo
        User = self.__User

        record = Mongo.getRecord("users", _id=userId)
        if record:
            User.clear()
            User._id = userId
            User.name = record.name
            User.role = record.role
            return True

        Messages.warning(msg="Unknown user", logmsg=f"Unknown user {userId}")
        return False
