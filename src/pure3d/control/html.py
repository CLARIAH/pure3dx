"""HTML generation made easy.

*   for each HTML element there is a function to wrap attributes and content in it.
*   additional support for more involved patches of HTML (`details`, `input`, icons)
*   escaping of HTML elements.

"""

AMP = "&"
LT = "<"
GT = ">"
APOS = "'"
QUOT = '"'
E = ""
MINONE = "-1"
ZERO = "0"
ONE = "1"
NBSP = "\u00a0"

CLS = "cls"
CLASS = "class"

TP = "tp"
TYPE = "type"

EMPTY_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}

# study url_for


class HtmlElement:
    """Wrapping of attributes and content into an HTML element."""

    def __init__(self, name):
        """## Initialization

        An HtmlElement object.

        Parameters
        ----------
        name: string
            See below.
        """

        self.name = name
        """*string* The element name.
        """

    @staticmethod
    def atNormal(k):
        """Normalize the names of attributes.

        Substitute the `cls` attribute name with `class`.

        Substitute the `tp` attribute name with `type`.
        """

        return CLASS if k == CLS else TYPE if k == TP else k

    @staticmethod
    def atEscape(v):
        """Escapes double quotes in attribute values."""

        return v.replace('"', "&quot;")

    @classmethod
    def attStr(thisCls, atts, addClass=None):
        """Stringify attributes.

        !!! hint
            Attributes with value `True` are represented as bare attributes, without
            value. For example: `{open=True}` translates into `open`.
            Attributes with value `False` are omitted.

        !!! caution
            Use the name `cls` to get a `class` attribute inside an HTML element.
            The name `class` interferes too much with Python syntax to be usable
            as a keyowrd argument.

        Parameters
        ----------
        atts: dict
            A dictionary of attributes.
        addClass: string
            An extra `class` attribute. If there is already a class attribute
            `addClass` will be appended to it.
            Otherwise a fresh class attribute will be created.

        Returns
        -------
        string
            The serialzed attributes.
        """

        if addClass:
            if atts and CLS in atts:
                atts[CLS] += f" {addClass}"
            elif atts:
                atts[CLS] = addClass
            else:
                atts = dict(cls=addClass)
        return E.join(
            f""" {thisCls.atNormal(k)}"""
            + (E if v is True else f'''="{thisCls.atEscape(v)}"''')
            for (k, v) in atts.items()
            if v is not None and v is not False
        )

    def wrap(self, material, addClass=None, **atts):
        """Wraps attributes and content into an element.

        !!! caution
            No HTML escaping of special characters will take place.
            You have to use `control.html.HtmlElements.he` yourself.

        Parameters
        ----------
        material: string | iterable
            The element content. If the material is not a string but another
            iterable, the items will be joined by the empty string.

        addClass: string
            An extra `class` attribute. If there is already a class attribute
            `addClass` will be appended to it.
            Otherwise a fresh class attribute will be created.

        Returns
        -------
        string
            The serialzed element.

        """

        name = self.name
        content = asString(material)
        attributes = self.attStr(atts, addClass=addClass)
        return (
            f"""<{name}{attributes}>"""
            if name in EMPTY_ELEMENTS
            else f"""<{name}{attributes}>{content}</{name}>"""
        )


