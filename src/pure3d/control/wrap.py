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
        representations = Settings.representations
        css = Settings.css
        Auth = self.Auth
        Content = self.Content

        wrapped = []
        wrapped.append(
            H.p(self.contentButton("site", site, "create", insertTable="project"))
        )

        for project in projects:
            projectId = project._id
            permitted = Auth.authorise("project", project, action="read")
            if not permitted:
                continue

            title = project.title
            if not title:
                title = H("no title")
            stat = project.isVisible
            status = representations.isVisible[stat]
            statusCls = css.isVisible[stat]

            projectUrl = f"/project/{projectId}"
            button = self.contentButton("project", project, "delete")
            visual = Content.getUpload(project, "iconProject")
            caption = self.getCaption(
                visual, title, status, statusCls, button, projectUrl
            )

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
        representations = Settings.representations
        css = Settings.css
        Auth = self.Auth
        Content = self.Content

        wrapped = []

        for edition in editions:
            editionId = edition._id
            permitted = Auth.authorise("edition", record=edition, action="read")
            if not permitted:
                continue

            title = edition.title
            if not title:
                title = H("no title")
            stat = edition.isPublished
            status = representations.isPublished[stat]
            statusCls = css.isPublished[stat]

            editionUrl = f"/edition/{editionId}"
            button = self.contentButton("edition", edition, "delete")
            visual = Content.getUpload(edition, "iconEdition")
            caption = self.getCaption(
                visual, title, status, statusCls, button, editionUrl
            )
            wrapped.append(caption)

        wrapped.append(
            H.p(self.contentButton("project", project, "create", insertTable="edition"))
        )
        return H.content(*wrapped)

    def sceneMain(
        self, projectId, edition, sceneFile, viewer, version, action, sceneExists
    ):
        """Wrap the scene of an edition for the main display.

        Parameters
        ----------
        projectId: ObjectId
            The id of the project to which the edition belongs.
        edition: AttrDict
            The edition record of the scene.
        viewer: string
            The viewer that will be used.
        version: string
            The version of the chosen viewer that will be used.
        action: string
            The mode in which the viewer should be opened.
        sceneExists: boolean
            Whether the scen file exists

        Returns
        -------
        string
            The HTML of the scene
        """
        Settings = self.Settings
        H = Settings.H
        Auth = self.Auth
        Viewers = self.Viewers

        actions = Auth.authorise("edition", edition)
        if "read" not in actions:
            return ""

        wrapped = []

        titleText = H.span(sceneFile, cls="entrytitle")
        button = self.contentButton("edition", edition, "delete")

        (frame, buttons) = Viewers.getFrame(
            edition, actions, viewer, version, action, sceneExists
        )
        title = H.span(titleText, cls="entrytitle")
        content = f"""{frame}{title}{buttons}"""
        caption = self.wrapCaption(content, button, None, active=True)

        wrapped.append(caption)
        return H.content(*wrapped)

    def getCaption(self, visual, titleText, status, statusCls, button, url):
        """Produces a caption of a project or edition.

        Parameters
        ----------
        visual: string
            A link to an image to display in the caption.
        titleText: string
            The text on the caption.
        status: string
            The status of the project/edition: visible/hidden/published/in progress.
            The exact names
        statusCls: string
            The CSS class corresponding to `status`
        button: string
            Control for a certain action, or empty if the user is not authorised.
        url: string
            The url to navigate to if the user clicks the caption.
        """
        Settings = self.Settings
        H = Settings.H

        title = H.span(titleText, cls="entrytitle")
        content = H.a(f"{visual}{title}", url, cls="entry")
        statusBadge = H.div(status, cls=f"pestatus {statusCls}")

        return self.wrapCaption(content, statusBadge, button)

    def wrapCaption(self, content, statusBadge, button, active=False):
        """Assembles a caption from building blocks."""
        Settings = self.Settings
        H = Settings.H

        activeCls = "active" if active else ""
        rest = []
        if statusBadge is not None:
            rest.append(statusBadge)
        rest.append(button)

        return H.div(
            [H.div(content, cls=f"caption {activeCls}"), *rest], cls="captioncontent"
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

        can = "Cannot " if disable else ""
        cls = "disabled " if disable else ""

        if action == "create":
            href = f"/{table}/{recordId}/{insertTable}/create" if href is None else href
            tip = f"{name} new {insertTable}"
        else:
            href = f"/{table}/{recordId}{keyRepUrl}/{action}" if href is None else href
            tip = f"{can}{name}{keyRepTip} this {table}"

        if disable:
            href = None

        fullCls = f"button small {cls}"
        return H.iconx(action, href=href, title=tip, cls=fullCls) + report
