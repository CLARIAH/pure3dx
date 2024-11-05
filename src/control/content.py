import os
import json
import yaml
import magic
from io import BytesIO
from tempfile import mkdtemp
from flask import jsonify
from zipfile import ZipFile, ZIP_DEFLATED
from traceback import format_exception

from control.generic import AttrDict
from control.files import (
    fileExists,
    fileRemove,
    dirExists,
    dirMake,
    dirCopy,
    dirRemove,
    extNm,
    readYaml,
)
from control.datamodel import Datamodel
from control.flask import requestData, getReferrer, redirectStatus
from control.admin import Admin
from control.checkgltf import check


class Content(Datamodel):
    def __init__(self, Settings, Messages, Viewers, Mongo, Wrap):
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
        Wrap: object
            Singleton instance of `control.wrap.Wrap`.
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

    def addPublish(self, Publish):
        """Give this object a handle to the Publish object.

        Because of cyclic dependencies some objects require to be given
        a handle to Publish after their initialization.
        """
        self.Publish = Publish

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
        if siteId is None:
            return ""

        return Wrap.projectsMain(site, Mongo.getList("project", sort="title"))

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
        if projectId is None:
            return ""

        return Wrap.editionsMain(
            project, Mongo.getList("edition", sort="title", projectId=projectId)
        )

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
            of the Voyager viewer, means `dragdrop` mode, in older versions
            `standalone`.
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
        if editionId is None:
            return ""

        (viewer, sceneFile) = Viewers.getViewInfo(edition)
        version = Viewers.check(viewer, version)

        if sceneFile is None:
            sceneExists = False
            baseResult = ""
        else:
            scenePath = (
                f"{workingDir}/project/{projectId}/edition/{editionId}/{sceneFile}"
            )
            sceneExists = fileExists(scenePath)
            baseResult = Wrap.sceneMain(
                projectId, edition, sceneFile, viewer, version, action, sceneExists
            )

        if action is None:
            action = "read"

        zipUpload = (
            ""
            if sceneExists or sceneFile is None
            else (
                H.h(4, "Scene plus model files, zipped")
                + H.div(self.getUpload(edition, "modelz", fileName=modelzFile))
            )
        )
        sceneUpload = (
            ""
            if sceneFile is None
            else H.div(self.getUpload(edition, "scene", fileName=sceneFile))
        )

        return (
            baseResult
            + H.h(4, "Scene" if sceneExists else "No scene yet")
            + sceneUpload
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
        if siteId is None:
            return None

        permitted = Auth.authorise("site", site, action="create", insertTable="project")
        if not permitted:
            return None

        User = Auth.myDetails()
        user = User.user
        name = User.nickname

        title = "Project without title"

        dcMeta = dict(
            title=title,
            abstract="No intro",
            description="No description",
            creator=name,
        )
        projectId = Mongo.insertRecord(
            "project", title=title, siteId=siteId, dc=dcMeta, isVisible=False
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

    def deleteItem(self, table, record):
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
        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo
        Auth = self.Auth
        workingDir = Settings.workingDir

        (recordId, record) = Mongo.get(table, record)
        if recordId is None:
            Messages.warning(
                msg=f"Delete {table}: no such {table}",
                logmsg=f"Delete {table}: no {table} {recordId}",
            )
            return None

        permitted = Auth.authorise(table, record, action="delete")
        if not permitted:
            return None

        details = self.getDetailRecords(table, record)
        nDetails = len(details)
        if nDetails:
            Messages.warning(
                msg=f"Cannot delete {table} because it has {nDetails} detail records",
                logmsg=f"Delete {table} {recordId} prevented: {nDetails} details",
            )
            return None

        good = True

        links = self.getLinkedCrit(table, record)

        if links:
            for linkTable, linkCriteria in links.items():
                (thisGood, count) = Mongo.deleteRecords(
                    linkTable, stop=False, **linkCriteria
                )
                if not thisGood:
                    good = False
                    Messages.error(
                        stop=False,
                        msg=f"Error during removing link records from {linkTable}",
                        logmsg=(
                            "Cannot delete records from "
                            f"{linkTable} by {linkCriteria}"
                        ),
                    )
                    break

                Messages.info(
                    msg=f"Deleted {count} link records from {linkTable}",
                    logmsg=f"Deleted {count} link records from {linkTable}",
                )

        if not good:
            return False

        good = Mongo.deleteRecord(table, _id=recordId)

        if not good:
            return False

        itemDirHead = workingDir
        itemDirTail = f"{table}/{recordId}"
        if table == "edition":
            projectId = record.projectId
            itemDirHead += f"/project/{projectId}"
        itemDir = f"{itemDirHead}/{itemDirTail}"

        if dirExists(itemDir):
            dirRemove(itemDir)
            Messages.info(
                msg=f"The {table} directory is removed",
                logmsg=f"The {table} dir {itemDir} is removed",
            )
        else:
            Messages.warning(
                msg=f"The {table} directory on file system did not exist",
                logmsg=f"The {table} dir {itemDir} did not exist",
            )

        return True

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
                for k, v in values.items():
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
        if projectId is None:
            return None

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
            abstract="No intro",
            description="No description",
            provenance="No sources",
            creator=name,
        )
        editionId = Mongo.insertRecord(
            "edition",
            title=title,
            projectId=projectId,
            dc=dcMeta,
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

    def saveValue(self, table, record, key):
        """Saves a value of into a record.

        A record is a document, which is a (nested) dict.
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

        value = json.loads(requestData())
        permitted = Auth.authorise(table, record, action="update")

        if not permitted:
            return dict(stat=False, messages=[["error", "update not allowed"]])

        F = self.makeField(key)

        nameSpace = F.nameSpace
        fieldPath = F.fieldPath
        tp = F.tp

        (recordId, record) = Mongo.get(table, record)
        if recordId is None:
            return dict(
                stat=False,
                messages=[["error", "record does not exist"]],
            )

        sValue = value if tp == "text" else readYaml(value, plain=True, ignore=True)
        nameSpaceRep = "" if not nameSpace else f"{nameSpace}."
        update = {f"{nameSpaceRep}{fieldPath}": sValue}
        if key == "title":
            update[key] = sValue

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

    def saveKeyword(self):
        """Saves a keyword.

        A keyword is a string value and it belongs to a list of keywords.
        Some metadata fields are associated with a list of values: keywords.

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
        specs = json.loads(requestData())
        name = specs["name"]
        value = specs["value"]
        return Admin(self).saveKeyword(name, value)

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
        specs = json.loads(requestData())
        name = specs["name"]
        value = specs["value"]
        return Admin(self).saveKeyword(name, value)

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
            user table and the project/edition record where the user's
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

    def createUser(self, user):
        """Creates a new user with a given user name.

        Parameters
        ----------
        user: string
            The user name of the user.
            This should be different from the user names of existing users.

        Returns
        -------
        dict
            Contains the following keys:

            * `status`: whether the create action was successful
            * `messages`: messages issued during the process
            * `name`: the name under which the new user has been saved
        """
        return Admin(self).createUser(user)

    def deleteUser(self, user):
        """Deletes a test user with a given user name.

        Parameters
        ----------
        user: string
            The user name of the user.
            This should be a test user, not linked to any project or edition.

        Returns
        -------
        dict
            Contains the following keys:

            * `status`: whether the create action was successful
            * `messages`: messages issued during the process
        """
        return Admin(self).deleteUser(user)

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
            user table and the project/edition record where the user's
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

    def getValue(self, table, record, key, level=None, manner="formatted"):
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

        manner: string, optional wrapped
            If it is "formatted", the value is represented fully wrapped in HTML,
            possibly with edit/save controls.
            If it is "bare", the value is represented as a simple string.
            If it is "logical", the logical value is returned.

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

        isBare = manner == "bare"
        isLogical = manner == "logical"

        if isBare or isLogical:
            return (F.bare if isBare else F.logical)(record)

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
        if recordId is None:
            return ""

        actions = Auth.authorise(table, record)

        if "read" not in actions:
            return ""

        return H.iconx(
            "download", text="download", href=f"/download/{table}/{recordId}"
        )

    def getPublishInfo(self, table, record):
        """Display the number under which a project/edition is published.

        Editions of a project may have been published. If that is the case,
        the project has been assigned a sequence number, under which it can be
        found on the static site with published material.

        Here we collect that number, and, for editions, we may put a publish
        button here.

        Parameters
        ----------
        table: string
            The table in which the relevant record sits
        record: string | ObjectId | AttrDict
            The relevant record.

        Returns
        -------
        string
            In case of a project: the number of the project on the static site.
            In case of an edition: the number of the project and the number of the
            edition on the static site. If the edition is not yet published, and
            the user is allowed to publish the edition, then a publish button is
            also added.
        """
        Settings = self.Settings

        H = Settings.H
        Mongo = self.Mongo
        Auth = self.Auth

        pubUrl = Settings.pubUrl
        published = Settings.published

        (recordId, record) = Mongo.get(table, record)
        if recordId is None:
            return ""

        actions = Auth.authorise(table, record)

        if "read" not in actions or table not in {"project", "edition"}:
            return ""

        (site, siteId, projectId, project, editionId, edition) = self.context(
            table, record
        )

        pPubNum = project.pubNum

        projectPubStr = (
            H.i("No published editions")
            if pPubNum is None
            else H.span("Published: ")
            + H.a(
                f"{pPubNum} ⌲",
                f"{pubUrl}/project/{pPubNum}/index.html",
                target=published,
                cls="button large",
            )
        )

        if table == "project":
            return H.p(projectPubStr)

        ePubNum = edition.pubNum

        editionPubRow = (
            (
                H.i("Not published")
                if ePubNum is None or pPubNum is None
                else H.span("Published: ")
            ),
            H.a(
                f"{pPubNum}/{ePubNum} ⌲",
                f"{pubUrl}/project/{pPubNum}/edition/{ePubNum}/index.html",
                target=published,
                cls="button large",
            ),
        )

        can = dict(
            precheck=True,
            publish=ePubNum is None,
            unpublish=pPubNum is not None and ePubNum is not None,
            republish=pPubNum is not None and ePubNum is not None,
        )

        rows = []

        for kind, kindRep, tbRecRoles in (
            (
                "precheck",
                "check articles",
                (
                    ("edition", edition, "editor"),
                    ("project", project, "organiser"),
                    ("site", site, "admin"),
                    ("site", site, "root"),
                ),
            ),
            ("publish", "publish", (("project", project, "organiser"),)),
            (
                ("publishf", "publish"),
                "force-publish",
                (("project", project, "organiser"),),
            ),
            (
                "republish",
                "re-publish",
                (("site", site, "admin"), ("site", site, "root")),
            ),
            (
                ("republishf", "republish"),
                "force-re-publish",
                (("site", site, "admin"), ("site", site, "root")),
            ),
            (
                "unpublish",
                "un-publish",
                (("site", site, "admin"), ("site", site, "root")),
            ),
        ):
            asKind = kind

            if type(kind) is tuple:
                (kind, asKind) = kind

            if can[asKind]:
                rows.append(
                    (
                        H.span(f"You may {kindRep}:"),
                        H.iconx(
                            kind,
                            href=f"/{kind}/{recordId}",
                            cls="button large",
                        ),
                    )
                    if asKind in actions
                    else (
                        H.span(f"You may not {kindRep}"),
                        Auth.getInvolvedUsers(tbRecRoles, asString=True),
                    )
                )

        return H.table(
            [([(cell, {}) for cell in editionPubRow], {})],
            [([(cell, {}) for cell in row], {}) for row in rows],
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

    def getDataFile(self, table, record, path, content=False, lenient=False):
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
        content: boolean, optional False
            If True, delivers the content of the file, instead of the path
        lenient: boolean, optional False
            If True, do not complain if the file does not exist.

        Returns
        -------
        string
            The full path of the data file, if it exists.
            But if the `content` parameter is True, we deliver the content of the file.

            Otherwise, we raise an error that will lead to a 404 response, except
            when `lenient` is True.

        """
        Settings = self.Settings
        H = Settings.H
        Messages = self.Messages
        Auth = self.Auth

        workingDir = Settings.workingDir

        (site, siteId, projectId, project, editionId, edition) = self.context(
            table, record
        )

        urlBase = (
            ""
            if project is None
            else (
                f"project/{projectId}"
                if edition is None
                else f"project/{projectId}/edition/{editionId}"
            )
        )
        sep = "/" if urlBase else ""
        base = f"{workingDir}{sep}{urlBase}"

        dataPath = base if path is None else f"{base}/{path}"

        (table, recordId, record) = self.relevant(project=project, edition=edition)
        if recordId is None:
            Messages.error(msg="record does not exist")
            return ""

        permitted = Auth.authorise(table, record, action="read")

        fexists = fileExists(dataPath)

        if permitted and fexists:
            if content:
                with open(dataPath) as fh:
                    result = fh.read()
            else:
                result = dataPath
        else:
            result = (
                ""
                if content
                else dataPath if lenient else H.span(dataPath, cls="error")
            )

            if not lenient:
                logmsg = f"Accessing {dataPath}: "

                if not permitted:
                    logmsg += "not allowed. "
                if not fexists:
                    logmsg += "does not exist. "

                Messages.error(
                    msg=f"Accessing file {path}",
                    logmsg=logmsg,
                )
                result = "" if content else dataPath

        return result

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
        if not project:
            return ""

        projectUrl = f"/project/{projectId}"
        text = self.getValue("project", project, "title", manner="bare")
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

    def precheck(self, record):
        """Check the articles of an edition prior to publishing.

        Parameters
        ----------
        record: string
            The record of the edition to be checked.

        Return
        ------
        response
            A status response.

            It will also generate a a bunch of toc files in the edition.
        """
        Messages = self.Messages
        Mongo = self.Mongo
        Auth = self.Auth
        Publish = self.Publish

        (recordId, record) = Mongo.get("edition", record)
        if recordId is None:
            Messages.error(
                msg="record does not exist", logmsg=f"edition {recordId} does not exist"
            )
            return False

        permitted = Auth.authorise("edition", record, action="precheck")

        if not permitted:
            logmsg = f"Checking articles not permitted: edition: {recordId}"
            msg = "Checking articles of edition not permitted"
            Messages.warning(msg=msg, logmsg=logmsg)
            return False

        (siteId, site, projectId, project, editionId, edition) = self.context(
            "edition", record
        )

        return Publish.Precheck.checkEdition(project, editionId, edition)

    def publish(self, record, force):
        """Publish an edition.

        Parameters
        ----------
        record: string
            The record of the item to be published.
        force: boolean
            If True, ignore when some checks fail

        Return
        ------
        response
            A publish status response.
        """
        Messages = self.Messages
        Mongo = self.Mongo
        Auth = self.Auth
        Publish = self.Publish

        (recordId, record) = Mongo.get("edition", record)
        if recordId is None:
            Messages.error(
                msg="record does not exist", logmsg=f"edition {recordId} does not exist"
            )
            return False

        permitted = Auth.authorise("edition", record, action="publish")

        if not permitted:
            logmsg = f"Publish not permitted: edition: {recordId}"
            msg = "Publishing of edition not permitted"
            Messages.warning(msg=msg, logmsg=logmsg)
            return False

        (siteId, site, projectId, project, editionId, edition) = self.context(
            "edition", record
        )

        return Publish.updateEdition(site, project, edition, "add", force=force)

    def republish(self, record, force):
        """Re-ublish an edition.

        Parameters
        ----------
        record: string
            The record of the item to be re-published.
        force: boolean
            If True, ignore when some checks fail

        Return
        ------
        response
            A re-publish status response.
        """
        Messages = self.Messages
        Mongo = self.Mongo
        Auth = self.Auth
        Publish = self.Publish

        (recordId, record) = Mongo.get("edition", record)
        if recordId is None:
            Messages.error(
                msg="record does not exist", logmsg=f"edition {recordId} does not exist"
            )
            return False

        permitted = Auth.authorise("edition", record, action="republish")

        if not permitted:
            logmsg = f"Re-publish not permitted: edition: {recordId}"
            msg = "Re-publishing of edition not permitted"
            Messages.warning(msg=msg, logmsg=logmsg)
            return False

        (siteId, site, projectId, project, editionId, edition) = self.context(
            "edition", record
        )

        return Publish.updateEdition(
            site, project, edition, "add", force=force, again=True
        )

    def unpublish(self, record):
        """Unpublish an edition.

        Parameters
        ----------
        record: string
            The record of the item to be unpublished.

        Return
        ------
        response
            An unpublish status response.
        """
        Messages = self.Messages
        Mongo = self.Mongo
        Auth = self.Auth
        Publish = self.Publish

        (recordId, record) = Mongo.get("edition", record)
        if recordId is None:
            Messages.error(
                msg="record does not exist", logmsg=f"edition {recordId} does not exist"
            )
            return False

        permitted = Auth.authorise("edition", record, action="unpublish")

        if not permitted:
            logmsg = f"Unpublish not permitted: edition: {recordId}"
            msg = "Unpublishing of edition not permitted"
            Messages.warning(msg=msg, logmsg=logmsg)
            return False

        (siteId, site, projectId, project, editionId, edition) = self.context(
            "edition", record
        )

        return Publish.updateEdition(site, project, edition, "remove")

    def generate(self):
        """Regenerate the HTML for the published site.

        Not only the site wide files, but also all projects and editions.

        Return
        ------
        response
            A publish status response.
        """
        Messages = self.Messages
        Auth = self.Auth
        Publish = self.Publish

        site = self.relevant()[-1]
        permitted = Auth.authorise("site", site, action="republish")

        if not permitted:
            logmsg = "Generate pages is not permitted"
            msg = "Generate pages is not permitted"
            Messages.warning(msg=msg, logmsg=logmsg)
            return False

        return Publish.generatePages(True, True)

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
        if recordId is None:
            return jsonify(status=False, msgs=[["warning", "record does not exist"]])

        permitted = Auth.authorise(table, record, action="read")

        if not permitted:
            logmsg = f"Download not permitted: {table}: {recordId}"
            msg = f"Download of {table} not permitted"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msgs=[["warning", msg]])

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
        Messages.info(logmsg=f"CREATED TEMP DIR {dst}")

        good = True

        try:
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
                editions = Mongo.getList("edition", sort="title", projectId=projectId)

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
            Messages.info(msg=f"{table} downloaded")

        except Exception as e:
            msg = "Could not assemble the data for download"
            Messages.error(msg=msg, logmsg=msg)
            Messages.error(logmsg="".join(format_exception(e)), stop=False)
            good = False

        dirRemove(dst)
        Messages.info(logmsg=f"DELETED TEMP DIR {dst}")

        if good:
            headers = {
                "Expires": "0",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Content-Type": "application/zip",
                "Content-Disposition": f'attachment; filename="{fileName}"',
                "Content-Encoding": "identity",
            }

            return (zipData, headers)

        else:
            ref = getReferrer().removeprefix("/")
            return redirectStatus(f"/{ref}", False)

    def saveFile(self, record, key, path, fileName, targetFileName=None):
        """Saves a file in the context given by a record.

        The parameter `key` refers to a configuration section in the datamodel.
        This determines what file type to expect.
        We only accept files whose name has an extension that matches the expected
        file type.

        The key `modelz` expects a zip file with the files of an edition, in particular
        a scene file and model files. We make sure that these files have the
        proper type, and we also perform checks on the other parts of the zip file,
        namely whether they have decent paths.

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
        targetFileName: string, optional None
            The name of the file as which the uploaded file will be saved;
            if None, the file will be saved with the name from the request.

        Return
        ------
        response
            A json response with the status of the save operation:

            * a boolean: whether the save succeeded
            * a list of messages to display
            * content: new content for an upload control (only if successful)
        """
        fileContent = requestData()  # essential to have this early on in the body
        # if not, the error responses might go wrong in some browsers

        Settings = self.Settings
        H = Settings.H
        Messages = self.Messages
        Mongo = self.Mongo
        Auth = self.Auth
        workingDir = Settings.workingDir

        uploadConfig = self.getUploadConfig(key)
        table = uploadConfig.table

        (recordId, record) = Mongo.get(table, record)
        if recordId is None:
            return jsonify(status=False, msgs=[["warning", "record does not exist"]])

        permitted = Auth.authorise(table, record, action="update")

        saveName = fileName

        if targetFileName is not None:
            saveName = targetFileName

        filePath = f"{path}{saveName}"
        fileFullPath = f"{workingDir}/{filePath}"

        if not permitted:
            logmsg = f"Upload not permitted: {key}: {fileFullPath}"
            msg = f"Upload not permitted: {fileName}"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msgs=[["warning", msg]])

        (good, msgs) = self.checkFileContent(key, targetFileName, fileName, fileContent)

        if not good:
            return jsonify(status=False, msgs=msgs)

        if key == "modelz":
            destDir = f"{workingDir}/{path}"
            (good, msgs) = self.processModelZip(fileContent, destDir)
            if good:
                return jsonify(
                    status=True,
                    msgs=msgs,
                    content=H.b("Please refresh the page", cls="good"),
                )
            return jsonify(status=False, msgs=msgs)

        try:
            with open(fileFullPath, "wb") as fh:
                fh.write(fileContent)
        except Exception:
            logmsg = f"Could not save uploaded file: {key}: {fileFullPath}"
            msg = f"Uploaded file not saved: {fileName}"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msgs=[["warning", msg]])

        content = self.getUpload(
            record, key, fileName=targetFileName, bust=fileName, wrapped=False
        )

        return jsonify(status=True, msgs=[["good", "Done"]], content=content)

    def checkFileContent(self, key, targetFileName, fileName, fileContent):
        """Performs checks on the name and content of an uploaded file before saving it.

        Parameters
        ----------
        key: string
            The key of the upload. This key determines what kind of file we expect.
            If None, we do not expect a particular mime type
        targetFileName: string
            The prescribed name to save the file under, if None, it will be saved under
            the name mentioned in the request.
        fileName: string
            The name of the file as mentioned in the request.
        fileContent: bytes
            The content of the file as bytes

        Returns
        -------
        tuple
            A boolean that tells whether the file content looks OK plus a sequences of
            messages indicating what is wrong with the content.
        """
        Settings = self.Settings
        datamodel = Settings.datamodel
        mimeTypes = datamodel.mimeTypes
        uploadConfig = self.getUploadConfig(key) or AttrDict()
        acceptStr = uploadConfig.accept
        accept = (
            None
            if acceptStr is None
            else {acc[1:].strip() for acc in acceptStr.split(",")}
        )

        good = True
        msgs = []

        fileExt = extNm(fileName)

        if targetFileName is not None:
            targetExt = extNm(targetFileName)

            if targetExt != fileExt:
                good = False
                msgs.append(
                    [
                        "error",
                        (
                            f"the uploaded file name {fileName} has an extension "
                            "different from that of the target "
                            f"file name {targetFileName}"
                        ),
                    ]
                )

            if accept is not None and targetExt not in accept:
                good = False
                msgs.append(
                    [
                        "error",
                        (
                            "Programming error: the prescribed file name "
                            f"{targetFileName} has an extension not in {acceptStr}"
                        ),
                    ]
                )
                return (good, msgs)

            fileName = targetFileName
            fileExt = extNm(fileName)

        if accept is not None and fileExt not in accept:
            good = False
            msgs.append(
                (
                    "error",
                    (
                        f"the uploaded file name {fileName} has an extension "
                        f"not in {acceptStr}"
                    ),
                )
            )
            return (good, msgs)

        if fileExt == "gltf":
            (thisGood, messages) = check(fileContent)
            if thisGood:
                mimeType = "model/gltf+json"
            else:
                good = False
                msgs.extend([("error", msg) for msg in messages])
                mimeType = None
        else:
            mimeType = magic.from_buffer(fileContent, mime=True)
            if mimeType is None:
                good = False
                msgs.append(
                    (
                        "error",
                        (
                            f"could not determined the mime type of {fileName} "
                            "based on its uploaded content"
                        ),
                    )
                )

        if mimeType is not None:
            if (
                fileExt not in mimeTypes.get(mimeType, [])
                and mimeType.split("/", 1)[-1].split("+", 1)[0].lower()
                != fileExt.lower()
            ):
                good = False
                msgs.append(
                    (
                        "error",
                        (
                            f"the uploaded file content of {mimeType} file "
                            f"{fileName} does not fit its extension {fileExt}"
                        ),
                    )
                )

        return (good, msgs)

    def processModelZip(self, zf, destDir):
        """Processes zip data with a scene and model files.

        All files in the zip file will be examined, and those with
        extension svx.json will be saved as scene.svx.json at top level
        and those with extensions glb of gltf will be saved under their
        own names, also at top level.

        All other files will be saved as is, unless they have extension .svx.json,
        or .gltf or .glb.

        These files can end up in subdirectories.

        We do not check the file types of the member files other than the svx.json files
        and the model files (glb, gltf).
        If the file type for these files does not match their extensions, they will be
        ignored.

        The user is held responsible to submit a suitable file.

        Parameters
        ----------
        zf: bytes
            The raw zip data
        """
        Messages = self.Messages

        msgs = []
        good = True

        try:
            zf = BytesIO(zf)
            z = ZipFile(zf)

            allFiles = 0
            sceneFiles = set()
            modelFiles = set()
            otherFiles = set()

            goodFiles = []

            for zInfo in z.infolist():
                if zInfo.filename[-1] == "/":
                    continue
                if zInfo.filename.startswith("__MACOS"):
                    continue

                allFiles += 1

                zName = zInfo.filename
                zPath = zName.split("/")

                if len(zPath) == 1:
                    zDir, zFile = "", zPath[0]
                else:
                    zDir = "/".join(zPath[0:-1])
                    zFile = zPath[-1]

                zTest = zFile.lower()
                doFileTypeCheck = False

                if zTest.endswith(".svx.json"):
                    if zDir == "":
                        sceneFiles.add(zName)
                        doFileTypeCheck = True
                    else:
                        msgs.append(
                            ("warning", f"ignoring non-toplevel scene file {zName}")
                        )
                        continue
                elif zTest.endswith(".glb") or zTest.endswith(".gltf"):
                    if zDir == "":
                        modelFiles.add(zName)
                        doFileTypeCheck = True
                    else:
                        msgs.append(
                            ("warning", f"ignoring non-toplevel model file {zName}")
                        )
                        continue
                else:
                    otherFiles.add(zName)

                if doFileTypeCheck:
                    fileContent = z.read(zInfo)
                    (thisGood, theseMsgs) = self.checkFileContent(
                        None, None, zFile, fileContent
                    )
                    if thisGood:
                        goodFiles.append((zName, fileContent))
                    else:
                        good = False
                        msgs.extend(theseMsgs)
                else:
                    goodFiles.append((zInfo, None))

            if good:
                for zName, fileContent in goodFiles:
                    if fileContent is None:
                        z.extract(zName, path=destDir)
                    else:
                        with open(f"{destDir}/{zName}", mode="wb") as fh:
                            fh.write(fileContent)

            nScenes = len(sceneFiles)
            sLabel = "info" if nScenes == 1 else "warning"
            msgs.append(("info", f"All files in zip: {allFiles:>3}"))
            msgs.append((sLabel, f"Scene files: {nScenes:>3} x"))
            msgs.append(("info", f"Model files: {len(modelFiles):>3} x"))
            msgs.append(("info", f"Other files: {len(otherFiles):>3} x"))

        except Exception as e:
            good = False
            msgs.append(("error", "Something went wrong"))
            self.debug(f"XXXXXXXXXXXXXXXXXX {e}")
            Messages.warning(logmsg=str(e))

        return (good, msgs)

    def deleteFile(self, record, key, path, fileName, targetFileName=None):
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
        targetFileName: string, optional None
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
        if recordId is None:
            return jsonify(status=False, msgs=[["warning", "record does not exist"]])

        permitted = Auth.authorise(table, record, action="update")

        sep = "/" if path else ""
        filePath = f"{path}{sep}{fileName}"
        fileFullPath = f"{workingDir}/{filePath}"

        if not permitted:
            logmsg = f"Delete file not permitted: {key}: {fileFullPath}"
            msg = f"Delete not permitted: {fileName}"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msgs=[["warning", msg]])

        if not fileExists(fileFullPath):
            logmsg = f"File does not exist: {key}: {fileFullPath}"
            msg = f"File does not exist: {fileName}"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msgs=[["warning", msg]])

        try:
            fileRemove(fileFullPath)
        except Exception:
            logmsg = f"Could not delete file: {key}: {fileFullPath}"
            msg = f"File not deleted: {fileName}"
            Messages.warning(logmsg=logmsg)
            return jsonify(status=False, msgs=[["error", msg]])

        content = self.getUpload(
            record, key, fileName=targetFileName, bust=fileName, wrapped=False
        )

        return jsonify(status=True, msgs=[["good", "Done"]], content=content)
