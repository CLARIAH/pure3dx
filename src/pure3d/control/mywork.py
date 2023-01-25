from control.generic import AttrDict


class Mywork:
    def __init__(self, Content):
        """Get the list of relevant projects, editions and users.

        Admin users get the list of all users.

        Normal users get the list of users associated with

        * the project of which they are organiser
        * the editions of which they are editor or reviewer

        Guests and not-logged-in users cannot see any user.

        If the user has rights to modify the association
        between users and projects/editions, he will get
        the controls to do so.
        """
        self.Content = Content

        Messages = Content.Messages
        Messages.debugAdd(self)

        Settings = Content.Settings
        H = Settings.H
        authSettings = Settings.auth
        roles = authSettings.roles

        Mongo = Content.Mongo
        Auth = Content.Auth

        User = Auth.myDetails()
        user = User.user
        myRole = User.role
        inPower = myRole in {"root", "admin"}

        self.H = H
        self.User = User
        self.user = user
        self.myRole = myRole
        self.inPower = inPower

        if not self.user:
            return

        siteRoles = roles.site
        projectRoles = roles.project
        editionRoles = roles.edition

        self.siteRoles = siteRoles
        self.projectRoles = projectRoles
        self.editionRoles = editionRoles
        self.siteRolesList = sorted(siteRoles, key=lambda x: x or "")
        self.projectRolesList = sorted(projectRoles)
        self.editionRolesList = sorted(editionRoles)
        self.siteRolesSet = set(siteRoles)
        self.projectRolesSet = set(projectRoles)
        self.editionRolesSet = set(editionRoles)

        userList = Mongo.getList("user")
        projectList = Mongo.getList("project")
        editionList = Mongo.getList("edition")
        projectLinks = Mongo.getList("projectUser")
        editionLinks = Mongo.getList("editionUser")

        users = AttrDict({x.user: x for x in userList})
        projects = AttrDict({x._id: x for x in projectList})
        editions = AttrDict({x._id: x for x in editionList})

        myIds = AttrDict()

        self.users = users
        self.projects = projects
        self.myIds = myIds

        for eRecord in editionList:
            eId = eRecord._id
            pId = eRecord.projectId
            projects[pId].setdefault("editions", {})[eId] = eRecord

        for pLink in projectLinks:
            roles = pLink.roles
            if roles:
                u = pLink.user
                uRecord = users[u]
                pId = pLink.projectId
                pRecord = projects[pId]
                pRecord.setdefault("users", AttrDict())

                if user == u:
                    myIds.setdefault("project", set()).add(pId)
                    for eId in pRecord.editions or []:
                        myIds.setdefault("edition", set()).add(eId)

                pRecord.setdefault("users", AttrDict())[u] = (uRecord, roles)

        for eLink in editionLinks:
            roles = eLink.roles
            if roles:
                u = eLink.user
                uRecord = users[u]
                eId = eLink.editionId
                eRecord = editions[eId]
                pId = eRecord.projectId

                if user == u:
                    myIds.setdefault("project", set()).add(pId)
                    myIds.setdefault("edition", set()).add(eId)

                eRecord.setdefault("users", AttrDict())[u] = (uRecord, roles)

    def authUser(self, otherUser, table=None, record=None):
        """Check whether a user may change the role of another user.

        The question are:

        "which *other* site-wide roles can the current user assign to the other
        user?" (when no table or record are given).

        "which project/edition scoped roles can the current user assign to or
        remove from the other user
        with respect to the relevant record in the given table?".

        Note that the current site-wide role of the other user is never included
        in the set of resulting roles.

        There are also additional business rules.
        This function will return the empty set if these rules are violated.

        **Business rules**

        *   Users have exactly one site-wise role.
        *   Users may demote themselves.
        *   Users maynot promote themselves.
        *   Users may have zero or more project/edition-scoped roles per
            project/edition
        *   When assigning new site-wide or project-scoped or edition-scoped
            roles, these roles must be valid roles for that scope.
        *   When assigning a new site-wide role, None is not one
            of the possible new roles:
            you cannot change the status of an authenticated user to "not
            logged in".
        *   When assigning project/edition scoped roles, removing all such
            roles from a user for a certain project/edition means that
            other user is removed from that project or edition.
        *   Users cannot promote or demote people that are currently as powerful
            as themselves. Exception: roots may demote other roots.
            But in normal cases there is exactly one root.
            If a situation occurs that there is no root, it is not possible from
            within the application to appoint a root: you need an extra command
            outside the app, operated by a system manager.
        *   Roots may appoint admins and change site-wide roles.
        *   Root and admins may appoint project organisers, but may not assign
            project/edition-scoped roles.
        *   Project organisers may appoint edition editors and reviewers.
        *   Edition editors may appoint edition reviewers.
        *   However, roots and admins may also be project organisers and
            edition editors for some projects and some editions.
        *   Normal users and guests can not administer site-wide roles.
        *   Guests can not be put in project/edition-scoped roles.

        Parameters
        ----------
        otherUser: string
            the other user as string (eppn)
        table: string, optional None
            the relevant table: `project` or `edition`;
            this is the table in which the record sits
            relative to which the other user will be assigned a role.
            If None, the role to be assigned is a site wide role.
        record: ObjectId | AttrDict, optional None
            the relevant record;
            it is the record relative to which the other user will be
            assigned an other role.
            If None, the role to be assigned is a site wide role.

        Returns
        -------
        frozenset
            The assignable roles to the other user by the current user with respect
            to the given table and record or site-wide.
        """
        myRole = self.myRole

        if myRole in {None, "guest"}:
            return frozenset()

        user = self.user
        users = self.users
        iAmInPower = self.inPower
        otherUserRecord = users[otherUser]
        otherRole = otherUserRecord.role
        otherIsInPower = otherRole in {"admin", "root"}

        # side-wide assignments

        if table is None or record is None:
            siteRolesSet = self.siteRolesSet

            # only admins and roots can change roles
            if not iAmInPower:
                return frozenset()

            theseSiteRoles = siteRolesSet - {None, otherRole}

            # root is all powerful
            if myRole == "root":
                return theseSiteRoles

            # when the user changes his own role: can only demote
            if user == otherUser:
                return theseSiteRoles - {"admin", "root"}

            # people cannot affect other more or equally powerful people
            if otherIsInPower:
                return frozenset()

            # people cannot promote others beyond their own level
            return theseSiteRoles - {otherRole, "root"}

        # not a project or edition, not a real record: Not allowed!

        if table not in {"project", "edition"} or record is None:
            return frozenset()

        # project-scoped assignments

        projectRolesSet = self.projectRolesSet

        if table == "project":
            # only admins and roots can assign a project-scoped role
            if not iAmInPower:
                return frozenset()

            # remaining cases are allowed
            return projectRolesSet

        # remaining case: only edition scoped.

        if table != "edition":
            return frozenset()

        # edition-scoped assignments

        projects = self.projects
        editionRolesSet = self.editionRolesSet

        # check whether the role is a edition-scoped role
        pRecord = projects[record.projectId]
        pUsers = pRecord.users or AttrDict()
        eUsers = record.users or AttrDict()

        otherProjectRoles = set((pUsers[otherUser] or [None, []])[1])
        otherEditionRoles = set((eUsers[otherUser] or [None, []])[1])

        myProjectRoles = set((pUsers[user] or [None, []])[1])
        myEditionRoles = set((eUsers[user] or [None, []])[1])

        # only organisers of the parent project can (un)assign an
        # edition editor

        iAmOrganiser = "organiser" in myProjectRoles
        otherIsOrganiser = "organiser" in otherProjectRoles
        iAmEditor = "editor" in myEditionRoles
        otherIsEditor = "editor" in otherEditionRoles

        # what I can do to myself
        if user == otherUser:
            if iAmOrganiser or iAmEditor:
                return editionRolesSet
            return frozenset()

        # what I can do to others
        if otherIsOrganiser:
            return frozenset()

        if otherIsEditor:
            if iAmOrganiser:
                return editionRolesSet
            return frozenset()

            return editionRolesSet

        if iAmOrganiser:
            return editionRolesSet
        if iAmEditor:
            return editionRolesSet - {"editor"}

        return frozenset()

    def wrap(self):
        """Produce a list of projects and editions for root/admin usage.

        This overview shows all projects and editions
        with their associated users and roles.

        Only items that the user may read are shown.

        If the user is authorised to change associations between
        users and items, they will be editable.

        ## Overview of data

        ### projects

        All project records in the system, keyed by id.
        If a project has editions, the editions are
        available under key `editions` as a dict of edition
        records keyed by id.
        If a project has users, the users are
        available under key `users` as a dict keyed by role and then by user id
        and valued by the user records.

        If an edition has users, the users are
        available under key `users` as a dict keyed by role and then by user id
        and valued by the user records.

        ### users

        All user records in the system, keyed by id.

        ### myIds

        All project and edition ids to which the current users as a relationship.
        It is a dict with keys `project` and `edition` and the values are sets
        of ids.
        """
        H = self.H
        user = self.user

        if not user:
            H = self.H
            return H.p(
                "Log in to view the projects and editions that you are working on."
            )

        projects = self.projects
        myIds = self.myIds
        siteRoles = self.siteRoles

        User = self.User
        inPower = self.inPower
        user = self.user

        projectsAll = sorted(
            projects.values(), key=lambda x: (1 if x.isVisible else 0, x.title, x._id)
        )
        projectsMy = [p for p in projectsAll if p._id in (myIds.project or set())]

        wrapped = [
            H.h(1, "My details"),
            self.wrapUsers(siteRoles, theseUsers={User.user: (User, [User.role])}),
        ]

        wrapped.append(H.h(1, "My projects and editions"))
        wrapped.append(
            H.div([self.wrapProject(p) for p in projectsMy])
            if len(projectsMy)
            else H.div("You do not have specific roles w.r.t. projects and editions.")
        )

        if inPower:
            wrapped.append(H.h(1, "All projects and editions"))
            wrapped.append(
                H.div([self.wrapProject(p, myOnly=False) for p in projectsAll])
                if len(projectsAll)
                else H.div("There are no projects and no editions")
            )

            wrapped.append(H.h(1, "Manage users"))
            wrapped.append(H.div(self.wrapUsers(siteRoles), cls="susers"))

        return "".join(wrapped)

    def wrapProject(self, p, myOnly=True):
        H = self.H
        myIds = self.myIds
        projectRoles = self.projectRoles

        status = "public" if p.isVisible else "hidden"
        statusCls = "public" if p.isVisible else "wip"

        theseEditions = sorted(
            (
                e
                for e in p.editions.values()
                if not myOnly or e._id in (myIds.edition or set())
            ),
            key=lambda x: (x.title, x._id),
        )
        return H.div(
            [
                H.div(
                    [
                        H.div(status, cls=f"pestatus {statusCls}"),
                        H.a(p.title, f"project/{p._id}", cls="ptitle"),
                        H.div(
                            self.wrapUsers(
                                projectRoles,
                                table="project",
                                record=p,
                            ),
                            cls="pusers",
                        ),
                    ],
                    cls="phead",
                ),
                H.div(
                    "no editions"
                    if len(theseEditions) == 0
                    else [self.wrapEdition(e) for e in theseEditions],
                    cls="peditions",
                ),
            ],
            cls="pentry",
        )

    def wrapEdition(self, e):
        H = self.H
        editionRoles = self.editionRoles

        status = "published" if e.isPublished else "in progress"
        statusCls = "published" if e.isPublished else "wip"
        return H.div(
            [
                H.div(status, cls=f"pestatus {statusCls}"),
                H.a(e.title, f"edition/{e._id}", cls="etitle"),
                H.div(
                    self.wrapUsers(editionRoles, table="edition", record=e),
                    cls="eusers",
                ),
            ],
            cls="eentry",
        )

    def wrapUsers(self, itemRoles, table=None, record=None, theseUsers=None):
        H = self.H
        users = self.users

        if record is None:
            if theseUsers is None:
                theseUsers = {
                    u: (uRecord, [uRecord.role]) for (u, uRecord) in users.items()
                }
        else:
            theseUsers = record.users

        if theseUsers is None:
            return "No users"

        wrapped = []

        for (u, (uRecord, roles)) in sorted(
            theseUsers.items(), key=lambda x: (x[1][1], x[1][0].nickname, x[0])
        ):
            otherRoles = self.authUser(u, table=table, record=record)
            button = (
                H.div(
                    H.actionButton("edit_assign") if otherRoles else H.nbsp,
                    cls="rolebutton",
                ),
            )
            wrapped.append(
                H.div(
                    [
                        H.div(uRecord.nickname, cls="user"),
                        H.div(
                            [H.div(role, cls="role") for role in roles],
                            cls="roles",
                        ),
                        button,
                        H.div(
                            [H.div(role, cls="role") for role in otherRoles],
                            cls="roles",
                        ),
                    ],
                    cls="userroles",
                )
            )

        return "".join(wrapped)

    def wrapUser(self, u):
        H = self.H
        siteRoles = self.siteRoles

        name = u.nickname
        mail = u.email or "no email"
        role = siteRoles[u.role]

        return H.div(
            [
                H.div(name, cls="user"),
                H.div(mail, cls="email"),
                H.div(role, cls="role"),
            ],
            cls="udetails",
        )
