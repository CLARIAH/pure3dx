# from control.generic import AttrDict


class Wrap:
    def __init__(self, Settings, Messages, Viewers):
        """Wrap concepts into HTML.

        This class knows how to wrap several higher-level concepts into HTML,
        such as projects, editions and users, depending on specific
        purposes, such as showing widgets to manage projects and editions.

        It is instantiated by a singleton object.

        Parameters
        ----------
        Settings: AttrDict
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        Viewers: object
            Singleton instance of `control.viewers.Viewers`.
        """
        self.Settings = Settings
        self.Messages = Messages
        self.Viewers = Viewers
        Messages.debugAdd(self)

    def addAuth(self, Auth):
        """Give this object a handle to the Auth object.

        The Wrap and Auth objects need each other, so one of them must
        be given the handle to the other after initialization.
        """
        self.Auth = Auth

    def addContent(self, Content):
        """Give this object a handle to the Content object.

        The Wrap and Content objects need each other, so one of them must
        be given the handle to the other after initialization.
        """
        self.Content = Content

    def projectsMain(self, site, projects):
        """Wrap the list of projects for the main display.

        Parameters
        ----------
        site: AttrDict
            The record that corresponds to the site as a whole.
            It acts as a master record of the projects.
        projects: list of AttrDict
            The project records.

        Returns
        -------
        string
            The HTML of the project list
        """
        Settings = self.Settings
        H = Settings.H
        Auth = self.Auth
        Content = self.Content

        wrapped = []
        wrapped.append(
            H.p(self.contentButton("site", site, action="create", insertTable="project"))
        )

        for project in projects:
            projectId = project._id
            permitted = Auth.authorise("project", project, action="read")
            if not permitted:
                continue

            title = project.title

            projectUrl = f"/project/{projectId}"
            button = self.contentButton("project", project, "delete")
            visual = Content.getUpload(project, "iconProject")
            caption = self.getCaption(visual, title, button, projectUrl)

            wrapped.append(caption)

        return H.content(*wrapped)

    def editionsMain(self, project, editions):
        """Wrap the list of editions of a project for the main display.

        Parameters
        ----------
        project: AttrDict
            The master project record of the editions.
        editions: list of AttrDict
            The edition records.

        Returns
        -------
        string
            The HTML of the edition list
        """
        Settings = self.Settings
        H = Settings.H
        Auth = self.Auth
        Content = self.Content

        wrapped = []

        for edition in editions:
            editionId = edition._id
            permitted = Auth.authorise("edition", record=edition, action="read")
            if not permitted:
                continue

            title = edition.title

            editionUrl = f"/edition/{editionId}"
            button = self.contentButton("edition", edition, "delete")
            visual = Content.getUpload(edition, "iconEdition")
            caption = self.getCaption(visual, title, button, editionUrl)
            wrapped.append(caption)

        wrapped.append(
            H.p(self.contentButton("project", project, "create", insertTable="edition"))
        )
        return H.content(*wrapped)

    def sceneMain(self, edition, sceneFile, viewer, version, action):
        """Wrap the scene of an edition for the main display.

        Parameters
        ----------
        edition: AttrDict
            The edition record of the scene.
        viewer: string
            The viewer that will be used.
        version: string
            The version of the chosen viewer that will be used.
        action: string
            The mode in which the viewer should be opened.

        Returns
        -------
        string
            The HTML of the scene
        """
        Settings = self.Settings
        H = Settings.H
        Auth = self.Auth
        Viewers = self.Viewers

        wrapped = []

        actions = Auth.authorise("edition", edition)
        if "read" not in actions:
            return ""

        wrapped = []

        titleText = H.span(sceneFile, cls="entrytitle")
        button = self.contentButton("edition", edition, "delete")

        (frame, buttons) = Viewers.getFrame(edition, actions, viewer, version, action)
        title = H.span(titleText, cls="entrytitle")
        content = f"""{frame}{title}{buttons}"""
        caption = self.wrapCaption(content, button, active=True)

        wrapped.append(caption)
        return H.content(*wrapped)

    def projectsAdmin(self, projects, editions, users, myIds):
        """Produce a list of projects and editions for admin usage.

        This overview shows all projects and editions
        with their associated users and roles.

        Only items that the user may read are shown.

        If the user is authorised to change associations between
        users and items, they will be editable.

        Parameters
        ----------
        projects: dict
            All project records in the system, keyed by id.
            If a project has editions, the editions are
            available under key `editions` as a dict of edition
            records keyed by id.
            If a project has users, the users are
            available under key `users` as a dict keyed by role and then by user id
            and valued by the user records.
        editions: dict
            All edition records in the system, keyed by id.
            If an edition has users, the users are
            available under key `users` as a dict keyed by role and then by user id
            and valued by the user records.
        users: dict
            All user records in the system, keyed by id.
        myIds: AttrDict
            All project and edition ids to which the current users as a relationship.
            It is a dict with keys `project` and `edition` and the values are sets
            of ids.
        """
        Settings = self.Settings
        Auth = self.Auth
        User = Auth.myDetails()
        myRole = User.role
        user = User.user

        H = Settings.H
        authSettings = Settings.auth
        roles = authSettings.roles

        pRoles = sorted(roles.project)
        eRoles = sorted(roles.edition)

        def authUser(otherUser, table=None, record=None):
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
            otherUser: string, optional None
                the other user
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
            if myRole in {None, "guest"}:
                return frozenset()

            otherRole = users[otherUser].role

            # side-wide assignments

            if table is None or record is None:
                # only admins and roots can change roles
                if myRole not in {"root", "admin"}:
                    return frozenset()

                siteRoles = set(roles.site) - {None, otherRole}

                # root is all powerful
                if myRole == "root":
                    return siteRoles

                # when the user changes his own role: can only demote
                if user == otherUser:
                    return siteRoles - {"admin", "root"}

                # people cannot affect other more or equally powerful people
                if otherRole in {"admin", "root"}:
                    return frozenset()

                # people cannot promote others beyond their own level
                return siteRoles - {otherRole, "root"}

            # not a project or edition, not a real record: Not allowed!

            if table not in {"project", "edition"} or record is None:
                return frozenset()

            # project-scoped assignments

            if table == "project":
                # only admins and roots can assign a project-scoped role
                if myRole not in {"root", "admin"}:
                    return frozenset()

                # remaining cases are allowed
                projectRoles = set(roles.project)
                return projectRoles

            # remaining case: only edition scoped.

            if table != "edition":
                return frozenset()

            # edition-scoped assignments

            editionRoles = set(roles.edition)

            # check whether the role is a edition-scoped role
            pRecord = projects[record.projectId]

            otherProjectRoles = {
                role for role in roles.project if otherUser in pRecord.users[role]
            }

            otherEditionRoles = {
                role for role in roles.edition if otherUser in record.users[role]
            }

            myProjectRoles = {
                role for role in roles.project if user in pRecord.users[role]
            }

            myEditionRoles = {
                role for role in roles.edition if user in record.users[role]
            }

            # only organisers of the parent project can (un)assign an
            # edition editor

            iAmOrganiser = "organiser" in myProjectRoles
            otherIsOrganiser = "organiser" in otherProjectRoles
            iAmEditor = "editor" in myEditionRoles
            otherIsEditor = "editor" in otherEditionRoles

            # what I can do to myself
            if user == otherUser:
                if iAmOrganiser or iAmEditor:
                    return editionRoles
                return frozenset()

            # what I can do to others
            if otherIsOrganiser:
                return frozenset()

            if otherIsEditor:
                if iAmOrganiser:
                    return editionRoles
                return frozenset()

                return editionRoles

            if iAmOrganiser:
                return editionRoles
            if iAmEditor:
                return editionRoles - {"editor"}

            return frozenset()

        def wrapUser(u):
            name = u.nickname
            mail = u.email or "no email"
            role = roles.site[u.role]

            return H.div(
                [
                    H.div(name, cls="user"),
                    H.div(mail, cls="email"),
                    H.div(role, cls="role"),
                ],
                cls="udetails",
            )

        def wrapProject(p, myOnly=True):
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
                                "no users"
                                if p.users is None
                                else wrapUsers(pRoles, p.users),
                                cls="pusers",
                            ),
                        ],
                        cls="phead",
                    ),
                    H.div(
                        "no editions"
                        if len(theseEditions) == 0
                        else [wrapEdition(e) for e in theseEditions],
                        cls="peditions",
                    ),
                ],
                cls="pentry",
            )

        def wrapEdition(e):
            status = "published" if e.isPublished else "in progress"
            statusCls = "published" if e.isPublished else "wip"
            return H.div(
                [
                    H.div(status, cls=f"pestatus {statusCls}"),
                    H.a(e.title, f"edition/{e._id}", cls="etitle"),
                    H.div(
                        "no users" if e.users is None else wrapUsers(eRoles, e.users),
                        cls="eusers",
                    ),
                ],
                cls="eentry",
            )

        def wrapUsers(itemRoles, users):
            return [
                H.div(
                    [
                        H.div(role, cls=f"role {role}"),
                        H.div(
                            H.nbsp
                            if users[role] is None
                            else [
                                H.div(u.nickname, cls="user")
                                for u in users[role].values()
                            ],
                            cls=f"users {role}",
                        ),
                    ],
                    cls="roleusers",
                )
                for role in itemRoles
            ]

        if myRole == "admin":
            usersAll = sorted(
                users.values(), key=lambda x: (x.role, x.nickname, x.email, x._id)
            )

        projectsAll = sorted(
            projects.values(), key=lambda x: (1 if x.isVisible else 0, x.title, x._id)
        )
        projectsMy = [p for p in projectsAll if p._id in (myIds.project or set())]

        wrapped = [H.h(1, "My details"), wrapUser(User)]

        wrapped.append(H.h(1, "My projects and editions"))
        wrapped.append(
            H.div([wrapProject(p) for p in projectsMy])
            if len(projectsMy)
            else H.div("You do not have specific roles w.r.t. projects and editions.")
        )

        if myRole == "admin":
            wrapped.append(H.h(1, "All projects and editions"))
            wrapped.append(
                H.div([wrapProject(p, myOnly=False) for p in projectsAll])
                if len(projectsAll)
                else H.div("There are no projects and no editions")
            )

            wrapped.append(H.h(1, "Manage users"))
            wrapped.append(
                H.div([wrapUser(u) for u in usersAll])
                if len(usersAll)
                else H.div("There are no users")
            )

        return "".join(wrapped)

    def getCaption(self, visual, titleText, button, url):
        Settings = self.Settings
        H = Settings.H

        title = H.span(titleText, cls="entrytitle")
        content = H.a(f"{visual}{title}", url, cls="entry")

        return self.wrapCaption(content, button)

    def wrapCaption(self, content, button, active=False):
        Settings = self.Settings
        H = Settings.H

        activeCls = "active" if active else ""
        return H.div(
            [H.div(content, cls=f"caption {activeCls}"), button], cls="captioncontent"
        )

    def contentButton(
        self,
        table,
        record,
        action,
        permitted=None,
        insertTable=None,
        key=None,
        href=None,
    ):
        """Puts a button on the interface, if that makes sense.

        The button, when pressed, will lead to an action on certain content.
        It will be checked first if that action is allowed for the current user.
        If not the button will not be shown.

        !!! note "Delete buttons"
            Even if a user is authorised to delete a record,
            it is not allowed to delete master records if its detail records
            still exist.
            In that case, no delete button is displayed. Instead we display a count
            of detail records.

        !!! note "Create buttons"
            When placing a create button, the relevant record acts as the master
            record, to which the newly created record will be added as a detail.

        Parameters
        ----------
        table: string
            The relevant table.
        record: string | ObjectId | AttrDict
            The relevant record.
        action: string
            The type of action that will be performed if the button triggered.
        permitted: boolean, optional None
            If the permission for the action is already known before calling
            this function, it is passed here.
            If this parameter is None, we'll compute the permission.
        insertTable: string, optional None
            If the action is "create", this is the table in which a record
            get inserted. The `table` and `record` arguments are then
            supposed to specify the *master* record of the newly inserted record.
            Needed to determine whether a press on the button is permitted.
        key: string, optional None
            If present, it identifies a field that is stored inside the
            record.
        href: string, optional None
            If present, contains the href attribute for the button.
        """
        Auth = self.Auth
        Content = self.Content

        recordId = record._id

        permitted = (
            Auth.authorise(table, record, action=action, insertTable=insertTable)
            if permitted is None
            else permitted
        )

        if not permitted:
            return ""

        Settings = self.Settings
        H = Settings.H
        actions = Settings.auth.actions

        disable = False
        report = ""

        if action == "delete":
            details = Content.getDetailRecords(table, record)
            if len(details):
                disable = True
                detailContent = []
                for (detailTable, detailRecords) in details.items():
                    nDetails = len(detailRecords)
                    plural = "" if nDetails == 1 else "s"
                    detailRep = detailTable + plural
                    detailContent.append(f"""{nDetails}{H.nbsp}{detailRep}""")

                report = H.div(
                    [
                        H.span(thisContent, cls="dreport") + H.br()
                        for thisContent in detailContent
                    ]
                )
                report = H.br() + report

        actionInfo = actions.get(action, {})
        name = actionInfo.name
        keyRepTip = "" if key is None else f" {key} of"
        keyRepUrl = "" if key is None else f"/{key}"

        if disable:
            href = None
            cls = "disabled"
            can = "Cannot"
        else:
            cls = ""
            can = ""

        if action == "create":
            href = f"/{table}/{recordId}/{insertTable}/create" if href is None else href
            tip = f"{name} new {insertTable}"
        else:
            href = f"/{table}/{recordId}{keyRepUrl}/{action}" if href is None else href
            tip = f"{can}{name}{keyRepTip} this {table}"

        fullCls = f"button small {cls}"
        return H.iconx(action, href=href, title=tip, cls=fullCls) + report
