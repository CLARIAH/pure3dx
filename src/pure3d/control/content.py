from flask import jsonify
from control.generic import AttrDict
from control.files import fileExists
from control.datamodel import Datamodel
from control.flask import data


class Content(Datamodel):
    def __init__(self, Settings, Viewers, Messages, Mongo):
        """Retrieving content from database and file system.

        This class has methods to retrieve various pieces of content
        from the data sources, and hand it over to the `control.pages.Pages`
        class that will compose a response out of it.

        It is instantiated by a singleton object.

        Parameters
        ----------
        Settings: AttrDict
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Viewers: object
            Singleton instance of `control.viewers.Viewers`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        Mongo: object
            Singleton instance of `control.mongo.Mongo`.
        """
        super().__init__(Settings, Messages, Mongo)
        self.Viewers = Viewers

    def addAuth(self, Auth):
        """Give this object a handle to the Auth object.

        Because of cyclic dependencies some objects require to be given
        a handle to Auth after their initialization.
        """
        self.Auth = Auth

    def getSurprise(self):
        """Get the data that belongs to the surprise-me functionality."""
        Settings = self.Settings
        H = Settings.H
        return H.h(2, "You will be surprised!")

    def getProjects(self):
        """Get the list of all projects.

        Well, the list of all projects visible to the current user.
        Unpublished projects are only visible to users that belong to that project.

        Visible projects are each displayed by means of an icon and a title.
        Both link to a landing page for the project.

        Returns
        -------
        string
            A list of captions of the projects,
            wrapped in a HTML string.
        """
        Settings = self.Settings
        H = Settings.H
        Mongo = self.Mongo
        Auth = self.Auth

        (table, recordId, record) = self.relevant()

        wrapped = []
        wrapped.append(self.actionButton(table, record, "create"))

        for project in Mongo.getList("project"):
            projectId = project._id
            permitted = Auth.authorise("project", record=project, action="read")
            if not permitted:
                continue

            title = project.title

            projectUrl = f"/project/{projectId}"
            button = self.actionButton("project", project, "delete")
            visual = self.getUpload(project, "iconProject")
            caption = self.getCaption(visual, title, button, projectUrl)

            wrapped.append(caption)

        return H.content(*wrapped)

    def insertProject(self):
        Mongo = self.Mongo
        Auth = self.Auth

        permitted = Auth.authorise("project")
        if not permitted:
            return None

        User = Auth.myDetails()
        user = User.sub
        name = User.nickname

        title = "Project without title"

        dcMeta = dict(
            title=title,
            description=dict(abstract="No intro", description="No description"),
            creator=name,
        )
        projectId = Mongo.insertRecord("project", title=title, meta=dict(dc=dcMeta))
        Mongo.insertRecord(
            "projectUser",
            projectId=projectId,
            user=user,
            role="editor",
        )
        return projectId

    def getEditions(self, project):
        """Get the list of the editions of a project.

        Well, only if the project is visible to the current user.
        See `Content.getProjects()`.

        Editions are each displayed by means of an icon and a title.
        Both link to a landing page for the edition.

        Parameters
        ----------
        project: string | ObjectId | AttrDict
            The project in question.

        Returns
        -------
        string
            A list of captions of the editions of the project,
            wrapped in a HTML string.
        """
        Settings = self.Settings
        H = Settings.H
        Mongo = self.Mongo
        Auth = self.Auth

        wrapped = []

        (projectId, project) = Mongo.get("project", project)

        for edition in Mongo.getList("edition", projectId=projectId):
            editionId = edition._id
            permitted = Auth.authorise("edition", record=edition, action="read")
            if not permitted:
                continue

            title = edition.title

            editionUrl = f"/edition/{editionId}"
            button = self.actionButton("edition", edition, "delete")
            visual = self.getUpload(edition, "iconEdition")
            caption = self.getCaption(visual, title, button, editionUrl)
            wrapped.append(caption)

        wrapped.append(self.actionButton("project", project, "create"))
        return H.content(*wrapped)

    def insertEdition(self, project):
        Mongo = self.Mongo
        Auth = self.Auth

        (projectId, project) = Mongo.get("project", project)

        permitted = Auth.authorise("edition", project=project)
        if not permitted:
            return None

        User = Auth.myDetails()
        name = User.nickname

        title = "Edition without title"

        dcMeta = dict(
            title=title,
            description=dict(
                abstract="No intro",
                description="No description",
                provenance="No sources",
            ),
            creator=name,
        )
        editionId = Mongo.insertRecord(
            "edition", title=title, projectId=projectId, meta=dict(dc=dcMeta)
        )
        return editionId

    def getViewInfo(self, edition):
        """Gets viewer-related info that an edition is made with.

        Parameters
        ----------
        edition: string | ObjectId | AttrDict
            The edition record.

        Returns
        -------
        tuple of string
            * The name of the viewer
            * The name of the scene

        """
        Mongo = self.Mongo
        Viewers = self.Viewers
        viewerDefault = Viewers.viewerDefault

        (editionId, edition) = Mongo.get("edition", edition)

        editionSettings = edition.settings or AttrDict()
        authorTool = editionSettings.authorTool or AttrDict()
        viewer = authorTool.name or viewerDefault
        sceneFile = authorTool.sceneFile

        return (viewer, sceneFile)

    def getScene(
        self,
        edition,
        version=None,
        action=None,
    ):
        """Get the scene of an edition of a project.

        Well, only if the current user is authorised.

        A scene is displayed by means of an icon and a row of buttons.

        If action is not None, the scene is loaded in a specific version of the
        viewer in a specific mode (`read` or `read`).
        The edition knows which viewer to choose.

        Which version and which mode are used is determined by the parameters.
        If the parameters do not specify values, sensible defaults are chosen.

        Parameters
        ----------
        edition: string | ObjectId | AttrDict
            The edition in question.
        version: string, optional None
            The version of the chosen viewer that will be used.
            If no version or a non-existing version are specified,
            the latest existing version for that viewer will be chosen.
        action: string, optional `view`
            The mode in which the viewer should be opened.
            If the mode is `edit`, the viewer is opened in edit mode.
            All other modes lead to the viewer being opened in read-only
            mode.

        Returns
        -------
        string
            A caption of the scene of the edition,
            with possibly a frame with the 3D viewer showing the scene.
            The result is wrapped in a HTML string.
        """
        Settings = self.Settings
        H = Settings.H
        Mongo = self.Mongo
        Auth = self.Auth
        Viewers = self.Viewers

        wrapped = []

        (editionId, edition) = Mongo.get("edition", edition)
        (viewer, sceneFile) = self.getViewInfo(edition)
        actions = Auth.authorise("edition", record=edition)
        if "read" not in actions:
            return ""

        version = Viewers.check(viewer, version)

        wrapped = []

        titleText = H.span(sceneFile, cls="entrytitle")
        button = self.actionButton("edition", edition, "delete")

        (frame, buttons) = Viewers.getFrame(edition, actions, viewer, version, action)
        title = H.span(titleText, cls="entrytitle")
        content = f"""{frame}{title}{buttons}"""
        caption = self.wrapCaption(content, button, active=True)

        wrapped.append(caption)
        return H.content(*wrapped)

    def wrapCaption(self, content, button, active=False):
        Settings = self.Settings
        H = Settings.H

        activeCls = "active" if active else ""
        return H.div(
            [H.div(content, cls=f"caption {activeCls}"), button], cls="captioncontent"
        )

    def getCaption(self, visual, titleText, button, url):
        Settings = self.Settings
        H = Settings.H

        title = H.span(titleText, cls="entrytitle")
        content = H.a(f"{visual}{title}", url, cls="entry")

        return self.wrapCaption(content, button)

    def getValue(self, table, record, key, level=None, bare=False):
        """Retrieve a metadata value.

        Metadata sits in a big, potentially deeply nested dictionary of keys
        and values.
        These locations are known to the system (based on `fields.yml`).
        This function retrieves the information from those known locations.

        If a value is in fact composed of multiple values, it will be
        handled accordingly.

        Parameters
        ----------
        key: an identifier for the meta data field.
        table: string
            The relevant table.
        record: string | ObjectId | AttrDict | void
            The relevant record.
        level: string, optional None
            The heading level with which the value should be formatted.

            * `0`: No heading level
            * `None`: no formatting at all

        bare: boolean, optional None
            Get the bare value, without HTML wrapping and without buttons.

        Returns
        -------
        string
            It is assumed that the metadata value that is addressed exists.
            If not, we return the empty string.
        """
        Auth = self.Auth

        actions = Auth.authorise(table, record=record)

        if "read" not in actions:
            return None

        F = self.makeField(key)

        if bare:
            return F.bare(record)

        button = self.actionButton(table, record, "update", key=key)

        return F.formatted(table, record, level=level, button=button)

    def getValues(self, table, record, fieldSpecs):
        """Puts several pieces of metadata on the web page.

        Parameters
        ----------
        fieldSpecs: string
            `,`-separated list of fieldSpecs
        table: string
            The relevant table
        record: string | ObjectId | AttrDict | void
            The relevant record

        Returns
        -------
        string
            The join of the individual results of retrieving metadata value.
        """
        Settings = self.Settings
        H = Settings.H

        return H.content(
            self.getValue(table, record, key, level=level) or ""
            for (key, level) in (
                fieldSpec.strip().split("@", 1) for fieldSpec in fieldSpecs.split("+")
            )
        )

    def getUpload(self, record, key, fileName=None, bust=None):
        """Display the name and/or upload controls of an uploaded file.

        The user may upload model files and a scene file to an edition,
        and various png files as icons for projects, edtions, and scenes.
        Here we produce the control to do so.

        Only if the user has `update` authorisation, an upload/delete widget
        will be returned.

        Parameters
        ----------
        record: string | ObjectId | AttrDict | void
            The relevant record.
        key: an identifier for the upload field.
        fileName: string, optional None
            If present, it indicates that the uploaded file will have this prescribed
            name.
            A file name for an upload object may also have been specified in
            the datamodel configuration.
        bust: string, optional None
            If not None, the image url of the file whose name is passed in
            `bust` is made unique by adding the current time to it. That will
            bust the cache for the image, so that uploaded images replace the
            existing images.

            This is useful when this function is called to provide udated
            content for an file upload widget after it has been used to
            successfully upload a file. The file name of the uploaded
            file is known, and that is the one that gets a cache buster appended.

        Returns
        -------
        string
            The name of the file that is currently present, or the indication
            that no file is present.

            If the user has edit permission for the edition, we display
            widgets to upload a new file or to delete the existing file.
        """
        Auth = self.Auth

        uploadObject = self.getUploadObject(key, fileName=fileName)
        table = uploadObject.table

        actions = Auth.authorise(table, record=record)

        if "read" not in actions:
            return None

        F = self.makeUpload(key, fileName=fileName)

        return F.formatted(record, "update" in actions, bust=bust)

    def getViewerFile(self, path):
        """Gets a viewer-related file from the file system.

        This is about files that are part of the viewer software.

        The viewer software is located in a specific directory on the server.
        This is the viewer base.

        Parameters
        ----------
        path: string
            The path of the viewer file within viewer base.

        Returns
        -------
        string
            The full path to the viewer file, if it exists.
            Otherwise, we raise an error that will lead to a 404 response.
        """
        Settings = self.Settings
        Messages = self.Messages

        viewerDir = Settings.viewerDir

        viewerPath = f"{viewerDir}/{path}"

        if not fileExists(viewerPath):
            logmsg = f"Accessing {viewerPath}: "
            logmsg += "does not exist. "
            Messages.error(
                msg="Accessing a file",
                logmsg=logmsg,
            )

        return viewerPath

    def getData(self, table, record, path):
        """Gets a data file from the file system.

        All data files are located under a specific directory on the server.
        This is the data directory.
        Below that the files are organized by projects and editions.
        Projects and editions corresponds to records in tables in MongoDB.

        Parameters
        ----------
        path: string
            The path of the data file within site/project/edition directory
            within the data directory.
        project: string | ObjectId | AttrDict
            The id of the project in question.
        edition: string | ObjectId | AttrDict
            The id of the edition in question.

        Returns
        -------
        string
            The full path of the data file, if it exists.
            Otherwise, we raise an error that will lead to a 404 response.
        """
        Settings = self.Settings
        Messages = self.Messages
        Auth = self.Auth

        workingDir = Settings.workingDir

        (site, siteId, project, projectId, edition, editionId) = self.context(
            table, record
        )

        urlBase = (
            ""
            if project is None
            else f"project/{projectId}"
            if edition is None
            else f"project/{projectId}/edition/{editionId}"
        )
        sep = "/" if urlBase else ""
        base = f"{workingDir}{sep}{urlBase}"

        dataPath = base if path is None else f"{base}/{path}"

        (table, recordId, record) = self.relevant(project=project, edition=edition)

        permitted = Auth.authorise(table, record=record, action="read")

        fexists = fileExists(dataPath)
        if not permitted or not fexists:
            logmsg = f"Accessing {dataPath}: "
            if not permitted:
                logmsg += "not allowed. "
            if not fexists:
                logmsg += "does not exist. "
            Messages.error(
                msg=f"Accessing file {path}",
                logmsg=logmsg,
            )

        return dataPath

    def actionButton(self, table, record, action, key=None):
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

        Parameters
        ----------
        table: string
            The relevant table.
        record: string | ObjectId | AttrDict | void
            The relevant record.
        action: string
            The type of action that will be performed if the button triggered.
        project: string | ObjectId | AttrDict
            The project in question, if any.
            Needed to determine whether a press on the button is permitted.
        key: string, optional None
            If present, it identifies a field that is stored inside the
            record.
        """
        Settings = self.Settings
        H = Settings.H
        Mongo = self.Mongo
        Auth = self.Auth

        (record, recordId) = Mongo.get(table, record)
        (site, siteId, project, projectId, edition, editionId) = self.context(
            table, record
        )
        permitted = Auth.authorise(
            table,
            record=record,
            action=action,
            project=project,
        )

        if not permitted:
            return ""

        Settings = self.Settings
        actions = Settings.auth.actions

        disable = False
        report = ""

        if action == "delete":
            details = self.getDetailRecords(table, record)
            if len(details):
                disable = True
                detailContent = []
                for (detailTable, detailRecords) in details.items():
                    nDetails = len(detailRecords)
                    plural = "" if nDetails == 1 else "s"
                    detailRep = detailTable + plural
                    detailContent.append(f"""{nDetails}&nbsp;{detailRep}""")

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
        recordIdRep = "" if recordId is None else f"/{recordId}"

        if disable:
            href = None
            cls = "disabled"
            can = "Cannot"
        else:
            if action == "create":
                datamodel = Settings.datamodel
                detail = datamodel.detail
                insertTable = detail[table]
                href = f"/{table}/{recordId}/{insertTable}/create"
                tip = f"{name} new {insertTable}"
            else:
                href = f"/{table}{recordIdRep}{keyRepUrl}/{action}"
                tip = f"{can}{name}{keyRepTip} this {table}"

            cls = ""
            can = ""

        fullCls = f"button large {cls}"
        return H.iconx(action, href=href, title=tip, cls=fullCls) + report

    def breadCrumb(self, project):
        """Makes a link to the landing page of a project.

        Parameters
        ----------
        project: string | ObjectId | AttrDict
            The project in question.
        """
        Settings = self.Settings
        H = Settings.H
        Mongo = self.Mongo

        (projectId, project) = Mongo.get("project", project)
        projectUrl = f"/project/{projectId}"
        text = self.getValue("project", project, "title", bare=True)
        return H.p(
            [
                "Project: ",
                H.a(
                    [text, H.gt()],
                    projectUrl,
                    cls="button",
                    title="back to the project page",
                ),
            ]
        )

    def saveFile(self, table, record, key, path, fileName, givenFileName=None):
        """Saves a file in the context given by a record.

        Parameters
        ----------
        table: string
            The relevant table.
        record: string | ObjectId | AttrDict | void
            The relevant record.
        key: string
            The upload key
        path: string
            The path from the context directory to the file
        fileName: string
            Name  of the file to be saved as mentioned in the request.
        givenFileName: string, optional None
            The name of the file as which the uploaded file will be saved;
            if None, the file will be saved with the name from the request.

        Return
        ------
        response
            A json response with the status of the save operation:

            * a boolean: whether the save succeeded
            * a message: messages to display
            * content: new content for an upload control (only if successful)
        """
        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo
        Auth = self.Auth
        workingDir = Settings.workingDir

        uploadObject = self.getUploadObject(key, fileName=givenFileName)
        table = uploadObject.table

        (recordId, record) = Mongo.get(table, record)

        permitted = Auth.authorise(table, record=record, action="update")

        if givenFileName is not None and fileName != givenFileName:
            fileName = givenFileName

        sep = "/" if path else ""
        filePath = f"{path}{sep}{fileName}"
        fileFullPath = f"{workingDir}/{filePath}"

        if not permitted:
            logmsg = f"Upload not permitted: {key}: {fileFullPath}"
            Messages.warning(
                logmsg=logmsg,
                msg=f"Upload not permitted: {filePath}",
            )
            return jsonify(status=False, msg=logmsg)

        try:
            with open(fileFullPath, "wb") as fh:
                fh.write(data())
        except Exception:
            logmsg = f"Could not save uploaded file: {key}: {fileFullPath}"
            Messages.warning(
                logmsg=logmsg,
                msg=f"Uploaded file not saved: {filePath}",
            )
            return jsonify(status=False, msg=logmsg)

        content = self.getUpload(record, key, fileName=givenFileName, bust=fileName)

        return jsonify(status=True, content=content)
