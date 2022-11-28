from control.generic import AttrDict
from markdown import markdown


class Fields:
    def __init__(self, Settings, Messages, Mongo):
        """Factory for field objects.

        This class has methods to retrieve various pieces of content
        from the data sources, and hand it over to higher level objects.

        It is instantiated by a singleton object, which is a factory object
        for `control.fields.Field` objects, which deal with individual fields.

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

        self.fieldsConfig = Settings.fieldsConfig
        self.fieldObjects = AttrDict()

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

        fieldObject = Field(Messages, Mongo, key, **fieldsConfig)
        fieldObjects[key] = fieldObject
        return fieldObject


class Field:
    def __init__(self, Messages, Mongo, key, **kwargs):
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

    def formatted(self, record, level=None, button=""):
        """Give the formatted value of the field in a record.

        Optionally also puts a caption and/or an edit control.

        Parameters
        ----------
        record: AttrDict or dict
            The record in which the field  value is stored.
        level: integer, optional None
            The heading level in which a caption will be placed.
            If None, no caption will be placed.
        button: string, optional ""
            An optional edit button.

        Returns
        -------
        string:
            Whatever the value is that we find for that field, converted to HTML.
            If the field is not present, returns the empty string, without warning.
        """
        tp = self.tp
        caption = self.caption

        bare = self.bare(record)

        content = markdown(bare) if tp == "text" else bare

        sep = "&nbsp;" if button else ""

        content = f"{button}{sep}{content}"

        if level is not None:
            if "{}" in caption:
                heading = caption.format(content)
                content = ""
            else:
                heading = caption

            heading = f"""<h{level}>{heading}</h{level}>\n"""

        return heading + content
