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
        self.fieldObjects = AttrDict()

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

        fieldObject = fieldObjects.key
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
            It will be checked that certain parts of the field configuration
            are present, such as `nameSpace`, `fieldPath` and `tp`.
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
            The record in which the field  value is stored.

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
            The record in which the field  value is stored.
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
