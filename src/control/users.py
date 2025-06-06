from .generic import AttrDict
from .flask import (
    acg,
    requestArg,
    sessionPop,
    sessionGet,
    sessionSet,
    getReferrer,
    redirectStatus,
)


PROVIDER_ATTS = {
    x: x
    for x in """
    sub
    email
    nickname
""".strip().split()
}
PROVIDER_ATTS["sub"] = "user"


class Users:
    def __init__(self, Settings, Messages, Mongo):
        """All about users and the current user.

        This class has methods to login/logout a user,
        to retrieve the data of the currently logged in user,
        and to query the users table in MongoDb.

        It is instantiated by a singleton object.

        !!! note "User details are not stored here"
            The user details are not stored as members of this object, since
            this object has been made before the flask app was initialized,
            hence the object is global in the sefver process, meaning that all
            workers can see its data.

            Instead, the user details are stored in a so-called *global* in an
            [Application Context](https://flask.palletsprojects.com/en/2.2.x/appcontext/),
            where it is visible and modifiable by the current request only.

        Parameters
        ----------
        Settings: AttrDict
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

        self.oidc = None
        """The object that gives access to authentication methods.
        """

    @staticmethod
    def initUser():
        """Initialize the storage that keeps the details of the currently
        logged-in user.

        It will put an empty AttrDict as *global* in the current application context.

        As long as there is no current user, this AttrDict will remain empty.
        If there is a current user, or a user logs in, it will get a member
        `user`, which is the *sub* as it comes from the OIDC authenticator or from
        a special login procedure.

        It may then also have additional members, such as `name` and `role`.
        """
        acg.User = AttrDict()

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

        When we log in special users, we can skip the first step, because
        we already know everything about the special user on the basis of the
        information in the request that brought us here.

        So, we find out if we have to log in a special user or a user that must be
        authenticated through oidc.

        We only log in a test/pilot user if we are in non-prod mode and the user's "sub"
        is passed in the request.

        Returns
        -------
        response
            A redirect. When logging in in non-prod mode, the redirect
            is to*referrer* (the url we came from). Otherwise it is to a url
            that triggers an oidc login procedure. To that page we pass
            the referrer as part of the url, so that after login the user
            can be redirected to the original referrer.
        """
        Messages = self.Messages
        Settings = self.Settings
        runProd = Settings.runProd

        referrer = getReferrer()
        (isSpecialUser, user) = self.getUser(fromArg=True)
        uName = acg.User.nickname  # this is the current user if any

        if user and not isSpecialUser and not runProd:
            Messages.warning(
                logmsg=(
                    "LOGIN attempt while an user is already logged in: "
                    f"user {uName} {user}"
                ),
                msg=f"first log out as user {uName}",
            )
            return redirectStatus(f"/{referrer}", False)

        return (
            self.__loginSpecial(referrer, requestArg("user"))
            if isSpecialUser
            else self.__loginOidc(referrer)
        )

    def afterLogin(self, referrer):
        """Logs in a user.

        When this function starts operating, the user has been through the login
        process provided by the authentication service.

        We can now find the user's "sub" and additional attributes in the request
        context.

        We use that information to lookup the user in the MongoDb users table.
        If the user does not exist, we add a new user record, with this "sub" and
        these attributes, and role `user`.

        If the user does exist, we check whether we have to update his attributes.
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
        referrer = referrer.removeprefix("/")

        if oidc.user_loggedin:
            user = oidc.user_getfield("sub")
            uName = oidc.user_getfield("nickname")

        if user is None or not self.__findUser(user, update=True):
            Messages.warning(
                logmsg=f"LOGIN failed for user {user}",
                msg="failed to log in",
            )
            return redirectStatus(f"/{referrer}", False)

        uName = acg.User.nickname
        Messages.plain(
            logmsg=f"LOGIN successful: user {uName} {user}",
            msg=f"LOGIN successful: user {uName}",
        )
        return redirectStatus(f"/{referrer}", True)

    def logout(self):
        """Logs off the current user.

        First we find out whether we have to log out a test/pilot user or a normal
        user.
        After logging out, we redirect to the home page.

        Returns
        -------
        response
            A redirect to the home page.
        """
        oidc = self.oidc
        Settings = self.Settings
        Messages = self.Messages
        uName = acg.User.nickname
        runProd = Settings.runProd

        (isSpecialUser, user) = self.getUser()

        if user is None:
            if not runProd:
                sessionPop("user")
            else:
                oidc.logout()
            acg.User.clear()
            Messages.plain(logmsg="LOGOUT but no user was logged in.")
            return redirectStatus("/", False)

        if isSpecialUser:
            sessionPop("user")
        else:
            oidc.logout()

        acg.User.clear()
        Messages.plain(
            logmsg=f"LOGOUT successful: user {uName} {user}",
            msg=f"{uName} logged out",
        )
        return redirectStatus("/", True)

    def identify(self):
        """Make sure who is the current user.

        Checks whether there is a current user and whether that user is fully known,
        i.e. in the users table of the mongoDb.

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

        (isSpecialUser, user) = self.getUser()

        if user is not None:
            if isSpecialUser:
                if not self.__findSpecialUser(user):
                    acg.User.clear()
                    sessionPop("user")
            else:
                if not self.__findUser(user, update=False):
                    acg.User.clear()
                    oidc.logout()

    def myDetails(self):
        """Who is the currently authenticated user?

        The application-context-global `User` is inspected:
        does it contain a member called `user`?
        If so, that is taken as proof that we have a valid user.

        Returns
        -------
        dict
            Otherwise a copy of the complete `User` record is returned.
            unless there is no `user` member in the current user, then
            the empty dictionary is returned.
        """
        User = acg.User
        return AttrDict(**User) if "user" in User else AttrDict({})

    def inPower(self):
        """Whether the current user is a power user: admin or root.

        Returns
        -------
        tuple
            The first member is a boolean:
            true if the current user is an admin or root, false if the current
            user is not logged in or neither an admin ir root.
            The second member is the role of the current user, None if there is
            no current user.
        """
        User = self.myDetails()
        user = User.user
        uName = User.nickname

        if not user or not uName:
            return (False, None)

        myRole = User.role
        return (myRole in {"root", "admin"}, myRole)

    def getUser(self, fromArg=False):
        """Obtain the "sub" of the currently logged in user from the request info.

        It works for test/pilot users and normal users.

        Parameters
        ----------
        fromArg: boolean, optional False
            If True, the test/pilot user is not read from the session, but from a
            request argument.
            This is used during the login procedure of test/pilot users.

        Returns
        -------
        boolean, string
            *   Whether the user is a test/pilot user or a normally authenticated user.
                None if there is no authenticated user.
            *   The "sub" of the user.
        """
        oidc = self.oidc
        Settings = self.Settings
        runProd = Settings.runProd

        user = None
        isSpecialUser = None

        if not runProd:
            user = requestArg("user") if fromArg else sessionGet("user")
            if user:
                isSpecialUser = True

        if user is None:
            user = oidc.user_getfield("sub") if oidc.user_loggedin else None
            if user:
                isSpecialUser = False

        return (isSpecialUser, user)

    def wrapLogin(self):
        """Generate HTML for the login widget.

        De task is to generate login/logout buttons.

        If the user is logged in, his nickname should be displayed, together
        with a logout button.

        If no user is logged in, a login button should be displayed.

        If in non-prod mode, a list of buttons for each test/pilot user should be
        displayed.

        Returns
        -------
        string
            HTML of the list of buttons for test/pilot users, with the button
            for the current user styled as active.
        """
        Settings = self.Settings
        H = Settings.H
        runProd = Settings.runProd
        Mongo = self.Mongo

        (isSpecialUser, userActive) = self.getUser()

        specialContent = []
        content = []

        def wrap(label, text, title, href, active, enabled):
            """Inner function to be called recursively."""
            if label:
                content.append(H.span(label, cls="label"))

            if active:
                cls = "active"
                elem = "span"
                href = []
            else:
                cls = ""
                elem = "a"
                href = [href]

            if not enabled:
                cls = "disabled"
                elem = "span"
                href = []

            fullCls = f"button small {cls}"

            return H.elem(elem, text, *href, cls=fullCls, title=title)

        if not runProd:
            # row of test/pilot users

            enabled = not userActive or isSpecialUser

            for record in sorted(
                Mongo.getList("user", dict(isSpecial=True), sort="nickname"),
                key=lambda r: r.nickname or "",
            ):
                user = record.user
                uName = record.nickname
                role = self.presentRole(record.role)

                active = user == userActive
                specialContent.append(
                    wrap(None, uName, role, f"/alogin?user={user}", active, enabled)
                )

        if userActive:
            # details of logged in user

            details = self.myDetails()
            uName = details.nickname
            email = details.email
            userRep = f"{uName} - {email}" if email else uName
            role = self.presentRole(details.role)
            content.append(wrap("Logged in as", userRep, role, None, True, True))

            # logout button
            content.append(
                wrap(None, "log out", f"log out {uName}", "/alogout", False, True)
            )

        else:
            # login button
            content.append(wrap(None, "log in", "log in", "/alogin", False, True))

        return (H.content(*specialContent), H.content(*content))

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

    def getInvolvedUsers(self, tableRecordRoles, asString=False):
        """Finds the users involved in a specific role with respect to something.

        By this method you can find the organisers of a project, the editors of
        an edition, the admins of the site, etc.

        Parameters
        ----------
        table: string
            Either `site`, `project` or `edition`.
            This indicates the kind of thing that the users are related to.
        tableRecordRoles: tuple
            The tuple consists of tuples `(table, record, role)`
            The users connected to that record in that table in that role
            should be added to the list.
            All roles are specified in the `yaml/authorise.yml` file.

        Returns
        -------
        tuple or string
            If `asString` is False, the result is a datastructure:

            *   whether the information can be disclosed to the current users
            *   the representation of that role on the interface.
            *   a tuple:

                Each item is a tuple, corresponding to a user.
                For each user there are the follwoing fields:

                *   user field in the user table
                *   full name
                *   table of the record to which the user is linked
                *   role in which the user is linked to that record

            If `asString` is True, this data structure will be wrapped in HTML.
        """
        Mongo = self.Mongo
        Settings = self.Settings
        H = Settings.H
        auth = Settings.auth

        involvedUsers = []

        for table, record, role in tableRecordRoles:
            roles = auth.roles[table]
            allowed = self.authorise(table, record, action="read")
            users = None

            if allowed and roles is not None and roles.get(role, None) is not None:
                userInfo = Mongo.getList("user", {}, sort="nickname", asDict="user")

                if table == "site":
                    relatedUsers = [
                        uInfo for uInfo in userInfo.values() if uInfo.role == role
                    ]
                else:
                    criteria = {f"{table}Id": record._id, "role": role}
                    relatedUserList = Mongo.getList(f"{table}User", criteria)
                    relatedUsers = sorted(
                        (
                            userInfo[r.user]
                            for r in relatedUserList
                            if r.user in userInfo
                        ),
                        key=lambda x: x.nickname or "",
                    )
                users = tuple((u.user, u.nickname) for u in relatedUsers)

                involvedUsers.append((table, role, users))

        if not asString:
            return tuple(involvedUsers)

        html = []

        seenUsers = set()

        for table, role, users in sorted(involvedUsers, key=lambda x: -len(x[2])):
            if len(users) == 0:
                continue

            userIds = {u[0] for u in users}

            if len(userIds - seenUsers) == 0:
                continue

            seenUsers |= userIds

            roles = auth.roles[table]
            roleRep = roles[role]

            label = H.i(f"{table} {roleRep}")
            userRep = " or ".join(H.span(name, uid=u) for (u, name) in users)
            html.append(f"{userRep}{H.nbsp}({label})")

        return f"ask: {'; '.join(html)}"

    def __loginSpecial(self, referrer, user):
        """Perform the steps to log in a test/pilot/custom user.

        This involves looking up the user in the user table,
        copying its information in the application-context-global `User`,
        and storing the user in the session. After that the user is redirected
        to where he came from.

        Parameters
        ----------
        referrer: string
            url where we came from.
        user: string
            The "sub" of the test/pilot user that we must log in as.

        Returns
        -------
        response
            A redirect to the referrer, with a status 302 if the log in was
            successful or 303 if not.
        """
        Messages = self.Messages
        Settings = self.Settings
        runMode = Settings.runMode

        if user is None or not self.__findSpecialUser(user):
            return redirectStatus(f"/{referrer}", False)

        sessionSet("user", user)
        uName = acg.User.nickname
        Messages.plain(
            logmsg=f"LOGIN successful: {runMode} user {uName} {user}",
            msg=f"LOGIN successful: {runMode} user {uName}",
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

    def __findSpecialUser(self, user):
        """Lookup data of a test/pilot user in the MongoDb user table.

        The user is looked up by the `user` field.

        Parameters
        ----------
        user: string
            The `user` of by which a user is looked up, if not None.

        Returns
        -------
        boolean
            Whether a user has been found/created.
            If so, the data of that user record is stored in the
            application-context-global `User`.
        """
        Messages = self.Messages
        Mongo = self.Mongo
        User = acg.User

        record = Mongo.getRecord("user", dict(user=user))

        if not record:
            Messages.warning(msg="Unknown user", logmsg=f"Unknown user {user}")
            return False

        User.clear()

        for att in PROVIDER_ATTS.values():
            User[att] = record[att]

        User.role = record.role

        return True

    def __findUser(self, user, update=False):
        """Lookup user data in the MongoDb user table.

        The user is looked up by the `user` field.
        Optionally, the user record in MongoDb is updated with attributes from
        the identity provider.

        Parameters
        ----------
        user: string
            The `user` of by which a user is looked up, if not None.
        update: boolean, optional False
            Whether to update the user record with fresh attributes of the
            identity provider.

        Returns
        -------
        boolean
            Whether a user has been found/created.
            If so, the data of that user record is stored in the
            application-context-global `User`.
        """
        Mongo = self.Mongo
        oidc = self.oidc
        User = acg.User

        def fillNickname(record):
            if not record.get("nickname", None):
                email = record.get("email", "") or ""
                record["nickname"] = email.split("@", 1)[0] or record.get(
                    "sub", "unknown_name"
                )

        record = Mongo.getRecord("user", dict(user=user), warn=False)
        newUser = None

        if not record:
            newUser = {
                att: oidc.user_getfield(oidcAtt)
                for (oidcAtt, att) in PROVIDER_ATTS.items()
            }
            fillNickname(newUser)
            newUser["role"] = "user"

            userId = Mongo.insertRecord("user", newUser)
            record = Mongo.getRecord("user", dict(_id=userId))

        User.clear()

        for att in PROVIDER_ATTS.values():
            User[att] = record[att]

        fillNickname(User)

        User.role = record.role

        if update and not newUser:
            givenUser = {
                att: oidc.user_getfield(oidcAtt)
                for (oidcAtt, att) in PROVIDER_ATTS.items()
            }
            # self.debug(f"{givenUser=}")
            # self.debug(f"{sessionGet('oidc_auth_profile')=}")

            fillNickname(givenUser)

            changes = {}

            for oidcAtt, att in PROVIDER_ATTS.items():
                orig = User[att]
                new = givenUser[att]

                if new is not None and orig != new:
                    changes[att] = new
                    User[att] = new

            if changes:
                Mongo.updateRecord("user", dict(user=User.user), changes, "system")

        return True
