import json
from flask import jsonify
from control.generic import AttrDict
from control.files import fileExists, fileRemove
from control.datamodel import Datamodel
from control.flask import requestData
from control.mywork import Mywork


class Content(Datamodel):
    def __init__(self, Settings, Viewers, Messages, Mongo, Wrap):
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
        self.Wrap = Wrap

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
        Mongo = self.Mongo
        Wrap = self.Wrap

        (siteTable, siteId, site) = self.relevant()

        return Wrap.projectsMain(site, Mongo.getList("project"))

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
        Mongo = self.Mongo
        Wrap = self.Wrap

        (projectId, project) = Mongo.get("project", project)

        return Wrap.editionsMain(project, Mongo.getList("edition", projectId=projectId))

    def getScene(self, edition, version=None, action=None):
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
        action: string, optional `read`
            The mode in which the viewer should be opened.
            If the mode is `update`, the viewer is opened in edit mode.
            All other modes lead to the viewer being opened in read-only
            mode.

        Returns
        -------
        string
            A caption of the scene of the edition,
            with possibly a frame with the 3D viewer showing the scene.
            The result is wrapped in a HTML string.
        """
        Mongo = self.Mongo
        Viewers = self.Viewers
        Wrap = self.Wrap

        (viewer, sceneFile) = self.getViewInfo(edition)
        version = Viewers.check(viewer, version)

        if action is None:
            action = "read"

        (editionId, edition) = Mongo.get("edition", edition)

        return Wrap.sceneMain(edition, sceneFile, viewer, version, action)

    def getMywork(self):
        """Get the list of relevant projects, editions and users.

        Admin users get the list of all users.

        Normal users get the list of users associated with

        * the project of which they are organiser
        * the editions of which they are editor or reviewer

        Guests and not-logged-in users cannot see any user.

        If the user has rights to modify the association
        between users and projects/editions, he will get
        the controls to do so.

        Returns
        -------
        string
        """
        Admin = Mywork(self)
        return Admin.wrap()

    def insertProject(self):
        Mongo = self.Mongo
        Auth = self.Auth

        (siteTable, siteId, site) = self.relevant()

        permitted = Auth.authorise("site", site, action="create", insertTable="project")
        if not permitted:
            return None

        User = Auth.myDetails()
        user = User.user
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

    def insertEdition(self, project):
        Mongo = self.Mongo
        Auth = self.Auth

        (projectId, project) = Mongo.get("project", project)

        permitted = Auth.authorise(
            "project", project, action="create", insertTable="edition"
        )
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

    def saveValue(self, table, record, key):
        """Saves a value of into a record.

        A record contains a document, which is a (nested) dict.
        A value is inserted somewhere (deep) in that dict.

        The value is given by the request.

        Where exactly is given by a path that is stored in the field information,
        which is accessible by the key.

        Parameters
        ----------
        table: string
            The relevant table.
        record: string | ObjectId | AttrDict | void
            The relevant record.

        key: string
            an identifier for the meta data field.

        Returns
        -------
        dict
            Contains the following keys:

            * `status`: whether the save action was successful
            * `messages`: messages issued during the process
            * `readonly`: the html of the updated formatted value,
              this will replace the currently displayed value.
        """
        Auth = self.Auth
        Mongo = self.Mongo

        permitted = Auth.authorise(table, record, action="update")

        if not permitted:
            return dict(stat=False, messages=[["error", "update not allowed"]])

        F = self.makeField(key)

        nameSpace = F.nameSpace
        fieldPath = F.fieldPath

        (recordId, record) = Mongo.get(table, record)

        value = json.loads(requestData())

        if (
            Mongo.updateRecord(
                table, {f"{nameSpace}.{fieldPath}": value}, stop=False, _id=recordId
            )
            is None
        ):
            return dict(
                stat=False,
                messages=[["error", "could not update the record in the database"]],
            )
        else:
            (recordId, record) = Mongo.get(table, recordId)

        return dict(
            stat=True,
            messages=[],
            readonly=F.formatted(table, record, editable=False, level=None),
        )

    def saveRole(self, user, table, recordId):
        """Saves a role into a user or cross table record.

        The role is given by the request.

        Parameters
        ----------
        user: string
            The eppn of the user.
        table: string | void
            The relevant table. If not None, it indicates whether we are updating
            site-wide roles, otherwise project/edition roles.
        recordId: string | void
            The id of the relevant record. If not None, it is a project/edition
            record Id, which can be used to locate the cross record between the
            user collection and the project/edition record where the user's
            role is stored.
            If None, the user's role is inside the user record.

        Returns
        -------
        dict
            Contains the following keys:

            * `status`: whether the save action was successful
            * `messages`: messages issued during the process
            * `updated`: if the action was successful, all user management info
              will be passed back and will replace the currently displayed
              material.
        """
        Admin = Mywork(self)

        newRole = json.loads(requestData())
        return Admin.saveRole(user, newRole, table, recordId)

    def linkUser(self, table, recordId):
        """Links a user in certain role to a project/edition record.

        The user and role are given by the request.

        Parameters
        ----------
        table: string
            The relevant table.
        recordId: string
            The id of the relevant record,
            which can be used to locate the cross record between the
            user collection and the project/edition record where the user's
            role is stored.

        Returns
        -------
        dict
            Contains the following keys:

            * `status`: whether the save action was successful
            * `messages`: messages issued during the process
            * `updated`: if the action was successful, all user management info
              will be passed back and will replace the currently displayed
              material.
        """
        Admin = Mywork(self)

        (newRole, newUser) = json.loads(requestData())
        return Admin.linkUser(newUser, newRole, table, recordId)

    def getValue(self, table, record, key, level=None, bare=False):
        """Retrieve a metadata value.

        Metadata sits in a big, potentially deeply nested dictionary of keys
        and values.
        These locations are known to the system (based on `fields.yml`).
        This function retrieves the information from those known locations.

        If a value is in fact composed of multiple values, it will be
        handled accordingly.

        If the user may edit the value, an edit button is added.

        Parameters
        ----------
        key: string
            an identifier for the meta data field.
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

        actions = Auth.authorise(table, record)

        if "read" not in actions:
            return None

        F = self.makeField(key)

        if bare:
            return F.bare(record)

        editable = Auth.authorise(table, record, action="update")
        return F.formatted(table, record, editable=editable, level=level)

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

    def getUpload(self, record, key, fileName=None, bust=None, wrapped=True):
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
        key: string
            an identifier for the upload field.
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
        wrapped: boolean, optional True
            Whether the content should be wrapped in a container element.
            See `control.html.HtmlElements.finput()`.

        Returns
        -------
        string
            The name of the file that is currently present, or the indication
            that no file is present.

            If the user has edit permission for the edition, we display
            widgets to upload a new file or to delete the existing file.
        """
        Auth = self.Auth

        uploadConfig = self.getUploadConfig(key)
        table = uploadConfig.table

        actions = Auth.authorise(table, record)

        if "read" not in actions:
            return None

        F = self.makeUpload(key, fileName=fileName)

        return F.formatted(record, "update" in actions, bust=bust, wrapped=wrapped)

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

        (site, siteId, projectId, project, editionId, edition) = self.context(
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

        permitted = Auth.authorise(table, record, action="read")

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
                    text,
                    projectUrl,
                    cls="button",
                    title="back to the project page",
                ),
            ]
        )

    def saveFile(self, record, key, path, fileName, givenFileName=None):
        """Saves a file in the context given by a record.

        Parameters
        ----------
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

        uploadConfig = self.getUploadConfig(key)
        table = uploadConfig.table

        (recordId, record) = Mongo.get(table, record)

        permitted = Auth.authorise(table, record, action="update")

        if givenFileName is not None and fileName != givenFileName:
            fileName = givenFileName

        sep = "/" if path else ""
        filePath = f"{path}{sep}{fileName}"
        fileFullPath = f"{workingDir}/{filePath}"

        if not permitted:
            logmsg = f"Upload not permitted: {key}: {fileFullPath}"
            msg = f"Upload not permitted: {filePath}"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msg=msg)

        try:
            with open(fileFullPath, "wb") as fh:
                fh.write(requestData())
        except Exception:
            logmsg = f"Could not save uploaded file: {key}: {fileFullPath}"
            msg = f"Uploaded file not saved: {filePath}"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msg=msg)

        content = self.getUpload(
            record, key, fileName=givenFileName, bust=fileName, wrapped=False
        )

        return jsonify(status=True, content=content)

    def deleteFile(self, record, key, path, fileName, givenFileName=None):
        """Deletes a file in the context given by a record.

        Parameters
        ----------
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

        uploadConfig = self.getUploadConfig(key)
        table = uploadConfig.table

        (recordId, record) = Mongo.get(table, record)

        permitted = Auth.authorise(table, record, action="update")

        sep = "/" if path else ""
        filePath = f"{path}{sep}{fileName}"
        fileFullPath = f"{workingDir}/{filePath}"

        if not permitted:
            logmsg = f"Delete file not permitted: {key}: {fileFullPath}"
            msg = f"Delete not permitted: {filePath}"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msg=msg)

        if not fileExists(fileFullPath):
            logmsg = f"File does not exist: {key}: {fileFullPath}"
            msg = f"File does not exist: {filePath}"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msg=msg)

        try:
            fileRemove(fileFullPath)
        except Exception:
            logmsg = f"Could not delete file: {key}: {fileFullPath}"
            msg = f"File not deleted: {filePath}"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msg=msg)

        content = self.getUpload(
            record, key, fileName=givenFileName, bust=fileName, wrapped=False
        )

        return jsonify(status=True, content=content)
