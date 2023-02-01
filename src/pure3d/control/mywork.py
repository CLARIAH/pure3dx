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

        Upon initialization the project/edition/user data will be read
        and assembled in a form ready for generating html.

        ## Overview of assembled data

        ### projects

        All project records in the system, keyed by id.
        If a project has editions, the editions are
        available under key `editions` as a dict of edition records keyed by id.
        If a project has users, the users are
        available under key `users` as a dict keyed by user id
        and valued by the user records.

        If an edition has users, the users are
        available under key `users` as a dict keyed by role and then by user id
        and valued by a tuple of the user record and the list of his roles.

        ### users

        All user records in the system, keyed by id.

        ### myIds

        All project and edition ids to which the current user has a relationship.
        It is a dict with keys `project` and `edition` and the values are sets
        of ids.
        """
        self.Content = Content

        Messages = Content.Messages
        Messages.debugAdd(self)

        Settings = Content.Settings
        H = Settings.H
        authSettings = Settings.auth
        roleInfo = authSettings.roles
        roleRank = authSettings.roleRank

        Mongo = Content.Mongo
        Auth = Content.Auth

        User = Auth.myDetails()
        user = User.user
        myRole = User.role
        inPower = myRole in {"root", "admin"}

        self.Mongo = Mongo
        self.H = H
        self.User = User
        self.user = user
        self.myRole = myRole
        self.inPower = inPower

        if not self.user:
            return

        siteRoles = roleInfo.site
        projectRoles = roleInfo.project
        editionRoles = roleInfo.edition

        self.siteRoles = siteRoles
        self.projectRoles = projectRoles
        self.editionRoles = editionRoles
        self.roleRank = roleRank
        self.siteRolesList = tuple(sorted(siteRoles, key=roleRank))
        self.projectRolesList = tuple(sorted(projectRoles, key=roleRank))
        self.editionRolesList = tuple(sorted(editionRoles, key=roleRank))
        self.siteRolesSet = frozenset(siteRoles)
        self.projectRolesSet = frozenset(projectRoles)
        self.editionRolesSet = frozenset(editionRoles)

        self.update()

    def update(self):
        Mongo = self.Mongo
        user = self.user

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
        self.editions = editions
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

                pRecord.setdefault("users", AttrDict())[u] = (uRecord, frozenset(roles))

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

                eRecord.setdefault("users", AttrDict())[u] = (uRecord, frozenset(roles))

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
        *   Users maynot promote themselves unless ... see later.
        *   Users may have zero or more project/edition-scoped roles per
            project/edition
        *   When assigning new site-wide or project-scoped or edition-scoped
            roles, these roles must be valid roles for that scope.
        *   When assigning a new site-wide role, None is not one
            of the possible new roles:
            you cannot change the status of an authenticated user to "not
            logged in".
        *   When assigning project/edition scoped roles, removing all such
            roles from a user for a certain project/edition means that the
            other user is removed from that project or edition.
        *   Users cannot promote or demote people that are currently as powerful
            as themselves.
        *   In normal cases there is exactly one root, but:
            *   If a situation occurs that there is no root and no admin, any authenticated
                user my grab the role of admin.
            *   If a situation occurs that there is no root, any admin may
                grab the role of root.
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
        boolean, frozenset
            The boolean indicates whether the current user may modify the set of roles
            of the target user.

            The frozenset is the set of assignable roles to the other user
            by the current user with respect to the given table and record or site-wide.

            If the boolean is false, the frozenset is empty.
            But if the frozenset is empty it might be the case that the current
            user is allowed to remove all roles of the target user.
        """
        myRole = self.myRole

        if myRole in {None, "guest"}:
            return (False, frozenset())

        user = self.user
        users = self.users
        nRoots = sum(1 for u in users.values() if u.role == "root")
        nAdmins = sum(1 for u in users.values() if u.role == "admin")
        iAmInPower = self.inPower
        otherUserRecord = users[otherUser]
        otherRole = otherUserRecord.role
        otherIsInPower = otherRole in {"admin", "root"}

        # side-wide assignments

        if table is None or record is None:
            siteRolesSet = self.siteRolesSet

            # if there are no admins and no roots,
            #   any admin may promote himself to root
            #   if there are no admins
            #     any authenticated user may promote himself to admin

            if nRoots == 0:
                if nAdmins == 0:
                    if myRole == "user":
                        return (True, frozenset({"admin"}))
                else:
                    if myRole == "admin":
                        return (True, frozenset({"root"}))

            # from here on, only admins and roots can change roles
            if not iAmInPower:
                return (False, frozenset())

            remainingRoles = frozenset(siteRolesSet - {None, otherRole})

            # root is all powerful, only limited by other roots
            if myRole == "root":
                if user == otherUser or otherRole != "root":
                    return (True, remainingRoles)
                else:
                    return (False, frozenset())

            # from here on, myRole is admin, so "root" cannot be assigned

            remainingRoles = frozenset(remainingRoles - {"root"})

            # when the user changes his own role: can only demote
            if user == otherUser:
                return (True, remainingRoles - {"admin"})

            # people cannot affect other more or equally powerful people
            if otherIsInPower:
                return (False, frozenset())

            # people cannot promote others beyond their own level
            return (True, remainingRoles)

        # not a project or edition, not a real record: Not allowed!

        if table not in {"project", "edition"} or record is None:
            return (False, frozenset())

        # project-scoped assignments

        projectRolesSet = self.projectRolesSet

        if table == "project":
            # only admins and roots can assign a project-scoped role
            if not iAmInPower:
                return (False, frozenset())

            # remaining cases are allowed
            return (True, projectRolesSet)

        # remaining case: only edition scoped.

        if table != "edition":
            return (False, frozenset())

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
                return (True, editionRolesSet)
            return (False, frozenset())

        # what I can do to others
        if otherIsOrganiser:
            return (False, frozenset())

        if otherIsEditor:
            if iAmOrganiser:
                return (True, editionRolesSet)
            return (False, frozenset())

        if iAmOrganiser:
            return (True, editionRolesSet)
        if iAmEditor:
            return (True, editionRolesSet - {"editor"})

        return (False, frozenset())

    def wrap(self):
        """Produce a list of projects and editions and users for root/admin usage.

        The first overview shows all projects and editions
        with their associated users and roles.

        Only items that are relevant to the user are shown.

        If the user is authorised to change associations between
        users and items, they will be editable.

        The second overview is for admin/roots only.
        It shows a list of users and their site-wide roles, which can be changed.

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
            self.wrapUsers(
                siteRoles, theseUsers={User.user: (User, frozenset([User.role]))}
            ),
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

        return H.div(wrapped, cls="myadmin")

    def wrapProject(self, project, myOnly=True):
        """Generate HTML for a project in admin view.

        Parameters
        ----------
        project: AttrDict
            A project record
        myOnly: boolean, optional False
            Whether to show only the editions in the project that are associated
            with the current user.

        Returns
        -------
        string
            The HTML
        """
        H = self.H
        myIds = self.myIds
        projectRoles = self.projectRoles

        status = "public" if project.isVisible else "hidden"
        statusCls = "public" if project.isVisible else "wip"

        theseEditions = sorted(
            (
                e
                for e in project.editions.values()
                if not myOnly or e._id in (myIds.edition or set())
            ),
            key=lambda x: (x.title, x._id),
        )
        return H.div(
            [
                H.div(
                    [
                        H.div(status, cls=f"pestatus {statusCls}"),
                        H.a(project.title, f"project/{project._id}", cls="ptitle"),
                        H.div(
                            self.wrapUsers(
                                projectRoles,
                                table="project",
                                record=project,
                                multiple=True,
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

    def wrapEdition(self, edition):
        """Generate HTML for an edition in admin view.

        Parameters
        ----------
        edition: AttrDict
            An edition record

        Returns
        -------
        string
            The HTML
        """
        H = self.H
        editionRoles = self.editionRoles

        status = "published" if edition.isPublished else "in progress"
        statusCls = "published" if edition.isPublished else "wip"
        return H.div(
            [
                H.div(status, cls=f"pestatus {statusCls}"),
                H.a(edition.title, f"edition/{edition._id}", cls="etitle"),
                H.div(
                    self.wrapUsers(
                        editionRoles, table="edition", record=edition, multiple=True
                    ),
                    cls="eusers",
                ),
            ],
            cls="eentry",
        )

    def saveRoles(self, u, multiple, newRoles, table=None, recordId=None):
        """Checks whether the current user may assign certain roles to a target user.

        It will be checked whether the roles are valid roles, whether the
        multiplicity of roles is OK, and whether the user has permission to
        perform this role assignment.

        Parameters
        ----------
        u: string
            The eppn of the user.
        multiple: boolean
            Whether multiple roles or a single role will be assigned
        newRoles: list
            The new roles for the target user.
        table: string
            Either None or `project` or `edition`, indicates what users we
            are listing: site-wide users or users related to a project or to an edition.
        recordId: ObjectId or None
            Either None or the id of a project or edition, corresponding to the
            `table` parameter.

        Returns
        -------
        dict
            with keys:

            * `stat`: indicates whether the save may proceed;
            * `msgs`: list of messages for the user,
            * `updated`: new content for the user managment div.
        """
        Mongo = self.Mongo

        (editable, otherRoles) = self.authUser(u, table=table, record=recordId)
        if not editable:
            return dict(stat=False, msgs=[["error", "update not allowed"]])

        wrongRoles = []

        for newRole in newRoles:
            if newRole not in otherRoles:
                wrongRoles.append(newRole)

        if len(wrongRoles):
            return dict(
                stat=False,
                msgs=[["error", "invalid role(s): " + ", ".join(wrongRoles)]],
            )

        nNewRoles = len(newRoles)

        if multiple:
            saveValue = newRoles
        else:
            if nNewRoles != 1:
                msg = (
                    "can not remove the role of a user"
                    if nNewRoles == 0
                    else "can not assign multiple roles to a user"
                )
                return dict(stat=False, msgs=[["error", msg]])

            saveValue = newRoles[0]

        result = (
            Mongo.updateRecord("user", dict(role=saveValue), user=u)
            if table is None
            else Mongo.updateRecord(
                f"{table}User",
                dict(roles=saveValue),
                **{"user": u, f"{table}Id": recordId},
            )
        )

        if result is None:
            return dict(
                stat=False,
                messages=[["error", "could not update the record in the database"]],
            )

        self.update()
        return dict(stat=True, messages=[], updated=self.wrap())

    def getRoles(self, u, table=None, recordId=None):
        """Get the role(s) of a user, either site-wide, or wrt to a project/edition.

        Parameters
        ----------
        u: string
            The eppn of the user.
        table: string
            Either None or `project` or `edition`, indicates what users we
            are listing: site-wide users or users related to a project or to an edition.
        recordId: ObjectId or None
            Either None or the id of a project or edition, corresponding to the
            `table` parameter.
        """
        users = self.users
        projects = self.projects
        editions = self.editions

        roles = frozenset()

        if table is None:
            source = users[u]
            if source:
                roles = frozenset([source.role])
        else:
            source = (
                projects
                if table == "project"
                else editions
                if table == "edition"
                else None
            )
            if source:
                source = source[recordId]
                if source:
                    source = source.users
                    if source:
                        source = source[u]
                        if source:
                            roles = source[1]
        return roles

    def wrapUsers(
        self, itemRoles, table=None, record=None, theseUsers=None, multiple=False
    ):
        """Generate HTML for a list of users.

        It is dependent on the value of table/record whether it is about the users
        of a specific project/edition or the site-wide users.

        Parameters
        ----------
        itemRoles: dict
            Dictionary keyed by the possible roles and valued by the description
            of that role.
        table: string, optional None
            Either `project` or `edition`, indicates what users we are listing:
            related to a project or to an edition.
        record: AttrDict, optional None
            If `table` is passed and not None, here is the specific project or edition
            whose users should be listed.
        theseUsers: dict, optional None
            If table/record is not specified, you can specify users here.
            If this parameter is also None, then all users in the system are taken.
            Otherwise you have to specify a dict, keyed by user eppns and valued by
            tuples consisting of a user record and a list of roles.
        multiple: boolean, optional False
            Whether users can have multiple roles of this kind.

        Returns
        -------
        string
            The HTML
        """
        users = self.users

        if record is None:
            if theseUsers is None:
                theseUsers = {
                    u: (uRecord, frozenset([uRecord.role]))
                    for (u, uRecord) in users.items()
                }
        else:
            theseUsers = record.users

        if theseUsers is None:
            return "No users"

        wrapped = []

        for (u, (uRecord, roles)) in sorted(
            theseUsers.items(), key=lambda x: (x[1][1], x[1][0].nickname, x[0])
        ):
            (editable, otherRoles) = self.authUser(u, table=table, record=record)
            wrapped.append(
                self.wrapUser(
                    u,
                    uRecord,
                    roles,
                    editable,
                    otherRoles,
                    itemRoles,
                    table,
                    record._id if record else None,
                    multiple,
                )
            )

        return "".join(wrapped)

    def wrapUser(
        self,
        u,
        uRecord,
        roles,
        editable,
        otherRoles,
        itemRoles,
        table,
        recordId,
        multiple,
    ):
        """Generate HTML for a single user and his roles.

        Parameters
        ----------
        u: string
            The eppn of the user.
        uRecord: AttrDict
            The user record.
        roles: frozenset
            The actual roles of the user.
        editable: boolean
            Whether the current user may changes the roles of this user.
        otherRoles: frozenset
            The other roles that the user may get from the current user.
        itemRoles: dict
            Dictionary keyed by the possible roles and valued by the description
            of that role.
        table: string
            Either None or `project` or `edition`, indicates what users we
            are listing: site-wide users or users related to a project or to an edition.
        recordId: ObjectId or None
            Either None or the id of a project or edition, corresponding to the
            `table` parameter.
        multiple: boolean
            Whether users can have multiple roles of this kind.

        Returns
        -------
        string
            The HTML
        """
        H = self.H

        return H.div(
            [
                H.div(uRecord.nickname, cls="user"),
                *self.wrapRoles(
                    u, itemRoles, roles, editable, otherRoles, table, recordId, multiple
                ),
            ],
            cls="userroles",
        )

    def wrapRoles(
        self, u, itemRoles, roles, editable, otherRoles, table, recordId, multiple
    ):
        """Generate HTML for a list of roles.

        This may or may not be an editable widget, depending on whether there
        are options to choose from.

        Site-wide users have a single site-wide role. But project/edition users
        can have multiple roles wrt projects/editions.

        If multiple roles are allowed, you have to pass `multiple=True`.

        Parameters
        ----------
        u: string
            The eppn of the user.
        itemRoles: dict
            Dictionary keyed by the possible roles and valued by the description
            of that role.
        roles: frozenset
            The actual roles that the user in question has.
        editable: boolean
            Whether the current user may changes the roles of this user.
        otherRoles: frozenset
            The other roles that the user may get from the current user.
        table: string
            Either None or `project` or `edition`, indicates what users we
            are listing: site-wide users or users related to a project or to an edition.
        recordId: ObjectId or None
            Either None or the id of a project or edition, corresponding to the
            `table` parameter.
        multiple: boolean
            Whether users can have multiple roles of this kind.

        Returns
        -------
        string
            The HTML
        """
        roleRank = self.roleRank
        H = self.H

        showRoles = sorted(roles, key=roleRank)
        showOtherRoles = sorted(otherRoles, key=roleRank)

        actualRoles = H.div(
            [H.div(itemRoles[role], cls="role", role=role) for role in showRoles],
            cls="roles",
        )
        tableRep = f"/{table}" if table else ""
        recordRep = f"/{recordId}" if table else ""
        multipleRep = "multiple" if multiple else "single"

        allOtherRoles = (
            showOtherRoles if multiple else sorted(roles | otherRoles, key=roleRank)
        )

        if editable:
            saveUrl = f"/save/roles/{u}/{multipleRep}/{tableRep}{recordRep}"
            updateButton = H.actionButton("edit_assign")
            cancelButton = H.actionButton("edit_cancel")
            saveButton = H.actionButton("edit_save")
            msgs = H.div("", cls="editmsgs")

            widget = H.div(
                [
                    updateButton,
                    saveButton,
                    cancelButton,
                    msgs,
                    H.div(
                        [
                            H.div(
                                itemRoles[role],
                                cls="role button " + ("on" if role in roles else ""),
                                role=role,
                            )
                            for role in allOtherRoles
                        ],
                        cls="edit roles",
                        multiple=multiple,
                        saveurl=saveUrl,
                        origvalue=",".join(showRoles),
                    ),
                ],
                cls="editroles",
            )
        else:
            widget = ""

        return [actualRoles, widget]
