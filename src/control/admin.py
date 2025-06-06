import re
import json

from .flask import requestData
from .generic import AttrDict, lessAgo, amountTogo, isonow, dateOnly
from .helpers import normalize
from .files import dirExists, fileExists, fileRemove, FDEL

from .mongo import MDEL, MDELDT, MDELBY


USERNAME_RE = re.compile(r"[^a-z0-9._-]")


class Admin:
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
        and valued by a tuple of the user record and his role.

        ### users

        All user records in the system, keyed by id.

        ### myIds

        All project and edition ids to which the current user has a relationship.
        It is a dict with keys `project` and `edition` and the values are sets
        of ids.

        ### keywords

        The lists of keywords in metadata fields

        ### deleted items

        Projects and directories that have been marked as deleted, and can still be
        restored (after 30 days marked deleted items may no longer be restored and
        they will be deleted after 1 day more).
        """
        self.Content = Content

        Messages = Content.Messages
        Messages.debugAdd(self)

        self.Messages = Messages

        Settings = Content.Settings
        H = Settings.H
        authSettings = Settings.auth
        roleInfo = authSettings.roles
        roleRank = authSettings.roleRank
        representations = Settings.representations
        css = Settings.css

        Mongo = Content.Mongo
        Auth = Content.Auth

        self.Settings = Settings
        self.Mongo = Mongo
        self.Auth = Auth
        self.H = H
        self.representations = representations
        self.css = css

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

    # main WRAP function

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
            return (
                H.p(
                    "Log in to view the projects and editions that you are working on."
                ),
                "",
            )

        projects = self.projects
        delProjects = self.delProjects

        projectsAll = sorted(
            projects.values(),
            key=lambda x: (1 if x.isVisible else 0, x.title or "", x._id),
        )

        delProjectsAll = sorted(
            delProjects.values(),
            key=lambda x: (x.title or "", x._id),
        )

        inPower = self.inPower

        (myDetails, tocMyDetails) = self.wrapMyDetails()

        (myProjects, tocMyProjects) = self.wrapMyProjects(projectsAll)

        if inPower:
            (pubControls, tocPub) = self.wrapPubControls()
            (allProjects, tocProjects) = self.wrapAllProjects(projectsAll)
            (allKeywords, tocKeywords) = self.wrapKeywordControls()
            (allUsers, tocAllusers) = self.wrapUserControls()
            (allDeleted, tocDeleted) = self.wrapDeletedItems(delProjectsAll)
        else:
            pubControls, tocPub = "", ""
            allProjects, tocProjects = "", ""
            allKeywords, tocKeywords = "", ""
            allUsers, tocAllusers = "", ""
            allDeleted, tocDeleted = "", ""

        toc = (
            tocPub,
            tocKeywords,
            tocAllusers,
            tocMyDetails,
            tocMyProjects,
            tocProjects,
            tocDeleted,
        )

        return (
            H.div(
                [
                    pubControls,
                    allKeywords,
                    allUsers,
                    myDetails,
                    myProjects,
                    allProjects,
                    allDeleted,
                ],
                cls="myadmin",
            ),
            H.ul([H.li(x) for x in toc if x]),
        )

    # specialized WRAP functions

    def wrapMyDetails(self):
        """Generate HTML for the details of the current user.

        Parameters
        ----------
        projectsAll: list
            The list of all projects

        Returns
        -------
        string
            The html
        """
        H = self.H
        siteRoles = self.siteRoles
        User = self.User

        title = "My details"
        name = "my-details"
        tocEntry = H.a(title, f"#{name}")

        return (
            H.div(
                [
                    H.h(1, H.anchor(title, name)),
                    self.wrapUsers(
                        siteRoles, theseUsers={User.user: (User, User.role)}
                    ),
                ],
                id="mydetails",
            ),
            tocEntry,
        )

    def wrapMyProjects(self, projectsAll):
        """Generate HTML for the list of the projects of the current user.

        Only projects and editions that are not marked as deleted show up.

        Parameters
        ----------
        projectsAll: list
            The list of all projects

        Returns
        -------
        string
            The html
        """
        H = self.H
        myIds = self.myIds

        projectsMy = [p for p in projectsAll if p._id in (myIds.project or set())]

        title = "My projects and editions"
        name = "my-projects"
        tocEntry = H.a(title, f"#{name}")

        wrapped = [
            H.h(1, H.anchor(title, name)),
            (
                H.div([self.wrapProject(p) for p in projectsMy])
                if len(projectsMy)
                else H.div(
                    "You do not have a specific role w.r.t. projects and editions."
                )
            ),
        ]
        return (H.div(wrapped, id="myprojects"), tocEntry)

    def wrapPubControls(self):
        """Generate HTML for the published projects in admin view.

        Currently, it provides

        *   a control to edit the list of featured published projects in a
            rather coarse manner.
        *   a control to regenerate the static pages

        Returns
        -------
        string
            The HTML
        """
        H = self.H

        Content = self.Content
        (table, siteId, site) = Content.relevant()

        title = "Published projects"
        name = "pub-controls"
        tocEntry = H.a(title, f"#{name}")

        wrapped = []
        wrapped.append(H.h(1, H.anchor(title, name)))

        wrapped.append(H.h(2, "Featured published projects"))
        wrapped.append(Content.getValue(table, site, "featured"))

        wrapped.append(H.h(2, "Regenerate HTML for published projects"))
        wrapped.append(
            H.a(
                "Regenerate",
                "/generate",
                title="Regenerate HTML for published projects",
                cls="button large",
            )
        )

        wrapped.append(H.h(2, "Publishing process status"))
        wrapped.append(
            H.p(
                [
                    H.a(
                        "Check",
                        "#",
                        id="pubcheck",
                        title="Check status of publication processes",
                        cls="button large",
                    ),
                    H.span("", id="pubstatus", cls="large"),
                    H.a(
                        "terminate",
                        "#",
                        id="pubcontrol",
                        title="terminate publication processes",
                        cls="button large",
                    ),
                ]
            )
            + H.div("test", id="pubmessages"),
        )
        return (H.div(wrapped, id="pubcontrols"), tocEntry)

    def wrapKeywordControls(self):
        """Generate HTML for the keyword management.

        The keywords sit in a table with name `keyword`.
        Each record corresponds to a keyword, each keyword has fields:

        *   *name*: the name of the metadata field of which it is a value;
        *   *value*: the keyword itself;

        Returns
        -------
        string
            The html
        """
        H = self.H
        Content = self.Content

        keywords = Content.getKeywords()

        saveUrl = "/save/keyword/"
        cancelButton = H.actionButton("kwmanage_cancel")
        saveButton = H.actionButton("kwmanage_save")
        messages = H.div("", cls="editmsgs")

        def wrapKeyword(name, value, occ):
            deleteButton = H.iconx(
                "cross",
                title=f"delete keyword {value}",
                name=name,
                value=value,
                delUrl="/keyword/delete/",
                cls="danger",
            )
            return H.span(
                value + H.nbsp + (f"({occ})" if occ else deleteButton), cls="fieldinner"
            )

        def wrapKeywordList(name, values):
            editableContent = H.input(
                "", "text", cls="editcontent show", name=name, saveurl=saveUrl
            )

            return H.details(
                name,
                H.div(
                    H.div(
                        [
                            editableContent,
                            saveButton,
                            cancelButton,
                            messages,
                        ],
                        cls="kwmanagewidgetinput",
                    )
                    + H.span(
                        [
                            wrapKeyword(name, value, values[value])
                            for value in sorted(values)
                        ],
                        cls="fieldouter",
                    ),
                    cls="kwmanagewidget",
                ),
                f"keywordlist-{name}",
            )

        keywordMaterial = H.div(
            [wrapKeywordList(name, keywords[name]) for name in sorted(keywords)],
            cls="skeywords",
        )

        title = "Manage keywords"
        name = "manage-keywords"
        tocEntry = H.a(title, f"#{name}")

        wrapped = []
        wrapped.append(H.h(1, H.anchor(title, name)))
        wrapped.append(H.div(keywordMaterial))
        return (H.div(wrapped, id="keywordcontrols"), tocEntry)

    def wrapUserControls(self):
        """Generate HTML for the user management.

        Returns
        -------
        string
            The html
        """
        H = self.H
        siteRoles = self.siteRoles

        title = "Manage users"
        name = "manage-users"
        tocEntry = H.a(title, f"#{name}")

        wrapped = []
        wrapped.append(H.h(1, H.anchor(title, name)))
        wrapped.append(
            H.div(self.wrapUsers(siteRoles, workIndicator=True), cls="susers")
        )
        return (H.div(wrapped, id="allusers"), tocEntry)

    def wrapAllProjects(self, projectsAll):
        """Generate HTML for the list of all projects.

        Parameters
        ----------
        projectsAll: list
            The list of all projects, in as far they have not been marked as deleted.

        Returns
        -------
        string
            The html
        """
        H = self.H

        title = "All projects and editions"
        name = "all-projects"
        tocEntry = H.a(title, f"#{name}")

        wrapped = []
        wrapped.append(H.h(1, H.anchor(title, name)))
        wrapped.append(
            H.div([self.wrapProject(p, myOnly=False) for p in projectsAll])
            if len(projectsAll)
            else H.div("There are no projects and no editions")
        )
        return (H.div(wrapped, id="allprojects"), tocEntry)

    def wrapDeletedItems(self, delProjectsAll):
        """Generate HTML for the list of all deleted projects and editions.

        All projects that have been marked as deleted or contain editions that
        have been marked as deleted, are listed,
        together with their marked-deleted editions.

        For each marked-deleted item that is in the grace period of 30 days,
        a control is added to restore it.

        Parameters
        ----------
        delProjectsAll: list
            The list of all projects that are either marked deleted or have
            editions that are marked deleted, all within the grace period of 30 days.

        Returns
        -------
        string
            The html
        """
        H = self.H

        title = "Deleted projects and editions"
        name = "deleted-items"
        tocEntry = H.a(title, f"#{name}")

        wrapped = []
        wrapped.append(H.h(1, H.anchor(title, name)))

        wrappedProjects = [self.wrapDelProject(p) for p in delProjectsAll]

        wrapped.append(
            H.div(wrappedProjects)
            if len(wrappedProjects)
            else H.div("There are no deleted projects/editions")
        )

        return (H.div(wrapped, id="delprojects"), tocEntry)

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
        representations = self.representations
        css = self.css

        stat = project.isVisible or False
        status = representations.isVisible[stat]
        statusCls = css.isVisible[stat]

        editions = project.editions or AttrDict()

        theseEditions = sorted(
            (
                e
                for e in editions.values()
                if not myOnly or e._id in (myIds.edition or set())
            ),
            key=lambda x: (x.title or "", x._id),
        )
        title = project.title or H.i("no title")

        return H.div(
            [
                H.div(
                    [
                        H.div(status, cls=f"pestatus {statusCls}"),
                        H.a(title, f"project/{project._id}", cls="ptitle"),
                        H.div(
                            self.wrapUsers(
                                projectRoles, table="project", record=project
                            ),
                            cls="pusers",
                        ),
                    ],
                    cls="phead",
                ),
                H.div(
                    (
                        "no editions"
                        if len(theseEditions) == 0
                        else [self.wrapEdition(e) for e in theseEditions]
                    ),
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
        representations = self.representations
        css = self.css

        stat = edition.isPublished or False
        status = representations.isPublished[stat]
        statusCls = css.isPublished[stat]

        title = edition.title or H.i("no title")

        return H.div(
            [
                H.div(status, cls=f"pestatus {statusCls}"),
                H.a(title, f"edition/{edition._id}", cls="etitle"),
                H.div(
                    self.wrapUsers(editionRoles, table="edition", record=edition),
                    cls="eusers",
                ),
            ],
            cls="eentry",
        )

    def wrapDelProject(self, project):
        """Generate HTML for a deleted project in admin view.

        Parameters
        ----------
        project: AttrDict
            A record of a project that is deleted or has deleted editions.

        Returns
        -------
        string
            The HTML
        """
        Settings = self.Settings
        delayUndel = Settings.sweeper.delayUndel

        H = self.H
        title = project.title or H.i("no title")
        pDeleted = project.get(MDEL, False)

        if pDeleted:
            pDeletedBy = project.get(MDELBY, None) or "unknown"
            pDeletedTm = project.get(MDELDT, "2000-01-01T00:00:00Z")
            pDeletedDt = dateOnly(pDeletedTm)
            pRemainingDays = amountTogo(delayUndel, pDeletedTm, iso=True)

            pTitle = H.span(title, cls="ptitle")
            pStatus = H.span(f"on {pDeletedDt} by {pDeletedBy}", cls="pestatus warning")
            pId = project._id
            pControl = H.span(
                f"undelete ({pRemainingDays:4.2f} days left)",
                url=f"project/{pId}/undelete",
                title=f"undelete project {pId}",
                cls="button medium undelete",
            )
        else:
            pTitle = H.a(title, f"project/{project._id}", cls="ptitle")
            pStatus = ""
            pControl = ""

        editions = (
            sorted(project.editions.values(), key=lambda x: (x.title or "", x._id))
            if project.editions
            else []
        )

        return H.div(
            [
                H.div(f"{pControl} {pTitle} {pStatus}", cls="phead"),
                H.div(
                    [self.wrapDelEdition(e, pDeleted) for e in editions],
                    cls="peditions",
                ),
            ],
            cls="pentry",
        )

    def wrapDelEdition(self, edition, pDeleted):
        """Generate HTML for a deleted edition in admin view.

        Parameters
        ----------
        edition: AttrDict
            An edition record
        pDeleted: boolean
            Whether the parent project is currently deleted.
            We do not allow undelete actions of editions if their parents are
            still deleted.

        Returns
        -------
        string
            The HTML
        """
        Settings = self.Settings
        delayUndel = Settings.sweeper.delayUndel

        H = self.H
        title = edition.title or H.i("no title")
        eDeletedBy = edition.get(MDELBY, None) or "unknown"
        eDeletedTm = edition.get(MDELDT, "2000-01-01T00:00:00Z")
        eDeletedDt = dateOnly(eDeletedTm)
        eRemainingDays = amountTogo(delayUndel, eDeletedTm, iso=True)

        eTitle = H.span(title, cls="etitle")
        eStatus = H.span(f"on {eDeletedDt} by {eDeletedBy}", cls="pestatus warning")
        undelete = "" if pDeleted else "undelete"
        disabled = "disabled" if pDeleted else ""
        eId = edition._id
        eControl = H.span(
            f"undelete ({eRemainingDays:4.2f} days left)",
            url=f"edition/{eId}/undelete",
            title=f"undelete edition {eId}",
            cls=f"button medium {undelete} {disabled}",
        )

        return H.div(
            [H.div(f"{eControl} {eTitle} {eStatus}", cls="ehead")],
            cls="eentry",
        )

    def wrapUsers(
        self, itemRoles, workIndicator=False, table=None, record=None, theseUsers=None
    ):
        """Generate HTML for a list of users.

        It is dependent on the value of table/record whether it is about the users
        of a specific project/edition or the site-wide users.

        Parameters
        ----------
        itemRoles: dict
            Dictionary keyed by the possible roles and valued by the description
            of that role.
        workIndicator: boolean, optional False
            Whether to mention the number of projects and editions the user is
            involved in.
        table: string, optional None
            Either `project` or `edition`, indicates what users we are listing:
            related to a project or to an edition.
        record: AttrDict, optional None
            If `table` is passed and not None, here is the specific project or edition
            whose users should be listed.
        theseUsers: dict, optional None
            If table/record is not specified, you can specify users here.
            If this parameter is also None, then all users in the system are taken.
            Otherwise, you have to specify a dict, keyed by user eppns and valued by
            tuples consisting of a user record and a role.

        Returns
        -------
        string
            The HTML
        """
        H = self.H
        Settings = self.Settings
        runProd = Settings.runProd
        users = self.users
        inPower = self.inPower
        doingAllUsers = theseUsers is None

        if record is None:
            if theseUsers is None:
                theseUsers = {
                    u: (uRecord, uRecord.role) for (u, uRecord) in users.items()
                }
        else:
            theseUsers = record.users

        recordId = record._id if record else None
        wrapped = []

        if theseUsers is None:
            rolesRep = ", ".join(f"{itemRoles[r]}s" for r in itemRoles if r)
            tableRep = table if table else "site"
            wrapped.append(f"No {rolesRep} for this {tableRep}")

        else:
            for u, (uRecord, role) in sorted(
                theseUsers.items(),
                key=lambda x: (x[1][1], x[1][0].nickname or "", x[0] or ""),
            ):
                (editable, otherRoles) = self.authUser(u, table=table, record=record)
                wrapped.append(
                    self.wrapUser(
                        u,
                        uRecord,
                        role,
                        editable,
                        otherRoles,
                        itemRoles,
                        table,
                        recordId,
                        workIndicator,
                    )
                )

        (editable, otherRoles) = self.authUser(None, table=table, record=record)

        if editable:
            wrapped.append(
                self.wrapLinkUser(otherRoles - {None}, itemRoles, table, recordId)
            )

        if record is None and not runProd and inPower and doingAllUsers:
            wrapped.append(
                H.div(
                    H.content(
                        H.input(
                            "", "text", placeholder="new test user name", cls="narrow"
                        ),
                        H.iconx(
                            "create",
                            title="add a new test user",
                            href="/user/create",
                            cls="button small",
                        ),
                    ),
                    cls="createuser",
                )
            )

        return "".join(wrapped)

    def wrapLinkUser(self, roles, itemRoles, table, recordId):
        """Generate HTML to add a user in a specified role.

        Parameters
        ----------
        roles: string | void
            The choice of roles that a new user can get.
        itemRoles: dict
            Dictionary keyed by the possible roles and valued by the description
            of that role.
        table: string
            Either None or `project` or `edition`, indicates to what we are linking
            users: site-wide users or users related to a project or to an edition.
        recordId: ObjectId or None
            Either None or the id of a project or edition, corresponding to the
            `table` parameter.

        Returns
        -------
        string
            The HTML
        """
        H = self.H
        users = self.users

        linkButton = H.actionButton("edit_link")
        cancelButton = H.actionButton("edit_cancel")
        saveButton = H.actionButton("edit_save")
        messages = H.div("", cls="editmsgs")

        roleChoice = H.div(
            [H.div(itemRoles[r], cls="role button", role=r) for r in roles],
            cls="chooseroles",
        )
        userChoice = H.div(
            [
                H.div(uRecord.nickname, cls="user button", user=u)
                for (u, uRecord) in users.items()
            ],
            cls="chooseusers",
        )

        return H.div(
            [linkButton, cancelButton, saveButton, messages, roleChoice, userChoice],
            cls="linkusers",
            saveurl=f"/link/user/{table}/{recordId}",
        )

    def wrapUser(
        self,
        u,
        uRecord,
        role,
        editable,
        otherRoles,
        itemRoles,
        table,
        recordId,
        workIndicator,
    ):
        """Generate HTML for a single user and his role.

        Parameters
        ----------
        u: string
            The eppn of the user.
        uRecord: AttrDict
            The user record.
        role: string | void
            The actual role of the user, or None if the user has no role.
        editable: boolean
            Whether the current user may change the role of this user.
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
        workIndicator: boolean
            Whether to mention the number of projects and editions the user is
            involved in.

        Returns
        -------
        string
            The HTML
        """
        H = self.H
        Content = self.Content

        if workIndicator:
            user = uRecord.user
            (nProjects, nEditions) = Content.getUserWork(user)
            indicator = [
                H.span(f"projects: {nProjects},", cls="dreport"),
                H.nbsp,
                H.span(f"editions: {nEditions}", cls="dreport"),
            ]
            if nProjects == 0 and nEditions == 0 and role == "user":
                indicator.extend(
                    [
                        H.nbsp,
                        H.iconx(
                            "delete",
                            title="delete this user",
                            href=f"/user/delete/{user}",
                            cls="button small",
                        ),
                    ]
                )
        else:
            indicator = []

        return H.div(
            [
                H.div(uRecord.nickname, cls="user"),
                *self.wrapRole(
                    u, itemRoles, role, editable, otherRoles, table, recordId
                ),
                *indicator,
            ],
            cls="userroles",
        )

    def wrapRole(self, u, itemRoles, role, editable, otherRoles, table, recordId):
        """Generate HTML for a role.

        This may or may not be an editable widget, depending on whether there
        are options to choose from.

        Site-wide users have a single site-wide role. But project/edition users
        can have zero or one role wrt projects/editions.

        Parameters
        ----------
        u: string
            The eppn of the user.
        itemRoles: dict
            Dictionary keyed by the possible roles and valued by the description
            of that role.
        role: string | void
            The actual role of the user, or None if the user has no role.
        editable: boolean
            Whether the current user may change the role of this user.
        otherRoles: frozenset
            The other roles that the target user may be assigned by the current user.
        table: string
            Either None or `project` or `edition`, indicates what users we
            are listing: site-wide users or users related to a project or to an edition.
        recordId: ObjectId or None
            Either None or the id of a project or edition, corresponding to the
            `table` parameter.

        Returns
        -------
        string
            The HTML
        """
        roleRank = self.roleRank
        H = self.H

        actualRole = H.div(itemRoles[role], role=role, cls="role")
        recordRep = f"/{recordId}" if table else ""

        allRoles = sorted({role} | otherRoles, key=roleRank)

        if editable:
            saveUrl = f"/save/role/{u}/{table or ''}{recordRep}"
            updateButton = H.actionButton("edit_assign")
            cancelButton = H.actionButton("edit_cancel")
            saveButton = H.actionButton("edit_save")
            messages = H.div("", cls="editmsgs")

            widget = H.div(
                [
                    updateButton,
                    saveButton,
                    cancelButton,
                    messages,
                    H.div(
                        [
                            H.div(
                                itemRoles[r],
                                cls="role button " + ("on" if r == role else ""),
                                role=r,
                            )
                            for r in allRoles
                        ],
                        cls="edit roles",
                        saveurl=saveUrl,
                        origvalue=role,
                    ),
                ],
                cls="editroles",
            )
        else:
            widget = ""

        return [actualRole, widget]

    # retrieval and action functions -- PUB

    def pubStatus(self):
        """Get the publication status.

        Only allowed for admins and roots.

        Returns
        -------
        dict
            With key `status`: whether the retrieval of the value succeeded;
            with key `messages`: the messages if the retrieval did not succeed;
            with key `value`: the value itself.
        """
        Content = self.Content
        inPower = self.inPower

        if inPower:
            (table, siteId, site) = Content.relevant()
            status = True
            messages = []
            value = site.processing or False
        else:
            status = False
            messages = ["error", "You are not allowed to retrieve this value"]
            value = None

        return dict(status=status, messages=messages, value=value)

    def pubTerminate(self):
        """Set the publication status to false

        Only allowed for admins and roots.

        This is meant for cases where a publication action has failed without
        restoring the flag that indicates that the site is publishing.
        It should not happen, but then: it might ...

        Returns
        -------
        dict
            With key `status`: whether the setting of the value succeeded;
            with key `messages`: the messages if the setting did not succeed;
        """
        Content = self.Content
        Mongo = self.Mongo
        inPower = self.inPower
        uName = self.uName

        if inPower:
            (table, siteId, site) = Content.relevant()

            if site.processing:
                Mongo.updateRecord(
                    "site",
                    dict(_id=site._id),
                    dict(processing=False, lastPublished=isonow()),
                    uName,
                )
            status = True
            messages = []
        else:
            status = False
            messages = ["error", "You are not allowed to set this value"]

        return dict(status=status, messages=messages)

    # retrieval and action functions -- KEYWORD

    def saveKeyword(self):
        """Saves a keyword.

        All keywords for all lists are stored in the table *keyword*. The keyword
        itself is stored in field *value*, and the name of the keyword list is stored
        in the field *name*.

        The name and value are given by the request.

        Returns
        -------
        dict
            Contains the following keys:

            * `status`: whether the save action was successful
            * `messages`: messages issued during the process
        """
        Auth = self.Auth
        Mongo = self.Mongo
        Content = self.Content

        permitted = Auth.inPower()[0]

        if not permitted:
            return dict(
                stat=False, messages=[["error", "adding a keyword is not allowed"]]
            )

        keywords = Content.getKeywords()
        specs = json.loads(requestData())
        name = specs["name"]
        value = specs["value"]

        if name not in keywords:
            return dict(
                stat=False, messages=[["error", f"unknown keyword list '{name}'"]]
            )

        keywords = keywords[name]

        if value in keywords:
            return dict(
                stat=False,
                messages=[
                    ["warning", f"keyword list '{name}' already contains '{value}'"]
                ],
            )

        if normalize(value) in {normalize(val) for val in keywords}:
            return dict(
                stat=False,
                messages=[
                    [
                        "warning",
                        f"keyword list '{name}' already contains "
                        f"a variant of '{value}'",
                    ]
                ],
            )

        Mongo.insertRecord("keyword", dict(name=name, value=value))

        self.update()
        return dict(stat=True, messages=[], updated=self.wrap())

    def deleteKeyword(self):
        """Deletes a keyword.

        The name and value are given by the request.

        Returns
        -------
        dict
            Contains the following keys:

            * `status`: whether the save action was successful
            * `messages`: messages issued during the process
        """
        Auth = self.Auth
        Mongo = self.Mongo
        Content = self.Content
        inPower = self.inPower

        if not inPower:
            return dict(
                stat=False, messages=[["error", "deleting a keyword is not allowed"]]
            )

        User = Auth.myDetails()
        uName = User.nickname

        keywords = Content.getKeywords()
        specs = json.loads(requestData())
        name = specs["name"]
        value = specs["value"]

        if name not in keywords:
            return dict(
                stat=False, messages=[["error", f"unknown keyword list '{name}'"]]
            )

        keywords = keywords[name]

        if value not in keywords:
            return dict(
                stat=False,
                messages=[
                    ["warning", f"keyword list '{name}' did not contain '{value}'"]
                ],
            )

        occs = keywords[value]

        if occs:
            return dict(
                stat=False,
                messages=[["error", f"keyword '{name}':'{value}' is used {occs} x"]],
            )

        good = Mongo.deleteRecord("keyword", dict(name=name, value=value), uName)
        messages = [] if good else [["warning", "no keyword has been deleted"]]

        self.update()
        return dict(stat=good, messages=messages, updated=self.wrap())

    # retrieval and action functions -- USERS and ROLES

    def saveRole(self, u, newRole, table=None, recordId=None):
        """Saves a role into a user or cross table record.

        It will be checked whether the new role is valid, and whether the user
        has permission to perform this role assignment.

        Parameters
        ----------
        u: string
            The eppn of the user.
        newRole: string | void
            The new role for the target user. None means: the target user will
            lose his role.
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
            * `messages`: list of messages for the user,
            * `updated`: new content for the user managment div.
        """
        Mongo = self.Mongo
        siteRoles = self.siteRoles
        projectRoles = self.projectRoles
        editionRoles = self.editionRoles
        itemRoles = (
            siteRoles
            if table is None
            else projectRoles if table == "project" else editionRoles
        )
        newRoleRep = itemRoles[newRole]

        (editable, otherRoles) = self.authUser(u, table=table, record=recordId)
        if not editable:
            return dict(stat=False, messages=[["error", "update not allowed"]])

        if newRole not in otherRoles:
            return dict(stat=False, messages=[["error", f"invalid role: {newRoleRep}"]])

        msg = ""

        uName = self.uName

        if table is None:
            result = Mongo.updateRecord("user", dict(user=u), dict(role=newRole), uName)
        else:
            (recordId, record) = Mongo.get(table, recordId)

            if recordId is None:
                return dict(
                    stat=False, messages=[["error", f"{table} record does not exist"]]
                )

            criteria = {"user": u, f"{table}Id": recordId}

            if newRole is None:
                result = Mongo.deleteRecord(f"{table}User", criteria, uName)

                if not result:
                    msg = f"could not unlink this user from the {table}"
            else:
                result = Mongo.updateRecord(
                    f"{table}User", criteria, dict(role=newRole), uName
                )
                if not result:
                    msg = (
                        "could not change this user's role to "
                        f"{newRoleRep} wrt. the {table}"
                    )

        if not result:
            return dict(stat=False, messages=[["error", msg]])

        self.update()
        return dict(stat=True, messages=[], updated=self.wrap())

    def linkUser(self, u, newRole, table, recordId):
        """Links a user in certain role to a project/edition record.

        It will be checked whether the new role is valid, and whether the user
        has permission to perform this role assignment.

        If the user is already linked to that project/edition, his role
        will be updated, otherwise a new link will be created.

        Parameters
        ----------
        u: string
            The eppn of the target user.
        newRole: string
            The new role for the target user.
        table: string
            Either `project` or `edition`.
        recordId: ObjectId
            The id of a project or edition, corresponding to the
            `table` parameter.

        Returns
        -------
        dict
            with keys:

            * `stat`: indicates whether the save may proceed;
            * `messages`: list of messages for the user,
            * `updated`: new content for the user managment div.
        """
        Mongo = self.Mongo
        uName = self.uName
        siteRoles = self.siteRoles
        projectRoles = self.projectRoles
        editionRoles = self.editionRoles

        itemRoles = (
            siteRoles
            if table is None
            else projectRoles if table == "edition" else editionRoles
        )
        newRoleRep = itemRoles[newRole]

        (editable, otherRoles) = self.authUser(None, table=table, record=recordId)
        if not editable:
            return dict(stat=False, messages=[["error", "update not allowed"]])

        if newRole not in otherRoles:
            return dict(stat=False, messages=[["error", f"invalid role: {newRoleRep}"]])

        (recordId, record) = Mongo.get(table, recordId)

        if recordId is None:
            return dict(stat=False, messages=[["error", "record does not exist"]])

        criteria = {"user": u, f"{table}Id": recordId}
        crossRecord = Mongo.getRecord(f"{table}User", criteria, warn=False)

        msg = ""

        if crossRecord:
            result = Mongo.updateRecord(
                f"{table}User", criteria, dict(role=newRole), uName
            )

            if not result:
                msg = (
                    "could not change this user's role to "
                    f"{newRoleRep} wrt. the {table}"
                )
        else:
            fields = {"user": u, f"{table}Id": recordId, "role": newRole}
            result = Mongo.insertRecord(f"{table}User", fields)
            if not result:
                msg = f"could not link this user to {table} as {newRoleRep}"

        if not result:
            return dict(stat=False, messages=[["error", msg]])

        self.update()
        return dict(stat=True, messages=[], updated=self.wrap())

    def createUser(self, user):
        """Creates new user.

        This action is only valid in test, pilot or custom mode.
        The current user must be an admin or root.

        Parameters
        ----------
        user: string
            The username of the user.
            This should be different from the usernames of existing users.
            The name may only contain the ASCII digits and lower case letters,
            plus dash, dot, and underscore.

            Spaces will be replaced by dots; all other illegal characters by
            underscores.

        Returns
        -------
        dict
            Contains the following keys:

            * `status`: whether the create action was successful
            * `messages`: messages issued during the process
        """
        Mongo = self.Mongo
        Settings = self.Settings
        runProd = Settings.runProd
        inPower = self.inPower

        status = True
        messages = []

        if inPower and not runProd:
            if len(user) == 0:
                status = False
                messages.append(("error", "name should not be empty"))

            else:
                uName = USERNAME_RE.sub("_", user.lower().replace(" ", "."))
                if uName != user:
                    messages.append(("warning", f"user {user} to be saved as {uName}"))

                userLong = f"{uName:0>16}"
                userInfo = dict(
                    nickname=uName,
                    user=userLong,
                    role="user",
                    isSpecial=True,
                )
                userId = Mongo.insertRecord("user", userInfo)

                if not userId:
                    status = False
                    messages.append(
                        ("error", f"could not add {uName} to the user table")
                    )
        else:
            status = False

            if not inPower:
                messages.append(("error", "adding a user needs admin privileges"))
            if runProd:
                messages.append(
                    ("error", "adding a user not allowed in production mode")
                )

        self.update()
        return dict(status=status, messages=messages, name=user)

    def deleteUser(self, user):
        """Deletes a test user.

        This action is only valid in test, pilot or custom mode.
        The current user must be an admin or root.
        The user to be deleted should be a test user, not linked to any project or
        edition.

        Parameters
        ----------
        user: string
            The username of the user.

        Returns
        -------
        dict
            Contains the following keys:

            * `status`: whether the create action was successful
            * `messages`: messages issued during the process
        """
        Auth = self.Auth
        Mongo = self.Mongo
        Settings = self.Settings
        runProd = Settings.runProd
        inPower = self.inPower
        User = Auth.myDetails()
        uName = User.nickname

        status = True
        messages = []

        if inPower and not runProd:
            if len(user) == 0:
                status = False
                messages.append(("error", "name should not be empty"))
            else:
                good = Mongo.deleteRecord(
                    "user", dict(isSpecial=True, user=user), uName
                )

                if not good:
                    status = False
                    messages.append(
                        ("error", f"could not delete {user} from the user table")
                    )
        else:
            status = False

            if not inPower:
                messages.append(("error", "deleting a user needs admin privileges"))
            if runProd:
                messages.append(
                    ("error", "deleting a user not allowed in production mode")
                )

        self.update()
        return dict(stat=status, messages=messages)

    def undeleteItem(self, table, record):
        """Deletes an item, project or edition.

        Parameters
        ----------
        table: string
            The kind of item: `project` or `edition`.
        record: string | ObjectId | AttrDict
            The item in question.

        Returns
        -------
        boolean
            Whether the deletion was successful.
        """
        Auth = self.Auth
        Mongo = self.Mongo
        Messages = self.Messages
        Content = self.Content
        inPower = self.inPower
        User = Auth.myDetails()
        uName = User.nickname

        messages = []

        (recordId, record) = Mongo.get(table, record, deleted=True)
        projectRep = f"{record.projectId}/" if table == "edition" else ""
        itemRep = f"{table} {projectRep}{recordId}"
        head = f"RESTORE (on behalf of {uName}) {itemRep}: "

        if inPower:
            if recordId is None:
                Messages.warning(logmsg=f"{head}Not found")
                messages.append(("warning", f"{table}: no such {table}"))
                return dict(stat=False, messages=messages)

            if table == "edition":
                parent = record.projectId
                (projectId, project) = Mongo.get("project", parent)

                if projectId is None:
                    Messages.error(logmsg=f"{head}Project is still deleted")
                    messages.append(
                        (
                            "error",
                            "Not allowed to restore an edition "
                            "whose parent project is still deleted",
                        )
                    )
                    return dict(stat=False, messages=messages)

            if Mongo.undeleteRecord(table, dict(_id=recordId), uName):
                Messages.info(logmsg=f"{head}restored the {table} record")
            else:
                Messages.error(logmsg=f"{head}restore of {table} record failed")
                messages.append(("error", f"could not restore this {table} record"))
                return dict(stat=False, messages=messages)

            links = Content.getLinkedCrit(table, record)
            status = True

            if links:
                for linkTable, linkCriteria in links.items():
                    (thisStatus, count) = Mongo.undeleteRecords(
                        linkTable, linkCriteria, uName
                    )

                    if not thisStatus:
                        status = False
                        Messages.error(
                            logmsg=(
                                f"Cannot restore link records from "
                                f"{linkTable} with {linkCriteria}"
                            )
                        )
                        messages.append(
                            ("error", f"could not restore linked {linkTable} record")
                        )
                    else:
                        Messages.info(
                            logmsg=(
                                f"{head}Restored {count} link records "
                                f"from {linkTable}"
                            )
                        )
                        messages.append(
                            ("info", f"Restored {count} link records from {linkTable}")
                        )

            if not status:
                return dict(stat=False, messages=messages)

            (status, theseMessages) = self.undeleteItemFiles(
                table, record, recordId, uName
            )
            messages.extend(theseMessages)

            self.update()
            updated = self.wrap()

            if status:
                Messages.info(logmsg=f"{head}Success")
                return dict(stat=True, messages=messages, updated=updated)
            else:
                Messages.info(logmsg=f"{head}Failed")
                return dict(stat=False, messages=messages, updated=updated)

        else:
            Messages.error(logmsg=f"{head}Not permitted")
            messages.append(("error", f"restoring a {table} needs admin privileges"))
            return dict(stat=False, messages=messages)

    def undeleteItemFiles(self, table, record, recordId, uName):
        Messages = self.Messages
        Settings = self.Settings
        workingDir = Settings.workingDir

        itemDirTail = f"{table}/{recordId}"

        if table == "project":
            itemDirTail = f"{table}/{recordId}"
        elif table == "edition":
            projectId = record.projectId
            itemDirTail = f"/project/{projectId}/{table}/{recordId}"

        itemDir = f"{workingDir}/{itemDirTail}"

        messages = []
        status = True

        head = f"RESTORE DIRECTORY (on behalf of {uName}) {itemDirTail}: "

        if dirExists(itemDir):
            markFile = f"{itemDir}/{FDEL}"

            if fileExists(markFile):
                fileRemove(markFile)
                Messages.info(logmsg=f"{head}by removing {FDEL}")
                messages.append(
                    ("good", f"Undeleted the {table} directory on the file system")
                )
            else:
                Messages.warning(logmsg=f"{head}was not marked as deleted!")
                messages.append(
                    ("warning", f"The {table} directory existed in a non-deleted state")
                )
        else:
            status = True
            Messages.warning(logmsg=f"{head}does not exist on the file system!")
            messages.append(("warning", f"The {table} directory does not exist"))
        return (status, messages)

    # LOGISTICS functions

    def update(self):
        """Reread the tables of users, projects, editions.

        Typically needed when you have used an admin function to perform
        a user administration action.

        This may change the permissions and hence the visibility of projects
        and editions.
        It also changes the possible user management actions in the future.
        """
        Settings = self.Settings
        delayUndel = Settings.sweeper.delayUndel

        Mongo = self.Mongo
        Auth = self.Auth
        Auth.identify()
        User = Auth.myDetails()
        user = User.user
        uName = User.nickname

        self.User = User
        self.user = user
        self.uName = uName

        (self.inPower, self.myRole) = Auth.inPower()

        if not user:
            return

        siteRecord = Mongo.getRecord("site", {})
        userList = Mongo.getList("user", {}, sort="nickname")
        projectList = Mongo.getList("project", {}, sort="title")
        projectList2 = Mongo.getList("project", {}, sort="title")
        editionList = Mongo.getList("edition", {}, sort="title")
        projectLinks = Mongo.getList("projectUser", {})
        editionLinks = Mongo.getList("editionUser", {})

        delProjectListAll = Mongo.getList("project", {}, deleted=True, sort="title")
        delEditionListAll = Mongo.getList("edition", {}, deleted=True, sort="title")

        delProjectList = [
            r for r in delProjectListAll if lessAgo(delayUndel, r.get(MDELDT, None))
        ]
        delProjectSet = {r._id for r in delProjectList}
        delEditionList = [
            r for r in delEditionListAll if lessAgo(delayUndel, r.get(MDELDT, None))
        ]

        users = AttrDict({x.user: x for x in userList})
        projects = AttrDict({x._id: x for x in projectList})
        projects2 = AttrDict({x._id: x for x in projectList2})
        editions = AttrDict({x._id: x for x in editionList})

        delProjects = AttrDict({x._id: x for x in delProjectList} | projects2)

        myIds = AttrDict()

        self.site = siteRecord
        self.users = users
        self.projects = projects
        self.editions = editions
        self.delProjects = delProjects
        self.myIds = myIds

        for eRecord in editionList:
            eId = eRecord._id
            pId = eRecord.projectId
            projects[pId].setdefault("editions", {})[eId] = eRecord

        for eRecord in delEditionList:
            eId = eRecord._id
            pId = eRecord.projectId
            delProjects[pId].setdefault("editions", {})[eId] = eRecord

        # delete projects that are not themselves deleted and have no deleted editions

        toBeRemoved = []

        for pID, pRecord in delProjects.items():
            if pID in delProjectSet:
                continue

            pEditions = pRecord.get("editions", {})

            if len(pEditions) == 0:
                toBeRemoved.append(pID)

        for pID in toBeRemoved:
            del delProjects[pID]

        for pLink in projectLinks:
            role = pLink.role

            if role:
                u = pLink.user
                uRecord = users[u]

                if uRecord is None:
                    continue

                pId = pLink.projectId
                pRecord = projects[pId]

                if pRecord is None:
                    continue

                pRecord.setdefault("users", AttrDict())

                if user == u:
                    myIds.setdefault("project", set()).add(pId)

                    for eId in pRecord.editions or []:
                        myIds.setdefault("edition", set()).add(eId)

                pRecord.setdefault("users", AttrDict())[u] = (uRecord, role)

        for eLink in editionLinks:
            role = eLink.role

            if role:
                u = eLink.user
                uRecord = users[u]

                if uRecord is None:
                    continue

                eId = eLink.editionId
                eRecord = editions[eId]

                if eRecord is None:
                    continue

                pId = eRecord.projectId

                if user == u:
                    myIds.setdefault("project", set()).add(pId)
                    myIds.setdefault("edition", set()).add(eId)

                eRecord.setdefault("users", AttrDict())[u] = (uRecord, role)

    def authUser(self, otherUser, table=None, record=None):
        """Check whether a user may change the role of another user.

        The questions are:

        "which *other* site-wide roles can the current user assign to the other
        user?" (when no table or record is given).

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
        *   Users may not promote themselves unless ... see later.
        *   Users may have zero or one project/edition-scoped role per
            project/edition
        *   When assigning new site-wide or project/edition-scoped roles, these
            roles must be valid roles for that scope.
        *   When assigning a new site-wide role, None is not one
            of the possible new roles:
            you cannot change the status of an authenticated user to "not
            logged in".
        *   When assigning project/edition scoped roles, removing such a
            role from a user for a certain project/edition means that the
            other user is removed from that project or edition.
        *   Roles are ranked in power. Users with a higher role are also authorised
            to all things for which lower roles give authorisation.

            The site-wide roles are ranked as:

            ```
            root - admin - user - guest - not logged in
            ```

            The project/edition roles are ranked as:

            ```
            (project) organiser - (edition) editor - (edition) reviewer
            ```

            Site-wide power does not automatically carry over to project/edition-scoped
            power.

        *   Users cannot promote or demote people that are currently as powerful
            as themselves.
        *   In normal cases there is exactly one root, but:
            *   If a situation occurs that there is no root and no admin, any authenticated
                user my grab the role of admin.
            *   If a situation occurs that there is no root, any admin may
                grab the role of root.
        *   Roots may appoint admins.
        *   Roots and admins may change site-wide roles.
        *   Roots and admins may appoint project organisers, but may not assign
            edition-scoped roles.
        *   Project organisers may appoint edition editors and reviewers.
        *   Edition editors may appoint edition reviewers.
        *   However, roots and admins may also be project organisers and
            edition editors for some projects and some editions.
        *   Normal users and guests can not administer site-wide roles.
        *   Guests can not be put in project/edition-scoped roles.

        Parameters
        ----------
        otherUser: string | void
            the other user as string (eppn)
            If None, the question is: what are the roles in which another
            user may be put wrt to this project/edition?
        table: string, optional None
            the relevant table: `project` or `edition`;
            this is the table in which the record sits
            relative to which the other user will be assigned a role.
            If None, the role to be assigned is a site wide role.
        record: ObjectId | AttrDict, optional None
            the relevant record;
            it is the record relative to which the other user will be
            assigned another role.
            If None, the role to be assigned is a site wide role.

        Returns
        -------
        boolean, frozenset
            The boolean indicates whether the current user may modify the role
            of the target user.

            The frozenset is the set of assignable roles to the other user
            by the current user with respect to the given table and record or site-wide.

            If the boolean is false, the frozenset is empty.
            But if the frozenset is empty it might be the case that the current
            user is allowed to remove the role of the target user.
        """
        myRole = self.myRole
        uName = self.uName

        if not uName or myRole in {None, "guest"}:
            return False, frozenset()

        user = self.user
        users = self.users
        nRoots = sum(1 for u in users.values() if u.role == "root")
        nAdmins = sum(1 for u in users.values() if u.role == "admin")
        iAmInPower = self.inPower
        otherUserRecord = users[otherUser] or AttrDict()
        otherRole = otherUserRecord.role
        otherIsInPower = otherRole in {"admin", "root"}

        nope = (False, frozenset())

        # side-wide assignments

        if table is None or record is None:
            # nobody can add site-wide users

            if otherUser is None:
                return nope

            siteRolesSet = self.siteRolesSet

            # if there are no admins and no roots,
            #   any admin may promote himself to root
            #   if there are no admins
            #     any authenticated user may promote himself to admin

            remainingRoles = frozenset(siteRolesSet - {None, otherRole})

            if nRoots == 0:
                if user == otherUser:
                    if nAdmins == 0:
                        if myRole == "user":
                            fineAdmin = (True, frozenset(["admin"]) | remainingRoles)
                            return fineAdmin
                    else:
                        if myRole == "admin":
                            fineRoot = (True, frozenset(["root"]) | remainingRoles)
                            return fineRoot

            # from here on, only admins and roots can change roles
            if not iAmInPower:
                return nope

            fine = (True, remainingRoles)

            # root is all powerful, only limited by other roots
            if myRole == "root":
                if user == otherUser or otherRole != "root":
                    return fine
                else:
                    return nope

            # from here on, myRole is admin, so "root" cannot be assigned

            remainingRoles = frozenset(remainingRoles - {"root"})
            fine = (True, remainingRoles)
            fineNoAdmin = (True, remainingRoles - {"admin"})

            # when the user changes his own role: can only demote
            if user == otherUser:
                return fineNoAdmin

            # people cannot affect other more or equally powerful people
            if otherIsInPower:
                return nope

            # people cannot promote others beyond their own level
            return fine

        # not a project or edition, or not a real record: Not allowed!

        if table not in {"project", "edition"} or record is None:
            return nope

        # project-scoped assignments

        projectRolesSet = self.projectRolesSet
        fine = (True, projectRolesSet)

        if table == "project":
            # only admins and roots can assign a project-scoped role
            if not iAmInPower:
                return nope

            # remaining cases are allowed
            return fine

        # remaining case: only edition scoped.

        if table != "edition":
            return nope

        # edition-scoped assignments

        Mongo = self.Mongo
        (recordId, record) = Mongo.get(table, record)

        if recordId is None:
            return nope

        projects = self.projects
        editionRolesSet = self.editionRolesSet

        # check whether the role is an edition-scoped role
        pRecord = projects[record.projectId]
        pUsers = pRecord.users or AttrDict()
        eUsers = record.users or AttrDict()

        otherProjectRole = (pUsers[otherUser] or (None, None))[1]
        otherEditionRole = (eUsers[otherUser] or (None, None))[1]

        myProjectRole = (pUsers[user] or (None, None))[1]
        myEditionRole = (eUsers[user] or (None, None))[1]

        # only organisers of the parent project can (un)assign an
        # edition editor

        iAmOrganiser = "organiser" == myProjectRole
        otherIsOrganiser = "organiser" == otherProjectRole
        iAmEditor = "editor" == myEditionRole
        otherIsEditor = "editor" == otherEditionRole

        # what I can do to myself

        fine = (True, editionRolesSet)
        fineNoEditor = (True, editionRolesSet - {"editor"})

        if user == otherUser:
            if iAmOrganiser or iAmEditor:
                return fine
            return nope

        # what I can do to others

        if otherUser is None:
            if iAmOrganiser:
                return fine
            if iAmEditor:
                return fineNoEditor

        if otherIsOrganiser:
            return nope

        if otherIsEditor:
            if iAmOrganiser:
                return fine
            return nope

        if iAmOrganiser:
            return fine
        if iAmEditor:
            return fineNoEditor

        return nope
