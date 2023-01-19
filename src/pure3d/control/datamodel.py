import json
from markdown import markdown

from control.generic import AttrDict, now
from control.files import fileExists, listFilesAccepted


class Datamodel:
    def __init__(self, Settings, Messages, Mongo):
        """Datamodel related operations.

        This class has methods to manipulate various pieces of content
        in the data sources, and hand it over to higher level objects.

        It can find out dependencies between related records, and it knows
        a thing or two about fields.

        It is instantiated by a singleton object.

        It has a method which is a factory for `control.datamodel.Field` objects,
        which deal with individual fields.

        Likewise it has a factory function for `control.datamodel.Upload` objects,
        which deal with file uploads.

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

        datamodel = Settings.datamodel
        self.detailMaster = datamodel.detailMaster
        self.masterDetail = datamodel.masterDetail
        self.linkConfig = datamodel.link
        self.fieldsConfig = datamodel.fields
        self.uploadsConfig = datamodel.uploads
        self.fieldObjects = AttrDict()
        self.uploadObjects = AttrDict()

    def relevant(self, project=None, edition=None):
        """Get a relevant record and the table to which it belongs.

        A relevant record is either a project record, or an edition record,
        or the one and only site record.

        If all optional parameters are None, we look for the site record.
        If the project parameter is not None, we look for the project record.

        This is the inverse of `context()`.

        Paramenters
        -----------
        project: string | ObjectId | AttrDict, optional None
            The project whose record we need.
        edition: string | ObjectId | AttrDict, optional None
            The edition whose record we need.

        Returns
        -------
        tuple
            * table: string; the table in which the record is found
            * record id: string; the id of the record
            * record: AttrDict; the record itself

            If both project and edition are not None
        """
        Settings = self.Settings
        Mongo = self.Mongo

        if edition is not None:
            table = "edition"
            (recordId, record) = Mongo.get(table, edition)
        elif project is not None:
            table = "project"
            (recordId, record) = Mongo.get(table, project)
        else:
            table = "site"
            siteCrit = Settings.siteCrit
            record = Mongo.getRecord(table, **siteCrit)
            recordId = record._id

        return (table, recordId, record)

    def context(self, table, record):
        """Get the context of a record.

        Get the project and edition records to which the record belongs.

        Parameters
        ----------
        table: string
            The table in which the record sits.
        record: string
            The record.

        This is the inverse of `relevant()`.

        Returns
        -------
        tuple of tuple
            * (site, project, record)
            where the members are either None, or a full record
        """
        Mongo = self.Mongo

        (recordId, record) = Mongo.get(table, record)

        if table == "site":
            (editionId, edition) = (None, None)
            (projectId, project) = (None, None)
            (siteId, site) = (recordId, record)
        elif table == "project":
            (editionId, edition) = (None, None)
            (projectId, project) = (recordId, record)
            (siteId, site) = Mongo.get("site", record.siteId)
        elif table == "edition":
            (editionId, edition) = (recordId, record)
            (projectId, project) = Mongo.get("project", record.projectId)
            (siteId, site) = Mongo.get("site", project.siteId)

        return (siteId, site, projectId, project, editionId, edition)

    def getDetailRecords(self, masterTable, master):
        """Retrieve the detail records of a master record.

        It finds all records that have a field containing an id of the
        given master record.

        Details are not retrieved recursively, only the direct details
        of a master are fetched.

        Parameters
        ----------
        masterTable: string
            The name of the table in which the master record lives.
        master: string | ObjectId | AttrDict
            The master record.

        Returns
        -------
        AttrDict
            The list of detail records, categorized by detail table in which
            they occur. The detail tables are the keys, the lists of records
            in those tables are the values.
            If the master record cannot be found or if there are no detail
            records, the empty dict is returned.
        """
        Mongo = self.Mongo
        masterDetail = self.masterDetail

        detailTable = masterDetail[masterTable]
        if detailTable is None:
            return AttrDict()

        (masterId, master) = Mongo.get(masterTable, master)
        crit = {f"{masterTable}Id": masterId}

        detailRecords = AttrDict()

        details = Mongo.getList(detailTable, **crit)
        if len(details):
            detailRecords[detailTable] = details

        return detailRecords

    def makeField(self, key):
        """Make a field object and registers it.

        An instance of class `control.datamodel.Field` is created,
        geared to this particular field.

        !!! note "Idempotent"
            If the Field object is already registered, nothing is done.

        Parameters
        ----------
        key: string
            Identifier for the field.
            The configuration for this field will be retrieved using this key.
            The new field object will be stored under this key.

        Returns
        -------
        object
            The resulting Field object.
            It is also added to the `fieldObjects` member.
        """
        Settings = self.Settings

        fieldObjects = self.fieldObjects

        fieldObject = fieldObjects[key]
        if fieldObject:
            return fieldObject

        Messages = self.Messages
        Mongo = self.Mongo
        fieldsConfig = self.fieldsConfig

        fieldsConfig = fieldsConfig[key]
        if fieldsConfig is None:
            Messages.error(logmsg=f"Unknown field key '{key}'")

        fieldObject = Field(Settings, Messages, Mongo, self, key, **fieldsConfig)
        fieldObjects[key] = fieldObject
        return fieldObject

    def getFieldObject(self, key):
        """Get a field object.

        Parameters
        ----------
        key: string
            The key of the field object

        Returns
        -------
        object | void
            The field object found under the given key, if present, otherwise None
        """
        return self.fieldObjects[key]

    def makeUpload(self, key, fileName=None):
        """Make a file upload object and registers it.

        An instance of class `control.datamodel.Upload` is created,
        geared to this particular field.

        !!! note "Idempotent"
            If the Upload object is already registered, nothing is done.

        Parameters
        ----------
        key: string
            Identifier for the upload.
            The configuration for this upload will be retrieved using this key.
            The new upload object will be stored under this key.
        fileName: string, optional None
            If present, it indicates that the uploaded file will have this prescribed
            name.
            A file name for an upload object may also have been specified in
            the datamodel configuration.

        Returns
        -------
        object
            The resulting Upload object.
            It is also added to the `uploadObjects` member.
        """
        Settings = self.Settings

        uploadObjects = self.uploadObjects
        uploadsConfig = self.uploadsConfig

        if fileName is None:
            fileName = uploadsConfig.get(key, AttrDict()).fileName

        uploadObject = uploadObjects[(key, fileName)]
        if uploadObject:
            return uploadObject

        Messages = self.Messages
        Mongo = self.Mongo
        uploadsConfig = self.uploadsConfig

        uploadsConfig = AttrDict(**uploadsConfig[key])
        if uploadsConfig is None:
            Messages.error(logmsg=f"Unknown upload key '{key}'")
        if fileName is not None:
            uploadsConfig["fileName"] = fileName

        uploadObject = Upload(Settings, Messages, Mongo, key, **uploadsConfig)
        uploadObjects[(key, fileName)] = uploadObject
        return uploadObject

    def getUploadConfig(self, key):
        """Get an upload config.

        Parameters
        ----------
        key: string
            The key of the upload config

        Returns
        -------
        object | void
            The upload config found under the given key and file name, if
            present, otherwise None
        """
        return self.uploadsConfig[key]

    def getUploadObject(self, key, fileName=None):
        """Get an upload object.

        Parameters
        ----------
        key: string
            The key of the upload object
        fileName: string, optional None
            The file name of the upload object.
            If not passed, the file name is derived from the config of the key.

        Returns
        -------
        object | void
            The upload object found under the given key and file name, if
            present, otherwise None
        """
        if fileName is None:
            fileName = self.uploadsConfig[key].fileName
        return self.uploadObjects[(key, fileName)]

    def actionButton(
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
        Mongo = self.Mongo
        Auth = self.Auth

        (recordId, record) = Mongo.get(table, record)

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


class Field:
    def __init__(self, Settings, Messages, Mongo, Datamodel, key, **kwargs):
        """Handle field business.

        A Field object does not correspond with an individual field in a record.
        It represents a *column*, i.e. a set of fields with the same name in all
        records of a collection.

        First of all there is a method to retrieve the value of the field from
        a specific record.

        Then there are methods to deliver those values, either bare or formatted,
        to produce edit widgets to modify the values, and handlers to save
        values.

        How to do this is steered by the specification of the field by keys and
        values that are stored in this object.

        All field access should be guarded by the authorisation rules.

        Parameters
        ----------
        kwargs: dict
            Field configuration arguments.
            It certain parts of the field configuration
            are not present, defaults will be provided.
        """
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)
        self.Mongo = Mongo
        self.Datamodel = Datamodel

        self.key = key
        """The identifier of this field within the app.
        """

        self.nameSpace = ""
        """The first key to access the field data in a record.

        Example `dc` (Dublin Core). So if a record has Dublin Core
        metadata, we expect that metadata to exist under key `dc` in that record.

        If the namespace is `""`, it is assumed that we can dig up the values without
        going into a namespace subdocument first.
        """

        self.fieldPath = key
        """Compound selector in a nested dict.

        A string of keys, separated by `.`, which will be used to drill down
        into a nested dict. At the end of the path we find the selected value.

        This field selection is applied after the name space selection
        (if `nameSpace` is not the empty string).
        """

        self.tp = "string"
        """The value type of the field.

        Value types can be string, integer, but also date times, and values
        from an other collection (value lists).
        """

        self.caption = key
        """A caption that may be displayed with the field value.

        The caption may be a literal string with or without a placeholder `{}`.

        If there is no place holder, the caption will precede the content of
        the field.

        If there is a placeholder, the content will replace the place holder
        in the caption.
        """

        for (arg, value) in kwargs.items():
            if value is not None:
                setattr(self, arg, value)

    def logical(self, record):
        """Give the logical value of the field in a record.

        Parameters
        ----------
        record: string | ObjectId | AttrDict
            The record in which the field value is stored.

        Returns
        -------
        any:
            Whatever the value is that we find for that field.
            No conversion/casting to other types will be performed.
            If the field is not present, returns None, without warning.
        """
        nameSpace = self.nameSpace
        fieldPath = self.fieldPath

        fields = fieldPath.split(".")

        dataSource = record.get(nameSpace, {}) if nameSpace else record

        for field in fields[0:-1]:
            dataSource = dataSource.get(field, None)
            if dataSource is None:
                break

        value = None if dataSource is None else dataSource.get(fields[-1], None)
        return value

    def bare(self, record):
        """Give the bare string value of the field in a record.

        Parameters
        ----------
        record: string | ObjectId | AttrDict
            The record in which the field value is stored.

        Returns
        -------
        string:
            Whatever the value is that we find for that field, converted to string.
            If the field is not present, returns the empty string, without warning.
        """
        logical = self.logical(record)
        return "" if logical is None else str(logical)

    def formatted(
        self,
        table,
        record,
        level=None,
        editable=False,
        outerCls="fieldouter",
        innerCls="fieldinner",
    ):
        """Give the formatted value of the field in a record.

        Optionally also puts a caption and/or an edit control.

        The value retrieved is (recursively) wrapped in HTML, steered by additional
        argument, as in `control.html.HtmlElements.wrapValue`.
        be applied.

        If the type is 'text', multiple values will simply be concatenated
        with newlines in between, and no extra classes will be applied.
        Instead, a markdown formatter is applied to the result.

        For other types:

        If the value is an iterable, each individual value is wrapped in a span
        to which an (other) extra CSS class may be applied.

        Parameters
        ----------
        table: string
            The table from which the record is taken
        record: string | ObjectId | AttrDict
            The record in which the field value is stored.
        level: integer, optional None
            The heading level in which a caption will be placed.
            If None, no caption will be placed.
            If 0, the caption will be placed in a span.
        editable: boolean, optional False
            Whether the field is editable by the current user.
            If so, edit controls are provided.
        outerCls: string optional "fieldouter"
            If given, an extra CSS class for the outer element that wraps the total
            value. Only relevant if the type is not 'text'
        innerCls: string optional "fieldinner"
            If given, an extra CSS class for the inner elements that wrap parts of the
            value. Only relevant if the type is not 'text'

        Returns
        -------
        string:
            Whatever the value is that we find for that field, converted to HTML.
            If the field is not present, returns the empty string, without warning.
        """
        Settings = self.Settings
        Mongo = self.Mongo

        H = Settings.H

        (recordId, record) = Mongo.get(table, record)

        tp = self.tp
        caption = self.caption
        key = self.key

        bare = self.bare(record)

        if tp == "text":
            readonlyContent = markdown(bare, tight=False)
        else:
            readonlyContent = H.wrapValue(
                bare,
                outerElem="span",
                outerAtts=dict(cls=outerCls),
                innerElem="span",
                innerAtts=dict(cls=innerCls),
            )
        if editable:
            bareRep = json.dumps(bare.replace("'", "&apos;"))
            keyRepUrl = "" if key is None else f"/{key}"
            levelUrl = "" if level is None else f"/{level}"
            saveUrl = f"/save/{table}/{recordId}{keyRepUrl}{levelUrl}"
            updateButton = self.actionButtonClient(table, "update", key=key)
            cancelButton = self.actionButtonClient(table, "cancel", key=key)
            returnButton = self.actionButtonClient(table, "return", key=key)
            resetButton = self.actionButtonClient(table, "reset", key=key)
            saveButton = self.actionButtonClient(table, "save", key=key)
            msgs = H.div("", cls="editmsgs")
            editableContent = H.textarea(
                "", cls="editContent", saveurl=saveUrl, origValue=bareRep
            )

        if level is not None:
            if "{value}" in caption:
                theCaption = caption.format(kind=table, value=readonlyContent)
                inCaption = True
            else:
                theCaption = caption
                inCaption = False

            if level == 0:
                elem = "span"
                lv = []
            else:
                elem = "h"
                lv = [level]
            theCaption = H.elem(elem, *lv, theCaption)
        else:
            theCaption = ""
            inCaption = False

        return (
            H.span(
                [
                    "" if inCaption else theCaption,
                    H.span(
                        theCaption if inCaption else readonlyContent,
                        cls="readonlycontent",
                    ),
                    "&nbsp;",
                    editableContent,
                    updateButton,
                    cancelButton,
                    returnButton,
                    resetButton,
                    saveButton,
                    msgs,
                ],
                cls="editwidget",
            )
            if editable
            else theCaption + ("" if inCaption else readonlyContent)
        )

    def actionButtonClient(self, table, name, key=None, **atts):
        """Generates an action button to be activated by client side Javascript.

        It is assumed that the permission has already been checked.

        Parameters
        ----------

        Returns
        -------

        """
        Settings = self.Settings
        H = Settings.H

        href = "#"

        fullCls = "button small"
        return H.iconx(name, href=href, cls=fullCls, kind=name)


class Upload:
    def __init__(self, Settings, Messages, Mongo, key, **kwargs):
        """Handle upload business.

        An upload is like a field of type 'file'.
        The name of the uploaded file is stored in a record in MongoDb.
        The contents of the file is stored on the file system.

        A Upload object does not correspond with an individual field in a record.
        It represents a *column*, i.e. a set of fields with the same name in all
        records of a collection.

        First of all there is a method to retrieve the file name of an upload from
        a specific record.

        Then there are methods to deliver those values, either bare or formatted,
        to produce widgets to upload or delete the corresponding files.

        How to do this is steered by the specification of the upload by keys and
        values that are stored in this object.

        All upload access should be guarded by the authorisation rules.

        Parameters
        ----------
        kwargs: dict
            Upload configuration arguments.
            The following parts of the upload configuration
            should be present: `table`, `accept`, while `caption`, `fileName`,
            `show` are optional.
        """
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)
        self.Mongo = Mongo

        self.key = key
        """The identifier of this upload within the app.
        """

        self.table = kwargs.get("table", None)
        """Indicates the directory where the actual file will be saved.

        Possibe values:

        * `site`: top level of the working data directory of the site
        * `project`: project directory of the project in question
        * `edition`: edition directory of the project in question
        """

        self.accept = kwargs.get("accept", None)
        """The file types that the field accepts.
        """

        self.caption = kwargs.get("caption", f"{self.table} ({self.accept})")
        """The text to display on the upload button.
        """

        self.multiple = kwargs.get("multiple", False)
        """Whether multiple files of this type may be uploaded.
        """

        self.fileName = kwargs.get("fileName", None)
        """The name of the file once it is uploaded.

        The file name for the upload can be passed when the file name
        is known in advance.
        In that case, a file that is uploaded in this upload widget,
        will get this as prescribed file name, regardless of the file name in the
        upload request.

        Without a file name, the upload widget will show all existing files
        conforming to the `accept` setting, and will have a control to upload a
        new file.
        """

        self.show = kwargs.get("show", False)
        """Whether to show the contents of the file.

        This is typically the case when the file is an image to be presented
        as a logo.
        """

        # let attributes be filled in from the function **kwargs

        for (arg, value) in kwargs.items():
            if value is not None:
                setattr(self, arg, value)

        # try to fill in defaults for attributes that are still None

        good = True

        for arg in ("table", "accept"):
            if getattr(self, arg, None) is None:
                Messages.error(logmsg=f"Missing info in Upload spec: {arg}")
                good = False

        if not good:
            quit()

    def getDir(self, record):
        """Give the path to the file in question.

        The path can be used to build the static url and the save url.

        It does not contain the file name.
        If the path is non-empty, a "/" will be appended.

        Parameters
        ----------
        record: string | ObjectId | AttrDict
            The record relevant to the upload
        """
        table = self.table
        recordId = record._id

        projectId = (
            recordId
            if table == "project"
            else record.projectId
            if table == "edition"
            else None
        )
        editionId = recordId if table == "edition" else None

        path = (
            ""
            if table == "site"
            else f"project/{projectId}"
            if table == "project"
            else f"project/{projectId}/edition/{editionId}"
            if table == "edition"
            else None
        )
        sep = "/" if path else ""
        return f"{path}{sep}"

    def formatted(self, record, mayChange=False, bust=None, wrapped=True):
        """Give the formatted value of a file field in a record.

        Optionally also puts an upload control.

        Parameters
        ----------
        record: string | ObjectId | AttrDict
            The record relevant to the upload
        mayChange: boolean, optional False
            Whether the file may be changed.
            If so, an upload widget is supplied, wich contains a a delete button.
        bust: string, optional None
            If not None, the image url of the file whose name is passed in
            `bust` is made unique by adding the current time to it.
            This is a cache buster.
        wrapped: boolean, optional True
            Whether the content should be wrapped in a container element.
            See `control.html.HtmlElements.finput()`.

        Returns
        -------
        string
            The name of the uploaded file(s) and/or an upload control.
        """
        Settings = self.Settings
        H = Settings.H
        workingDir = Settings.workingDir

        key = self.key
        fileName = self.fileName
        accept = self.accept
        caption = self.caption
        show = self.show

        recordId = record._id

        fileNameRep = "-" if fileName is None else fileName
        fid = f"{recordId}/{key}/{fileNameRep}"

        path = self.getDir(record)
        sep = "/" if path else ""
        fullDir = f"{workingDir}{sep}{path}"
        saveUrl = f"/upload/{fid}{sep}{path}"
        deleteUrl = f"/deletefile/{fid}{sep}{path}".rstrip("/") + "/"

        if fileName is None:
            content = []
            for fileNm in listFilesAccepted(fullDir, accept, withExt=True):
                buster = (
                    f"?v={now()}"
                    if show and bust is not None and bust == fileNm
                    else ""
                )
                item = [fileNm, f"/data/{path}{fileNm}{buster}" if show else None]
                content.append(item)
        else:
            buster = (
                f"?v={now()}" if show and bust is not None and bust == fileName else ""
            )
            fullPath = f"{workingDir}/{path}{fileName}"
            exists = fileExists(fullPath)
            content = (
                fileName,
                exists,
                f"/data/{path}{fileName}{buster}" if show else None,
            )

        return H.finput(
            content,
            accept,
            mayChange,
            saveUrl,
            deleteUrl,
            caption,
            wrapped=wrapped,
            buttonCls="button small",
            cls=f"{key.lower()}",
        )
