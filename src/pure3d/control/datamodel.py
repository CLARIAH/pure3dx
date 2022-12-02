from markdown import markdown

from control.generic import AttrDict
from control.html import HtmlElements as H


class Datamodel:
    def __init__(self, Settings, Messages, Mongo):
        """Datamodel related operations.

        This class has methods to manipulate various pieces of content
        in the data sources, and hand it over to higher level objects.

        It can find out dependencies between related records, and it knows
        a thing or two about fields.

        It is instantiated by a singleton object.

        It has a method which is a factory for `control.fields.Field` objects,
        which deal with individual fields.

        Likewise it has a factory function for `control.fields.Upload` objects,
        which deal with file uploads.

        Parameters
        ----------
        Settings: `control.helpers.generic.AttrDict`
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
        self.masterConfig = datamodel.master
        self.linkConfig = datamodel.link
        self.fieldsConfig = datamodel.fields
        self.uploadsConfig = datamodel.uploads
        self.fieldObjects = AttrDict()
        self.uploadObjects = AttrDict()

    def getDetailRecords(self, masterTable, masterId):
        """Retrieve the detail records of a master record.

        It finds all records that have a field containing an id of the
        given master record.

        Details are not retrieved recursively, only the direct details
        of a master are fetched.

        Parameters
        ----------
        masterTable: string
            The name of the table in which the master record lives.
        masterId: ObjectId
            The id of the master record.

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
        masterConfig = self.masterConfig

        detailTables = masterConfig.get(masterTable, [])

        crit = {f"{masterTable.rstrip('s')}Id": masterId}

        detailRecords = AttrDict()

        for detailTable in detailTables:
            details = Mongo.getList(detailTable, **crit)
            if len(details):
                detailRecords[detailTable] = details

        return detailRecords

    def makeField(self, key):
        """Make a field object and registers it.

        An instance of class `control.fields.Field` is created,
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

        fieldObject = Field(Settings, Messages, Mongo, key, **fieldsConfig)
        fieldObjects[key] = fieldObject
        return fieldObject

    def makeUpload(self, key):
        """Make a file upload object and registers it.

        An instance of class `control.fields.Upload` is created,
        geared to this particular field.

        !!! note "Idempotent"
            If the Upload object is already registered, nothing is done.

        Parameters
        ----------
        key: string
            Identifier for the upload.
            The configuration for this upload will be retrieved using this key.
            The new upload object will be stored under this key.

        Returns
        -------
        object
            The resulting Upload object.
            It is also added to the `uploadObjects` member.
        """
        Settings = self.Settings

        uploadObjects = self.uploadObjects

        uploadObject = uploadObjects[key]
        if uploadObject:
            return uploadObject

        Messages = self.Messages
        Mongo = self.Mongo
        uploadsConfig = self.uploadsConfig

        uploadsConfig = uploadsConfig[key]
        if uploadsConfig is None:
            Messages.error(logmsg=f"Unknown upload key '{key}'")

        uploadObject = Upload(Settings, Messages, Mongo, key, **uploadsConfig)
        uploadObjects[key] = uploadObject
        return uploadObject


class Field:
    def __init__(self, Settings, Messages, Mongo, key, **kwargs):
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
        record: AttrDict or dict
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
        record: AttrDict or dict
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
        button="",
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
        record: AttrDict or dict
            The record in which the field value is stored.
        level: integer, optional None
            The heading level in which a caption will be placed.
            If None, no caption will be placed.
            If 0, the caption will be placed in a span.
        button: string, optional ""
            An optional edit button.
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
        tp = self.tp
        caption = self.caption

        logical = self.logical(record)

        if tp == "text":
            content = markdown(H.content(logical), tight=False)
        else:
            content = H.wrapValue(
                logical,
                outerElem="span",
                outerAtts=dict(cls=outerCls),
                innerElem="span",
                innerAtts=dict(cls=innerCls),
            )
        sep = "&nbsp;" if button else ""

        content = f"{button}{sep}{content}"

        if level is not None:
            if "{value}" in caption:
                kind = table.rstrip("s")
                heading = caption.format(kind=kind, value=content)
                content = ""
            else:
                heading = caption

            if level == 0:
                elem = "span"
                lv = []
            else:
                elem = "h"
                lv = [level]
            heading = H.elem(elem, *lv, heading)

        return heading + content


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
            Field configuration arguments.
            The following parts of the field configuration
            should be present: `table`, `field` and `relative`.
        """
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)
        self.Mongo = Mongo

        self.key = key
        """The identifier of this upload within the app.
        """

        self.table = None
        """The table in which the file name should be placed.
        """

        self.field = None
        """The field in which the file name should be placed.
        """

        self.relative = None
        """Indicates the directory where the actual file will be saved.

        Possibe values:

        * `site`: top level of the working data directory of the site
        * `project`: project directory of the project in question
        * `edition`: edition directory of the project in question

        If left out, the value will be derived from `table`.
        """

        self.accept = None
        """The file types that the field accepts.
        """

        self.caption = None
        """The text to display on the upload button.
        """

        self.show = None
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

        table = getattr(self, "table", None)
        field = getattr(self, "field", None)
        accept = getattr(self, "accept", None)

        for arg in ("table", "field", "relative", "accept", "caption", "show"):
            if getattr(self, arg, None) is None:
                if arg == "relative" and table is not None:
                    setattr(self, arg, table.removesuffix("s"))
                elif arg == "caption":
                    setattr(self, arg, f"{table}-{field}-{accept}")
                elif arg == "show":
                    setattr(self, arg, False)
                else:
                    Messages.error(logmsg=f"Missing info in Upload spec: {arg}")
                    good = False

        if not good:
            quit()

    def bare(self, record):
        """Give the bare file name as stored in a record in MongoDb.

        Parameters
        ----------
        record: AttrDict
            The record in which the file name is stored.

        Returns
        -------
        string:
            Whatever the value is that we find.
            If the field is not present, returns None, without warning.
        """
        field = self.field

        return record[field]

    def getPath(self, record):
        """Give the path to the file in question.

        The path can be used to build the static url and the save url.

        It does not contain the file name.
        If the path is non-empty, a "/" will be appended.
        """
        table = self.table
        relative = self.relative

        recordId = record._id
        projectId = recordId if table == "projects" else record.projectId
        editionId = recordId if table == "editions" else record.editionId

        path = (
            ""
            if relative == "site"
            else f"projects/{projectId}"
            if relative == "project"
            else f"projects/{projectId}/editions/{editionId}"
            if relative == "edition"
            else None
        )
        sep = "/" if path else ""
        return f"{path}{sep}"

    def formatted(self, record, mayChange=False):
        """Give the formatted value of a file field in a record.

        Optionally also puts an upload control.

        Parameters
        ----------
        record: AttrDict or dict
            The record in which the field value is stored.
        mayChange: boolean, optional False
            Whether the file may be changed.
            If so, an upload widget is supplied, wich contains a a delete button.

        Returns
        -------
        string:
            Whatever the value is that we find for that field, converted to HTML.
            If the field is not present, returns the empty string, without warning.
        """

        fileName = self.bare(record)

        Messages = self.Messages

        key = self.key
        table = self.table
        field = self.field
        relative = self.relative
        accept = self.accept
        caption = self.caption
        show = self.show

        title = f"click to upload a {caption}"

        recordId = record._id

        fid = f"{table}/{recordId}/{field}"

        path = self.getPath(record)
        if path is None:
            Messages.warning(
                logmsg=f"Wrong file path for upload {key} based on relative {relative}",
                msg="The location for this file cannot be determined",
            )

        if show:
            staticUrl = f"/data/{path}{fileName}"
            img = H.img(staticUrl, fid=fid)
        else:
            img = ""

        visual = img or H.span(fileName, cls="fieldinner")

        if not mayChange:
            return visual

        sep = "/" if path else ""
        saveUrl = f"/upload/{fid}{sep}{path}"

        if key == "model":
            self.debug(f"XXXX {fileName=} {accept=} {title=}")

        return H.content(
            visual, H.finput(fileName, accept, saveUrl, show=show, fid=fid, title=title)
        )
