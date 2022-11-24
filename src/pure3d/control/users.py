from control.generic import AttrDict
from control.flask import (
    arg,
    sessionPop,
    sessionGet,
    sessionSet,
    getReferrer,
    redirectStatus,
)


USERIDFIELD = "user"

PROVIDER_ATTS = tuple(
    """
    sub
    email
    nickname
""".strip().split()
)


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

        Otherwise, it has member `sub`, the sub of the current user.
        It may also have additional members, such as `name` and `role`.
        """

        self.oidc = None
        """The object that gives access to authentication methods.
        """

    def addAuthenticator(self, oidc):
        """Adds the object that gives access to authentication methods.

        Parameters
        ----------
        oidc: object
            The object corresponding to the flask app prepared with the
            Flask-OIDC authenticator.

        Returns
        -------
        void
            The object is stored in the `oidc` member.
        """
        self.oidc = oidc

    def login(self):
        """Log in a user.

        Logging in has several main steps:

        1. redirecting to a private page, for which login is required
        2. obtaining the authentication results when the user visits that page
        3. storing the relevant user data

        When we log in test users, we can skip the first step, because
        we already know everything about the test user on the basis of the
        information in the request that brought us here.

        So, we find out if we have to log in a test user or a user that must be
        authenticated through oidc.

        We only log in a test user if we are in test mode and the user's sub
        is passed in the request.

        Returns
        -------
        response
            A redirect. When logging in in test mode, the redirect
            is to *referrer* (the url we came from). Otherwise it is to a url
            that triggers an oidc login procedure. To that page we pass
            the referrer as part of the url, so that after login the user
            can be redirected to the original referrer.
        """
        Messages = self.Messages
        Settings = self.Settings
        testMode = Settings.testMode

        referrer = getReferrer()
        (testMode, isTestUser, user) = self.getUser(fromArg=True)
        name = self.__User.nickname

        if user and not isTestUser and testMode:
            Messages.warning(
                logmsg=(
                    "LOGIN attempt while an user is already logged in: "
                    f"user {name} {user}"
                ),
                msg=f"first log out as user {name}",
            )
            return redirectStatus(f"/{referrer}", False)

        return (
            self.__loginTest(referrer, arg(USERIDFIELD))
            if isTestUser
            else self.__loginOidc(referrer)
        )

    def afterLogin(self, referrer):
        """Logs in a user.

        When this function starts operating, the user has been through the login
        process provided by the authentication service.

        We can now find the user's sub and additional attributes in the request
        context.

        We use that information to lookup the user in the MongoDb users table.
        If the user does not exists, we add a new user record, with this sub and
        these attributes, and role `user`.

        If the user does exists, we check whether we have to update his attributes.
        If the attributes found in MongoDb differ from those supplied by the
        authentication service, we update the MongoDb values on the basis
        of the provider values.

        Parameters
        ----------
        referrer: string
            url where we came from.

        Returns
        -------
        response
            A redirect to the referrer, with a status 302 if the log in was
            successful or 303 if not.
        """
        Messages = self.Messages
        oidc = self.oidc

        user = None

        if oidc.user_loggedin:
            user = oidc.user_getfield("sub")
            name = oidc.user_getfield("nickname")

        if user is None or not self.__findUser(user, update=True):
            Messages.warning(
                logmsg="LOGIN failed for user {user}",
                msg="failed to log in",
            )
            return redirectStatus(f"/{referrer}", False)

        name = self.__User.nickname
        Messages.plain(
            logmsg=f"LOGIN successful: user {name} {user}",
            msg=f"LOGIN successful: user {name}",
        )
        return redirectStatus(f"{referrer}", True)

    def logout(self):
        """Logs off the current user.

        First we find out whether we have to log out a test user or a normal
        user.
        After logging out, we redirect to the home page.

        Returns
        -------
        response
            A redirect to the home page.
        """
        oidc = self.oidc
        Messages = self.Messages
        name = self.__User.nickname

        (testMode, isTestUser, user) = self.getUser()

        if user is None:
            if testMode:
                sessionPop(USERIDFIELD)
            else:
                oidc.logout()
            self.__User.clear()
            Messages.plain(logmsg="LOGOUT but no user was logged in.")
            return redirectStatus("/", False)

        if isTestUser:
            sessionPop(USERIDFIELD)
        else:
            oidc.logout()

        self.__User.clear()
        Messages.plain(
            logmsg=f"LOGOUT successful: user {name} {user}",
            msg=f"{name} logged out",
        )
        return redirectStatus("/", True)

    def identify(self):
        """Make sure who is the current user.

        Checks whether there is a current user and whether that user is fully known,
        i.e. in the users collection of the mongoDb.

        If there is a current user that is unknown to the database, the current user
        will be cleared.

        Otherwise, we make sure that we retrieve the current user's attributes from
        the database.

        !!! note "No login"
            We do not try to perform a login of a user,
            we only check who is the currently logged in user.

            A login must be explicitly triggered by the the `/login` url.
        """
        oidc = self.oidc

        (testMode, isTestUser, user) = self.getUser()

        if user is not None:
            if isTestUser:
                if not self.__findTestUser(user):
                    self.__User.clear()
                    sessionPop(USERIDFIELD)
            else:
                if not self.__findUser(user, update=False):
                    self.__User.clear()
                    oidc.logout()

    def myDetails(self):
        """Who is the currently authenticated user?

        The `__User` member is inspected: does it contain an sub?
        If so, that is taken as proof that we have a valid user.

        Returns
        -------
        dict
            Otherwise a copy of the complete __User record is returned.
            unless there is no `sub` member in the current user, then
            the empty dictionary is returned.
        """
        User = self.__User
        return AttrDict(**User) if "sub" in User else AttrDict({})

    def getUser(self, fromArg=False):
        """Obtain the sub of the currently logged in user from the request info.

        It works for test users and normal users.

        Parameters
        ----------
        fromArg: boolean, optional False
            If True, the test user is not read from the session, but from a
            request argument.
            This is used during the login procedure of test users.

        Returns
        -------
        boolean, boolean, string
            Whether we are in test mode.
            Whether the user is a test user.
            The sub of the user
        """
        oidc = self.oidc
        Settings = self.Settings
        testMode = Settings.testMode

        user = None
        isTestUser = None

        if testMode:
            user = arg(USERIDFIELD) if fromArg else sessionGet(USERIDFIELD)
            if user:
                isTestUser = True

        if user is None:
            user = oidc.user_getfield("sub") if oidc.user_loggedin else None
            if user:
                isTestUser = False

        return (testMode, isTestUser, user)

    def wrapLogin(self):
        """Generate HTML for the login widget.

        De task is to generate login/logout buttons.

        If the user is logged in, his nickname should be displayed, together
        with a logout button.

        If no user is logged in, a login button should be displayed.

        If in test mode, a list of buttons for each test-user should be
        displayed.

        Returns
        -------
        string
            HTML of the list of buttons for test users, with the button
            for the current user styled as active.
        """
        Mongo = self.Mongo

        (testMode, isTestUser, userActive) = self.getUser()

        html = []

        def wrap(label, text, title, href, active, enabled):
            labelRep = f"""<span class="label">{label}</span>""" if label else ""
            cls = "active" if active else ""
            elem = "span" if active else "a"
            hrefAtt = "" if active else f'href="{href}"'
            if not enabled:
                cls = "disabled"
                elem = "span"
                hrefAtt = ""
            html.append(
                f"{labelRep}"
                f'<{elem} title="{title}" {hrefAtt} class="button small {cls}">'
                f"{text}</{elem}>"
            )

        if testMode:
            # row of test users

            enabled = not userActive or isTestUser
            for record in sorted(
                Mongo.getList("users", isTest=True),
                key=lambda r: r.nickname,
            ):
                user = record.sub
                name = record.nickname
                role = self.presentRole(record.role)

                active = user == userActive
                wrap(None, name, role, f"/login?user={user}", active, enabled)

        if userActive:
            # details of logged in user

            details = self.myDetails()
            name = details.nickname
            email = details.email
            userRep = f"{name} - {email}" if email else name
            role = self.presentRole(details.role)
            wrap("Logged in as", userRep, role, None, True, True)

            # logout button
            wrap(None, "log out", f"log out {name}", "/logout", False, True)

        else:
            # login button
            wrap(None, "log in", "log in", "/login", False, True)

        return "\n".join(html)

    def presentRole(self, role):
        """Finds the interface representation of a role.

        Parameters
        ----------
        role: string
            The internal name of the role.

        Returns
        -------
        string
            The name of the role as it should be presented to users.
            If no representation can be found, the internal name is returned.
        """
        Settings = self.Settings
        roles = Settings.auth.roles
        return roles.get(role, role)

    def __loginTest(self, referrer, user):
        """Perform the steps to log in a test user.

        This involves looking up the user in the user table,
        copying its information in the `__User` member of this object,
        and storing the user in the session. After that the user is redirected
        to where he came from.

        Parameters
        ----------
        referrer: string
            url where we came from.
        user: string
            The sub of the test user that we must log in as.

        Returns
        -------
        response
            A redirect to the referrer, with a status 302 if the log in was
            successful or 303 if not.
        """
        Messages = self.Messages

        if user is None or not self.__findTestUser(user):
            return redirectStatus(f"/{referrer}", False)

        sessionSet(USERIDFIELD, user)
        name = self.__User.nickname
        Messages.plain(
            logmsg=f"LOGIN successful: test user {name} {user}",
            msg=f"LOGIN successful: test user {name}",
        )
        return redirectStatus(f"/{referrer}", True)

    def __loginOidc(self, referrer):
        """Redirect step in logging in normal user.

        This means redirecting the user to a url for which authentication
        is required.

        Parameters
        ----------
        referrer: string
            url where we came from. We pass this to the private url.

        Returns
        -------
        response
            A redirect to the referrer, with a status 302 if the log in was
            successful or 303 if not.
        """
        return redirectStatus(f"/afterlogin/referrer/{referrer}", True)

    def __findTestUser(self, user):
        Messages = self.Messages
        Mongo = self.Mongo
        User = self.__User

        record = Mongo.getRecord("users", sub=user)

        if not record:
            Messages.warning(msg="Unknown user", logmsg=f"Unknown user {user}")
            return False

        User.clear()
        for att in PROVIDER_ATTS:
            User[att] = record[att]
        User.role = record.role

        return True

    def __findUser(self, user, update=False):
        """Lookup user data in the MongoDb users collection.

        The user is looked up by the `sub` field.
        Optionally, the user record in MongoDb is updated with attributes from
        the identity provider.

        Parameters
        ----------
        user: string
            The `sub` of by which a user is looked up, if not None.
        update: boolean, optional False

        Returns
        -------
        boolean
            Whether a user has been found/created.
            If so, the data of that user record is stored
            in the `__User` member.
        """
        Mongo = self.Mongo
        oidc = self.oidc
        User = self.__User

        record = Mongo.getRecord("users", sub=user, warn=False)
        newUser = None

        if not record:
            newUser = {att: oidc.user_getfield(att) for att in PROVIDER_ATTS}
            userId = Mongo.insertRecord("users", role="user", **newUser)
            record = Mongo.getRecord("users", _id=userId)

        User.clear()
        for att in PROVIDER_ATTS:
            User[att] = record[att]
        User.role = record.role

        if update and not newUser:
            changes = {}
            for att in PROVIDER_ATTS:
                orig = User[att]
                new = oidc.user_getfield(att)
                if new is not None and orig != new:
                    changes[att] = new
                    User[att] = new
            if changes:
                Mongo.updateRecord("users", changes, sub=User.sub)
        return True