class HtmlElements:
    """Wrap specific HTML elements and patterns.

    !!! note
        Nearly all elements accept an arbitrary supply of attributes
        in the `**atts` parameter, which will not further be documented.
    """

    def __init__(self, Settings, Messages):
        """Gives the HtmlElements access to Settings and Messages.
        """
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)

    amp = "&amp;"
    lt = "&lt;"
    gt = "&gt;"
    apos = "&apos;"
    quot = "&quot;"
    nbsp = NBSP

    @classmethod
    def he(cls, val):
        """Escape HTML characters.

        The following characters will be replaced by entities:
        ```
        & < ' "
        ```

        The dollar sign will be wrapped into a `<span>`.
        """

        return (
            E
            if val is None
            else (
                str(val)
                .replace(AMP, cls.amp)
                .replace(LT, cls.lt)
                .replace(APOS, cls.apos)
                .replace(QUOT, cls.quot)
            )
        )

    @staticmethod
    def content(*material, tight=True):
        """fragment.

        This is a pseudo element.
        The material will be joined together, without wrapping it in an element.
        There are no attributes.

        The material is recursively joined into a string.

        Parameters
        ----------
        material: string | iterable
            Every argument in `material` may be None, a string, or an iterable.
        tight: boolean, optional False
            If True, all material will be joined tightly, with no intervening string.
            Otherwise, all pieces will be joined with a newline.

        Returns
        -------
        string(html)
        """

        return asString(material, tight=tight)

    @classmethod
    def wrapValue(
        thisCls,
        value,
        _level=0,
        outerElem="div",
        outerArgs=[],
        outerAtts={},
        innerElem="span",
        innerArgs=[],
        innerAtts={},
    ):
        """Wraps one or more values in elements.

        The value is recursively joined into elements.
        The value at the outermost level the result is wrapped in a single
        outer element.
        All nested values are wrapped in inner elements.

        If the value is None, a bare empty string is returned.

        The structure of elements reflects the structure of the value.

        Parameters
        ----------
        value: string | iterable
            Every argument in `value` may be None, a string, or an iterable.
        outerElem: string, optional "div"
            The single element at the outermost level
        outerArgs: list, optional []
            Arguments for the outer element.
        outerAtts: dict, optional {}
            Attributes for the outer element.
        innerElem: string, optional "span"
            The elements at all deeper levels
        innerArgs: list, optional []
            Arguments for the inner elements.
        innerAtts: dict, optional {}
            Attributes for the inner elements.

        Returns
        -------
        string(html)
        """

        if value is None:
            return E

        def _wrapValue(value, isOuter):
            """Inner function to be called recursively.
            """
            if isOuter:
                elem = outerElem
                args = outerArgs
                atts = outerAtts
            else:
                elem = innerElem
                args = innerArgs
                atts = innerAtts

            isMany = isIterable(value)

            if value is None or type(value) is str or not isMany:
                return thisCls.elem(elem, str(value or ""), *args, **atts)

            return thisCls.elem(
                elem,
                [_wrapValue(val, False) for val in value],
                *args,
                **atts,
            )

        return _wrapValue(value, True)

    @classmethod
    def elem(thisClass, tag, *args, **kwargs):
        """Wraps an element whose tag is determined at run time.

        You can also use this to wrap non-html elements.

        Parameters
        ----------
        thisClass: class
            The current class
        tag: string
            The name of the element
        *args, **kwargs: any
            The remaining arguments to be passed to the underlying wrapper.
        """
        method = getattr(thisClass, tag, None)
        return (
            HtmlElement(tag).wrap(*args, **kwargs)
            if method is None
            else method(*args, **kwargs)
        )

    @staticmethod
    def a(material, href, **atts):
        """A.

        Hyperlink.

        Parameters
        ----------
        material: string | iterable
            Text of the link.
        href: url
            Destination of the link.

        Returns
        -------
        string(html)
        """

        return HtmlElement("a").wrap(material, href=href, **atts)

    @staticmethod
    def b(material, **atts):
        """B.

        Bold element.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement("b").wrap(material, **atts)

    @staticmethod
    def body(material, **atts):
        """BODY.

        The <body> part of a document

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement("body").wrap(material, **atts)

    @staticmethod
    def br():
        """BR.

        Line break.

        Returns
        -------
        string(html)
        """

        return HtmlElement("br").wrap(E)

    @staticmethod
    def button(material, tp, **atts):
        """BUTTON.

        A clickable button

        Parameters
        ----------
        material: string | iterable
            What is displayed on the button.
        tp:
            The type of the button, e.g. `submit` or `button`

        Returns
        -------
        string(html)
        """

        return HtmlElement("button").wrap(material, tp=tp, **atts)

    @staticmethod
    def code(material, **atts):
        """CODE.

        Code element.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement("code").wrap(material, **atts)

    @staticmethod
    def checkbox(var, **atts):
        """INPUT type=checkbox.

        The element to receive user clicks.

        Parameters
        ----------
        var: string
            The name of an identifier for the element.

        Returns
        -------
        string(html)
        """

        return HtmlElement("input").wrap(
            E,
            tp="checkbox",
            id=var,
            addClass="option",
            **atts,
        )

    @staticmethod
    def dd(material, **atts):
        """DD.

        The definition part of a term.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement("dd").wrap(material, **atts)

    @staticmethod
    def details(summary, material, itemkey, **atts):
        """DETAILS.

        Collapsible details element.

        Parameters
        ----------
        summary: string | iterable
            The summary.
        material: string | iterable
            The expansion.
        itemkey: string
            Identifier for reference from Javascript.

        Returns
        -------
        string(html)
        """

        content = asString(material)
        return HtmlElement("details").wrap(
            HtmlElement("summary").wrap(summary) + content, itemkey=itemkey, **atts
        )

    def detailx(
        self,
        detailIcons,
        material,
        itemkey,
        openAtts={},
        closeAtts={},
        **atts,
    ):
        """detailx.

        Collapsible details pseudo element.

        Unlike the HTML `details` element, this one allows separate open and close
        controls. There is no summary.

        !!! warning
            The `icon` names must be listed in the web.yaml config file
            under the key `icons`. The icon itself is a Unicode character.

        !!! hint
            The `atts` go to the outermost `div` of the result.

        Parameters
        ----------
        detailIcons: string | (string, string)
            Names of the icons that open and close the element.
        itemkey: string
            Identifier for reference from Javascript.
        openAtts: dict, optinal, `{}`
            Attributes for the open icon.
        closeAtts: dict, optinal, `{}`
            Attributes for the close icon.

        Returns
        -------
        string(html)
        """
        Settings = self.Settings
        icons = Settings.icons

        content = asString(material)
        (iconOpen, iconClose) = (
            (detailIcons, detailIcons) if type(detailIcons) is str else detailIcons
        )
        triggerElements = [
            (self.iconx if icon in icons else self.span)(
                icon,
                itemkey=itemkey,
                trigger=value,
                **triggerAtts,
            )
            for (icon, value, triggerAtts) in (
                (iconOpen, ONE, openAtts),
                (iconClose, MINONE, closeAtts),
            )
        ]
        return (
            *triggerElements,
            HtmlElement("div").wrap(content, itemkey=itemkey, body=ONE, **atts),
        )

    @staticmethod
    def div(material, **atts):
        """DIV.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement("div").wrap(material, **atts)

    @staticmethod
    def dl(items, **atts):
        """DL.

        Definition list.

        Parameters
        ----------
        items: iterable of (string, string)
            These are the list items, which are term-definition pairs.

        Returns
        -------
        string(html)
        """

        return HtmlElement("dl").wrap(
            [
                HtmlElement("dt").wrap(item[0]) + HtmlElement("dd").wrap(item[1])
                for item in items
            ],
            **atts,
        )

    @staticmethod
    def dt(material, **atts):
        """DT.

        Term of a definition.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement("dt").wrap(material, **atts)

    @staticmethod
    def h(level, material, **atts):
        """H1, H2, H3, H4, H5, H6.

        Parameters
        ----------
        level: int
            The heading level.
        material: string | iterable
            The heading content.

        Returns
        -------
        string(html)
        """

        return HtmlElement(f"h{level}").wrap(material, **atts)

    @staticmethod
    def head(material, **atts):
        """HEAD.

        The <head> part of a document

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement("head").wrap(material, **atts)

    @staticmethod
    def i(material, **atts):
        """I.

        Italic element.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement("i").wrap(material, **atts)

    def icon(self, icon, text=None, asChar=False, **atts):
        """icon.

        Pseudo element for an icon.

        !!! warning
            The `icon` names must be listed in the settings.yml config file
            under the key `icons`. The icon itself is a Unicode character.

        Parameters
        ----------
        icon: string
            Name of the icon.
        text: string, optional, `None`
            Extra text that will be placed in front of the icon.
        asChar: boolean, optional, `False`
            If `True`, just output the icon character.
            Otherwise, wrap it in a `<span>` with all
            attributes that might have been passed.

        Returns
        -------
        string(html)
        """
        Settings = self.Settings
        icons = Settings.icons

        iconChar = icons.get(icon, icons["noicon"])

        if asChar:
            return icons.get(icon, icons["noicon"])

        addClass = f"symbol i-{icon} "
        return HtmlElement("span").wrap(
            (text or "") + iconChar, addClass=addClass, **atts
        )

    def iconx(self, icon, text=None, href=None, **atts):
        """iconx.

        Pseudo element for a clickable icon.
        It will be wrapped in an `<a href="...">...</a>` element or a <span...>
        if `href` is `None`.

        If `href` is the empty string, the element will still be wrapped in
        an `<a ...>` element, but without a `href` attribute.

        !!! warning
            The `icon` names must be listed in the settings.yml config file
            under the key `icons`. The icon itself is a Unicode character.

        Parameters
        ----------
        icon: string
            Name of the icon.
        text: string, optional, `None`
            Extra text that will be placed in front of the icon.
        href: url, optional, `None`
            Destination of the icon when clicked.
            Will be left out when equal to the empty string.

        Returns
        -------
        string(html)
        """
        Settings = self.Settings
        icons = Settings.icons
        iconTips = Settings.iconTips

        iconChar = icons.get(icon, icons["noicon"])
        addClass = f"icon i-{icon} "
        if href:
            atts["href"] = href

        if "title" not in atts:
            title = iconTips.get(icon, None)
            if title is not None:
                atts["title"] = title

        return HtmlElement("span" if href is None else "a").wrap(
            (text or "") + iconChar, addClass=addClass, **atts
        )

    def actionButton(self, name, kind=None, **atts):
        """Generates an action button to be activated by client side Javascript.

        It is assumed that the permission has already been checked.

        Parameters
        ----------
        H: object
            The `control.html.HtmlElements` object

        name: string
            The name of the icon as displayed on the button

        kind: string, optional None
            The kind of the button, passed on in attribute `kind`, can be
            used by Javascript to identify this button.
            If `None`, the kind is set to the value of the `name` parameter.

        Returns
        -------
        string
            The HTML of the button.

        """
        return self.iconx(name, href="#", cls="button small", kind=name, **atts)

    @staticmethod
    def iframe(src, **atts):
        """IFRAME.

        An iframe, which is an empty element with an obligatory end tag.

        Parameters
        ----------
        src: url
            Source for the iframe.

        Returns
        -------
        string(html)
        """

        return HtmlElement("iframe").wrap("", src=src, **atts)

    def img(self, src, href=None, title=None, imgAtts={}, **atts):
        """IMG.

        Image element.

        !!! note
            The `atts` go to the outer element, which is either `<img>` if it is
            not further wrapped, or `<a>`.
            The `imgAtts` only go to the `<img>` element.

        Parameters
        ----------
        src: url
            The url of the image.
        href: url, optional, `None`
            The destination to navigate to if the image is clicked.
            The images is then wrapped in an `<a>` element.
            If missing, the image is not wrapped further.
        title: string, optional, `None`
            Tooltip.
        imgAtts: dict, optional {}
            Attributes that go to the `<img>` element.

        Returns
        -------
        string(html)
        """

        return (
            self.a(
                HtmlElement("img").wrap(E, src=src, **imgAtts),
                href,
                title=title,
                **atts,
            )
            if href
            else HtmlElement("img").wrap(E, src=src, title=title, **imgAtts, **atts)
        )

    def input(self, material, tp, **atts):
        """INPUT.

        The element to receive types user input.

        !!! caution
            Do not use this for checkboxes. Use
            `control.html.HtmlElements.checkbox` instead.

        !!! caution
            Do not use this for file inputs. Use
            `control.html.HtmlElements.finput` instead.

        Parameters
        ----------
        tp: string
            The type of input
        material: string | iterable
            This goes into the `value` attribute of the element, after HTML escaping.

        Returns
        -------
        string(html)
        """

        content = asString(material)
        return HtmlElement("input").wrap(E, tp=tp, value=self.he(content), **atts)

    def finput(
        self,
        content,
        accept,
        mayChange,
        saveUrl,
        deleteUrl,
        caption,
        cls="",
        buttonCls="",
        wrapped=True,
        **atts,
    ):
        """INPUT type="file".

        The input element for uploading files.

        If the user does not have `update` permission, only information about
        currently uploaded file(s) is presented.

        But if the user does have upload permission, there will be an additional control
        to update a new file and there will be controls to delete existing files.

        Parameters
        ----------
        content: list or tuple
            The widget handles to cases:

            * 1 single file with a prescribed name.
            * no prescribed name, lists all files that match the
              `accept` parameter.

            In the first case, `content` is a tuple consisting of

            * file name
            * whether the file exists
            * a url to load the file as image, or None

            In the second case, `content` is a list containing a tuple for each file:

            * file name
            * a url to load the file as image, or None

            And in this case, all files exist.

            In both cases, a delete control will be added to each file, if allowed.

            If an image url is present, the contents of the file will be
            displayed as an img element.
        accept: string
            MIME type of uploaded file
        mayChange: boolean
            Whether the user is allowed to upload new files and delete existing files.
        saveUrl: string
            The url to which the resulting file should be posted.
        deleteUrl: string
            The url to use to delete a file, with the understanding that the
            file name should be appended to it.
        caption: string
            basis for tooltips for the upload and delete buttons
        cls: string, optional ""
            CSS class for the outer element
        buttonCls: string, optional ""
            CSS class for the buttons
        wrapped: boolean, optional True
            Whether the content should be wrapped in a container element.
            If so, the container element carries a class attribute filled
            with `cls`, and all attributes specified in the `atts` argument.
            This generates a new widget on the page.

            If False, only the content is passed. Use this if the content
            of an existing widget has changed and must be inserted in
            that widget. The outer element of the widget is not changed.

        Returns
        -------
        string(html)
        """

        if type(content) is tuple:
            prescribed = True
            items = [content]
            outerCls = "fileswidgetsingle"
        else:
            prescribed = False
            items = [(file, True, imgUrl) for (file, imgUrl) in content]
            outerCls = "fileswidgetmulti"

        html = []

        for (file, exists, imgUrl) in items:
            fileRep = self.he(file)

            itemCls = "withimage" if imgUrl else "withoutimage"
            label = (
                (
                    self.img(imgUrl, title=file, cls="content")
                    if exists
                    else self.icon(
                        "noexist", imgurl=imgUrl, title=f"{file} does not exist"
                    )
                )
                if imgUrl
                else self.span(
                    [self.icon("exist" if exists else "noexist"), fileRep]
                    if prescribed
                    else fileRep,
                    cls="filename",
                )
            )
            deleteControl = ""
            inputControl = ""
            uploadControl = ""

            if mayChange:
                if exists:
                    deleteControl = self.icon(
                        "delete",
                        cls=f"delete {buttonCls}",
                        title=f"delete {caption}",
                        url=f"{deleteUrl}{file}",
                    )
                if prescribed:
                    inputControl = self.input(fileRep, "file", accept=accept)
                    uploadControl = self.iconx(
                        "upload", cls=f"upload {buttonCls}", title=f"upload {caption}"
                    )

            html.append(
                self.span(
                    [inputControl, label, deleteControl, uploadControl], cls=itemCls
                )
            )

        if mayChange and not prescribed:
            label = self.span(f"Upload file ({accept})", cls="filenamex")
            inputControl = self.input(None, "file", accept=accept)
            uploadControl = self.iconx(
                "upload",
                text=label,
                cls=f"upload {buttonCls}",
                title=f"upload {caption}",
            )
            html.append(self.span([inputControl, uploadControl]))

        return (
            self.span(
                html,
                saveurl=saveUrl,
                cls=f"fileupload {outerCls} {cls}",
                **atts,
            )
            if wrapped
            else "".join(html)
        )

    @staticmethod
    def link(rel, href, **atts):
        """LINK.

        Typed hyperlink in the <head> element.

        Parameters
        ----------
        rel: string:
            The type of the link
        href: url
            Destination of the link.

        Returns
        -------
        string(html)
        """

        return HtmlElement("link").wrap(E, rel=rel, href=href, **atts)

    @staticmethod
    def meta(**atts):
        """META.

        A <meta> element inside the <head> part of a document

        Returns
        -------
        string(html)
        """

        return HtmlElement("meta").wrap(E, **atts)

    @staticmethod
    def p(material, **atts):
        """P.

        Paragraph.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement("p").wrap(material, **atts)

    @staticmethod
    def script(material, **atts):
        """SCRIPT.

        Parameters
        ----------
        material: string | iterable
            The Javascript.

        Returns
        -------
        string(html)
        """

        return HtmlElement("script").wrap(material, **atts)

    @staticmethod
    def small(material, **atts):
        """SMALL.

        Small element.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement("small").wrap(material, **atts)

    @staticmethod
    def span(material, **atts):
        """SPAN.

        Inline element.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement("span").wrap(material, **atts)

    def table(self, headers, rows, **atts):
        """TABLE.

        The table element.

        Parameters
        ----------
        headers, rows: iterables of iterables
            An iterable of rows.
            Each row is a tuple: an iterable of cells, and a dict of atts for the row.
            Each cell is a tuple: material for the cell, and a dict of atts for the cell.

        !!! note
            Cells in normal rows are wrapped in `<td>`, cells in header rows go
            into `<th>`.

        Returns
        -------
        string(html)
        """

        th = HtmlElement("th").wrap
        td = HtmlElement("td").wrap
        headerMaterial = self.wrapTable(headers, th)
        rowMaterial = self.wrapTable(rows, td)
        material = HtmlElement("tbody").wrap(headerMaterial + rowMaterial)
        return HtmlElement("table").wrap(material, **atts)

    @staticmethod
    def textarea(material, **atts):
        """TEXTAREA.

        Input element for larger text, typically Markdown.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        content = asString(material)
        return HtmlElement("textarea").wrap(content, **atts)

    @staticmethod
    def wrapTable(data, td):
        """Rows and cells.

        Parameters
        ----------
        data: iterable of iterables.
            Rows and cells within them, both with dicts of atts.
        td: function
            Funnction for wrapping the cells, typically boiling down
            to wrapping them in either `<th>` or `<td>` elements.

        Returns
        -------
        string(html)
        """

        tr = HtmlElement("tr").wrap
        material = []
        for (rowData, rowAtts) in data:
            rowMaterial = []
            for (cellData, cellAtts) in rowData:
                rowMaterial.append(td(cellData, **cellAtts))
            material.append(tr(rowMaterial, **rowAtts))
        return material


def asString(value, tight=True):
    """Join an iterable of strings or iterables into a string.

    And if the value is already a string, return it, and if it is `None`
    return the empty string.

    The material is recursively joined into a string.

    Parameters
    ----------
    value: string | iterable | void
        Every argument in `value` may be None, a string, or an iterable.
    tight: boolean, optional False
        If True, all material will be joined tightly, with no intervening string.
        Otherwise, all pieces will be joined with a newline.

    Returns
    -------
    string(html)
    """

    sep = E if tight else "\n"

    return (
        E
        if value is None
        else value
        if type(value) is str
        else sep.join(asString(val, tight=tight) for val in value)
        if isIterable(value)
        else str(value)
    )


def isIterable(value):
    """Whether a value is a non-string iterable.

    !!! note
        Strings are iterables.
        We want to know whether a value is a string or an iterable of strings.
    """

    return type(value) is not str and hasattr(value, "__iter__")
