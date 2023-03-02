from io import BytesIO
import os
from datetime import datetime as dt
import json
import yaml
from tempfile import mkdtemp
from flask import jsonify
from zipfile import ZipFile, ZIP_DEFLATED

from control.generic import AttrDict
from control.files import fileExists, fileRemove, dirExists, dirMake, dirCopy, dirRemove
from control.datamodel import Datamodel
from control.flask import requestData
from control.admin import Admin


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

    def getScene(self, projectId, edition, version=None, action=None):
        """Get the scene of an edition of a project.

        Well, only if the current user is authorised.

        A scene is displayed by means of an icon and a row of buttons.

        There are also buttons to upload model files and the scene file.

        If action is not None, the scene is loaded in a specific version of the
        viewer in a specific mode (`read` or `edit`).
        The edition knows which viewer to choose.

        Which version and which mode are used is determined by the parameters.
        If the parameters do not specify values, sensible defaults are chosen.

        Parameters
        ----------
        projectId: ObjectId
            The id of the project to which the edition belongs.
        edition: string | ObjectId | AttrDict
            The edition in question.
        version: string, optional None
            The version of the chosen viewer that will be used.
            If no version or a non-existing version are specified,
            the latest existing version for that viewer will be chosen.
        action: string, optional read
            The mode in which the viewer should be opened.
            If the mode is `update`, the viewer is opened in edit mode, if the
            scene file exists, otherwise in create mode,  which, in case
            of the Voyager viewer, means `standalone` mode.
            All other modes lead to the viewer being opened in read-only
            mode.
            If the mode is read-only, but the scene file is missing, no viewer
            will be opened.

        Returns
        -------
        string
            A caption of the scene of the edition,
            with possibly a frame with the 3D viewer showing the scene.
            The result is wrapped in a HTML string.
        """
        Settings = self.Settings
        H = Settings.H
        workingDir = Settings.workingDir
        modelzFile = Settings.modelzFile
        Mongo = self.Mongo
        Viewers = self.Viewers
        Wrap = self.Wrap

        (editionId, edition) = Mongo.get("edition", edition)
        (viewer, sceneFile) = self.getViewInfo(edition)
        version = Viewers.check(viewer, version)

        scenePath = f"{workingDir}/project/{projectId}/edition/{editionId}/{sceneFile}"
        sceneExists = fileExists(scenePath)

        if action is None:
            action = "read"

        (editionId, edition) = Mongo.get("edition", edition)

        baseResult = Wrap.sceneMain(
            projectId, edition, sceneFile, viewer, version, action, sceneExists
        )
        zipUpload = (
            ""
            if sceneExists
            else (
                H.h(4, "Scene plus model files, zipped")
                + H.div(self.getUpload(edition, "modelz", fileName=modelzFile))
            )
        )

        return (
            baseResult
            + H.h(4, "Scene" if sceneExists else "No scene yet")
            + H.div(self.getUpload(edition, "scene", fileName=sceneFile))
            + H.h(4, "Model files")
            + H.div(self.getUpload(edition, "model"))
            + zipUpload
        )

    def getAdmin(self):
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
        return Admin(self).wrap()

    def createProject(self, site):
        """Creates a new project.

        Parameters
        ----------
        site: AttrDict | string
            record that represents the site, or its id.
            It acts as a master record for all projects.

        Returns
        -------
        ObjectId
            The id of the new project.
        """
        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo
        Auth = self.Auth
        workingDir = Settings.workingDir

        (siteId, site) = Mongo.get("site", site)

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
        projectId = Mongo.insertRecord(
            "project", title=title, meta=dict(dc=dcMeta), isVisible=False
        )
        Mongo.insertRecord(
            "projectUser", projectId=projectId, user=user, role="organiser"
        )
        projectDir = f"{workingDir}/project/{projectId}"
        if dirExists(projectDir):
            Messages.warning(
                msg="The new project already exists on the file system",
                logmsg=f"New project {projectId} already exists on the filesystem.",
            )
        else:
            dirMake(projectDir)

        return projectId

    def deleteProject(self, project):
        """Deletes a project.

        Parameters
        ----------
        project: string | ObjectId | AttrDict
            The project in question.
        """
        Mongo = self.Mongo
        Auth = self.Auth

        (projectId, project) = Mongo.get("project", project)

        permitted = Auth.authorise("project", project, action="delete")
        if not permitted:
            return None

        result = Mongo.deleteRecord("project", _id=projectId)
        return result

    def createEdition(self, project):
        """Creates a new edition.

        Parameters
        ----------
        project: AttrDict | string
            record that represents the maste project, or its id.

        Returns
        -------
        ObjectId
            The id of the new edition.
        """
        Mongo = self.Mongo
        Messages = self.Messages
        Auth = self.Auth
        Settings = self.Settings
        workingDir = Settings.workingDir

        def fillin(template, values):
            typ = type(template)
            if typ is str:
                for (k, v) in values.items():
                    template = template.replace(f"«{k}»", v)
                return template
            if typ in {list, tuple}:
                return [fillin(e, values) for e in template]
            if typ in {dict, AttrDict}:
                return {k: fillin(v, values) for (k, v) in template.items()}
            return template

        editionSettingsTemplate = Settings.editionSettingsTemplate
        viewerDefault = Settings.viewerDefault
        viewerInfo = Settings.viewers[viewerDefault] or AttrDict()
        versionDefault = viewerInfo.defaultVersion
        sceneFile = viewerInfo.sceneFile

        values = dict(viewer=viewerDefault, version=versionDefault, scene=sceneFile)
        editionSettings = fillin(editionSettingsTemplate, values)

        (projectId, project) = Mongo.get("project", project)

        permitted = Auth.authorise(
            "project", project, action="create", insertTable="edition"
        )
        if not permitted:
            return None

        User = Auth.myDetails()
        user = User.user
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
            "edition",
            title=title,
            projectId=projectId,
            meta=dict(dc=dcMeta),
            settings=editionSettings,
            isPublished=False,
        )
        Mongo.insertRecord("editionUser", editionId=editionId, user=user, role="editor")

        editionDir = f"{workingDir}/project/{projectId}/edition/{editionId}"
        if dirExists(editionDir):
            Messages.warning(
                msg="The new edition already exists on the file system",
                logmsg=f"New edition {editionId} already exists on the filesystem.",
            )
        else:
            dirMake(editionDir)

        return editionId

    def deleteEdition(self, edition):
        """Deletes an edition.

        Parameters
        ----------
        edition: string | ObjectId | AttrDict
            The edition in question.
        """
        Mongo = self.Mongo
        Auth = self.Auth

        (editionId, edition) = Mongo.get("edition", edition)

        permitted = Auth.authorise("edition", edition, action="delete")
        if not permitted:
            return None

        result = Mongo.deleteRecord("edition", _id=editionId)
        return result

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
        update = {f"{nameSpace}.{fieldPath}": value}
        if key == "title":
            update[key] = value

        if Mongo.updateRecord(table, update, stop=False, _id=recordId) is None:
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
        newRole = json.loads(requestData())
        return Admin(self).saveRole(user, newRole, table, recordId)

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
        (newRole, newUser) = json.loads(requestData())
        return Admin(self).linkUser(newUser, newRole, table, recordId)

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

    def getSnapshots(self):
        """Produce a snapshot button and an overview of existing snapshots.

        Only if it is relevant to the current user in the current run mode.
        """
        Auth = self.Auth
        if not Auth.maySnapshot():
            return ""

        Settings = self.Settings
        H = Settings.H
        Messages = self.Messages

        dataDir = Settings.dataDir
        snapshotBase = f"{dataDir}/snapshots"

        snapshots = []

        if dirExists(snapshotBase):
            with os.scandir(snapshotBase) as dh:
                for entry in dh:
                    if entry.is_dir():
                        snapshots.append(entry.name)
            snapshots = list(reversed(sorted(snapshots)))

        snapshots = (
            H.small(H.i("No snapshots"))
            if len(snapshots) == 0
            else H.div([[H.small(snapshot), H.br()] for snapshot in snapshots])
        )

        return H.details(
            H.a(
                "make snapshot",
                "/snapshot",
                title="make a snapshot of all data in files and database",
                cls="small",
                **Messages.client(
                    "info", "wait for snapshot complete ...", replace=True
                ),
            ),
            snapshots,
            "snapshots",
        )

    def getDownload(self, table, record):
        """Display the name and/or upload controls of an uploaded file.

        The user may upload model files and a scene file to an edition,
        and various png files as icons for projects, edtions, and scenes.
        Here we produce the control to do so.

        Only if the user has `update` authorisation, an upload/delete widget
        will be returned.

        Parameters
        ----------
        table: string
            The table in which the relevant record sits
        record: string | ObjectId | AttrDict
            The relevant record.

        Returns
        -------
        string
            The name of the file that is currently present, or the indication
            that no file is present.

            If the user has edit permission for the edition, we display
            widgets to upload a new file or to delete the existing file.
        """
        Settings = self.Settings
        H = Settings.H
        Mongo = self.Mongo
        Auth = self.Auth

        (recordId, record) = Mongo.get(table, record)

        actions = Auth.authorise(table, record)

        if "read" not in actions:
            return None

        return H.iconx(
            "download", text="download", href=f"/download/{table}/{recordId}"
        )

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
        if not text:
            text = H.i("no title")

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

    def snapshot(self):
        """Makes a snapshot of all data of all projects, in files and db.

        A copy of the data of the current run mode is put in the
        data directory under `snapshots`. The directory name of the snapshot is
        the current date-time up to the second in iso format, but with the `:`
        replaced by `-`.

        Below that we have directories:

        *   `files`: contains the complete contents of the working directory of
            the current run mode.
        *   `db`: a backup of the complete contents of the MongoDb database of the
            current run mode.
            In there again a subdivision:

            * [`bson`](https://www.mongodb.com/basics/bson)
            * `json`

            The name indicates the file format of the backup.
            In both cases, the data ends up in folders per collection,
            and within those folders we have files per document.
        """
        Messages = self.Messages
        Auth = self.Auth

        if not Auth.maySnapshot():
            Messages.warning(
                msg="Reset data is not allowed",
                logmsg=("Reset data is not allowed"),
            )
            return False

        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo
        dataDir = Settings.dataDir
        workingDir = Settings.workingDir

        now = dt.utcnow().isoformat(timespec="seconds").replace(":", "-")
        snapshotDir = f"{dataDir}/snapshots/{now}"
        dbDest = f"{snapshotDir}/db"
        fileDest = f"{snapshotDir}/files"

        dirCopy(workingDir, fileDest)

        Messages.info(
            msg=f"Making snapshot {now}", logmsg=f"Making snapshot to {snapshotDir}"
        )
        Messages.info(msg="snapshot of database ...")
        Mongo.backup(dbDest, asJson=True)
        Messages.info(msg="snapshot of files ...")
        Messages.info(msg="snapshot completed.")

    def download(self, table, record):
        """Responds with a download of a project or edition.

        Parameters
        ----------
        table: string
            The table where the item to be downloaded sits.
        record: string
            The record of the item to be downloaded.

        Return
        ------
        response
            A download response.
        """
        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo
        Auth = self.Auth
        dataDir = Settings.dataDir
        workingDir = Settings.workingDir
        runMode = Settings.runMode

        (recordId, record) = Mongo.get(table, record)

        permitted = Auth.authorise(table, record, action="read")

        if not permitted:
            logmsg = f"Download not permitted: {table}: {recordId}"
            msg = f"Download of {table} not permitted"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msg=msg)

        (siteId, site, projectId, project, editionId, edition) = self.context(
            table, record
        )

        src = f"{workingDir}/project/{projectId}"

        if edition is not None:
            src += f"/edition/{editionId}"

        sep = "/" if dataDir else ""
        tempBase = f"{dataDir}{sep}temp/{runMode}"
        dirMake(tempBase)
        dst = mkdtemp(dir=tempBase)
        landing = f"{dst}/{recordId}"
        fileName = f"{table}-{recordId}.zip"

        if edition is None:
            yamlDest = f"{landing}/project.yaml"
        else:
            yamlDest = f"{landing}/edition.yaml"

        dirCopy(src, landing)

        with open(yamlDest, "w") as yh:
            yaml.dump(Mongo.consolidate(project), yh, allow_unicode=True)

        if edition is None:
            editions = Mongo.getList("edition", projectId=projectId)
            for ed in editions:
                edId = ed._id
                yamlDest = f"{landing}/edition/{edId}/edition.yaml"
                with open(yamlDest, "w") as yh:
                    yaml.dump(Mongo.consolidate(ed), yh, allow_unicode=True)

        zipBuffer = BytesIO()
        with ZipFile(zipBuffer, "w", compression=ZIP_DEFLATED) as zipFile:

            def compress(path):
                sep = "/" if path else ""
                with os.scandir(f"{landing}{sep}{path}") as dh:
                    for entry in dh:
                        name = entry.name
                        if entry.is_file():
                            arcFile = f"{path}{sep}{name}"
                            srcFile = f"{landing}/{arcFile}"
                            zipFile.write(srcFile, arcFile)
                        elif entry.is_dir():
                            compress(f"{path}/{name}")

            compress("")
        zipData = zipBuffer.getvalue()

        dirRemove(dst)

        headers = {
            "Expires": "0",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Content-Type": "application/zip",
            "Content-Disposition": f'attachment; filename="{fileName}"',
            "Content-Encoding": "identity",
        }

        return (zipData, headers)

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
        H = Settings.H
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

        filePath = f"{path}{fileName}"
        fileFullPath = f"{workingDir}/{filePath}"

        if not permitted:
            logmsg = f"Upload not permitted: {key}: {fileFullPath}"
            msg = f"Upload not permitted: {fileName}"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msg=msg)

        if key == "modelz":
            destDir = f"{workingDir}/{path}"
            (good, msg) = self.processModelZip(requestData(), destDir)
            if good:
                return jsonify(
                    status=True, msg=msg, content=H.b("Please refresh the page")
                )
            Messages.warning(logmsg=msg)
            return jsonify(status=False, msg=msg)

        try:
            with open(fileFullPath, "wb") as fh:
                fh.write(requestData())
        except Exception:
            logmsg = f"Could not save uploaded file: {key}: {fileFullPath}"
            msg = f"Uploaded file not saved: {fileName}"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msg=msg)

        content = self.getUpload(
            record, key, fileName=givenFileName, bust=fileName, wrapped=False
        )

        return jsonify(status=True, content=content)

    def processModelZip(self, zf, destDir):
        """Processes zip data with a scene and model files.

        All files in the zip file will be examined, and those with
        extension svx.json will be saved as voyager.svx.json
        and those with extensions glb of gltf will be saved under their
        own names.
        All pathnames will be ignored, so potentially files may overwrite each other.

        The user is held responsible to submit a suitable file.

        Parameters
        ----------
        zf: bytes
            The raw zip data
        """
        Messages = self.Messages
        Settings = self.Settings
        viewerDefault = Settings.viewerDefault
        viewerInfo = Settings.viewers[viewerDefault] or AttrDict()
        sceneFile = viewerInfo.sceneFile

        msgs = []
        good = True
        try:
            zf = BytesIO(zf)
            z = ZipFile(zf)

            allFiles = 0
            sceneFiles = set()
            modelFiles = set()
            doubles = set()
            otherFiles = set()

            for zInfo in z.infolist():
                if zInfo.filename[-1] == "/":
                    continue
                if zInfo.filename.startswith("__MACOS"):
                    continue

                allFiles += 1

                zName = zInfo.filename
                zTest = zName.lower()

                if zTest.endswith(".svx.json"):
                    if zName in sceneFiles:
                        doubles.add(zName)
                    else:
                        sceneFiles.add(zName)
                        zInfo.filename = sceneFile
                elif zTest.endswith(".glb") or zTest.endswith(".gltf"):
                    if zName in modelFiles:
                        doubles.add(zName)
                    else:
                        modelFiles.add(zName)
                else:
                    if zName in otherFiles:
                        doubles.add(zName)
                    else:
                        otherFiles.add(zName)
                z.extract(zInfo, path=destDir)

            msgs.append(f"All files in zip: {allFiles:>3}")
            msgs.append(f"Files encountered multiple times: {len(doubles):>3} x")
            msgs.append(f"Scene files: {len(sceneFiles):>3} x")
            msgs.append(f"Model files: {len(modelFiles):>3} x")
            msgs.append(f"Other files: {len(otherFiles):>3} x")

        except Exception as e:
            good = False
            msgs.append("Something went wrong")
            Messages.warning(logmsg=str(e))

        msg = "\n".join(msgs)
        return (good, msg)

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
            msg = f"Delete not permitted: {fileName}"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msg=msg)

        if not fileExists(fileFullPath):
            logmsg = f"File does not exist: {key}: {fileFullPath}"
            msg = f"File does not exist: {fileName}"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msg=msg)

        try:
            fileRemove(fileFullPath)
        except Exception:
            logmsg = f"Could not delete file: {key}: {fileFullPath}"
            msg = f"File not deleted: {fileName}"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msg=msg)

        content = self.getUpload(
            record, key, fileName=givenFileName, bust=fileName, wrapped=False
        )

        return jsonify(status=True, content=content)
