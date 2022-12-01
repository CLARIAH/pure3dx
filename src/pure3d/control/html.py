"""HTML generation made easy.

*   for each HTML element there is a function to wrap attributes and content in it.
*   additional support for more involved patches of HTML (`details`, `input`, icons)
*   escaping of HTML elements.

"""

from control.generic import AttrDict

AMP = "&"
LT = "<"
GT = ">"
APOS = "'"
QUOT = '"'
E = ""
MINONE = "-1"
ZERO = "0"
ONE = "1"

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

ICONS = AttrDict(
    chain="⚭",
    check="✔︎",
    clear="✖︎",
    cross="✘",
    delete="🗑",
    devel="⚒︎",
    edit="✎",
    info="ℹ︎",
    create="✦",
    missing="☒",
    noicon="☹︎",
    none="○",
    ok="↩︎",
    prov="⌚︎",
    refresh="♺",
)

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
            if v is not None
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

    @staticmethod
    def he(val):
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
                .replace(AMP, """&amp;""")
                .replace(LT, """&lt;""")
                .replace(APOS, """&apos;""")
                .replace(QUOT, """&quot;""")
            )
        )

    @staticmethod
    def amp():
        return "&amp;"

    @staticmethod
    def lt():
        return "&lt;"

    @staticmethod
    def gt():
        return "&gt;"

    @staticmethod
    def apos():
        return "&apos;"

    @staticmethod
    def quot():
        return "&quot;"

    @staticmethod
    def content(*material, tight=False):
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
        The at the outermost level the result is wrapped in a single outer element.
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

        if _level == 0:
            elem = outerElem
            args = outerArgs
            atts = outerAtts
        else:
            elem = innerElem
            args = innerArgs
            atts = innerAtts

        isMany = isIterable(value)

        if type(value) is str or not isMany:
            if _level == 0:
                elem = outerElem
                args = outerArgs
                atts = outerAtts
            else:
                elem = innerElem
                args = innerArgs
                atts = innerAtts
            return thisCls.elem(elem, thisCls.he(str(value)), *args, **atts)

        return thisCls.elem(
            elem,
            [
                thisCls.wrapValue(
                    val,
                    _level=_level + 1,
                    outerElem=innerElem,
                    outerArgs=innerArgs,
                    outerAtts=innerAtts,
                    innerElem=innerElem,
                    innerArgs=innerArgs,
                    innerAtts=innerAtts,
                )
                for val in value
            ],
            *args,
            **atts,
        )

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

        A clickable butto

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

    @staticmethod
    def detailx(
        icons,
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
        icons: string | (string, string)
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

        content = asString(material)
        (iconOpen, iconClose) = (icons, icons) if type(icons) is str else icons
        triggerElements = [
            (HtmlElements.iconx if icon in ICONS else HtmlElements.span)(
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
    def icon(icon, asChar=False, **atts):
        """icon.

        Pseudo element for an icon.

        !!! warning
            The `icon` names must be listed in the authorise.yaml config file
            under the key `icons`. The icon itself is a Unicode character.

        Parameters
        ----------
        icon: string
            Name of the icon.
        asChar: boolean, optional, `False`
            If `True`, just output the icon character.
            Otherwise, wrap it in a `<span>` with all
            attributes that might have been passed.

        Returns
        -------
        string(html)
        """

        iconChar = ICONS.get(icon, default=ICONS["noicon"])
        if asChar:
            return ICONS.get(icon, default=ICONS["noicon"])
        addClass = f"symbol i-{icon} "
        return HtmlElement("span").wrap(iconChar, addClass=addClass, **atts)

    @staticmethod
    def iconx(icon, href=None, **atts):
        """iconx.

        Pseudo element for a clickable icon.
        It will be wrapped in an `<a href="...">...</a>` element or a <span...>
        if `href` is `None`.

        If `href` is the empty string, the element will still be wrapped in
        an `<a ...>` element, but without a `href` attribute.

        !!! warning
            The `icon` names must be listed in the web.yaml config file
            under the key `icons`. The icon itself is a Unicode character.

        Parameters
        ----------
        icon: string
            Name of the icon.
        href: url, optional, `None`
            Destination of the icon when clicked.
            Will be left out when equal to the empty string.

        Returns
        -------
        string(html)
        """

        iconChar = ICONS.get(icon, default=ICONS["noicon"])
        addClass = f"icon i-{icon} "
        if href:
            atts["href"] = href

        return HtmlElement("span" if href is None else "a").wrap(
            iconChar, addClass=addClass, **atts
        )

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

    @staticmethod
    def img(src, href=None, title=None, imgAtts={}, **atts):
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
        imgAtts: dict, optional `{}`
            Attributes that go to the `<img>` element.

        Returns
        -------
        string(html)
        """

        return (
            HtmlElements.a(
                HtmlElement("img").wrap(E, src=src, **imgAtts),
                href,
                title=title,
                **atts,
            )
            if href
            else HtmlElement("img").wrap(E, src=src, title=title, **imgAtts, **atts)
        )

    @staticmethod
    def input(material, **atts):
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
        material: string | iterable
            This goes into the `value` attribute of the element, after HTML escaping.

        Returns
        -------
        string(html)
        """

        content = asString(material)
        return HtmlElement("input").wrap(E, value=HtmlElements.he(content), **atts)

    @staticmethod
    def finput(
        fileName,
        accept,
        saveUrl,
        title="Click to upload a file",
        cls="",
        **atts,
    ):
        """INPUT type="file".

        The input element for uploading files.

        Parameters
        ----------
        fileName: string
            The name of the currently existing file. If there is not yet a file
            pass the empty string.
        accept: string
            MIME type of uploaded file
        saveUrl: string
            The url to which the resulting file should be posted.
        cls: string, optional ""
            CSS class for the button
        title: string, optional ""
            tooltip for the button

        Returns
        -------
        string(html)
        """

        return HtmlElement("input").wrap(
            fileName,
            tp="file",
            accept=accept,
            url=saveUrl,
            title=title,
            cls=f"fileupload {cls}",
            **atts,
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

    @staticmethod
    def table(headers, rows, **atts):
        """TABLE.

        The table element.

        Parameters
        ----------
        headers, rows: iterables of iterables
            An iterable of rows.
            Each row is a tuple: an iterable of cells, and a CSS class for the row.
            Each cell is a tuple: material for the cell, and a CSS class for the cell.

        !!! note
            Cells in normal rows are wrapped in `<td>`, cells in header rows go
            into `<th>`.

        Returns
        -------
        string(html)
        """

        th = HtmlElement("th").wrap
        td = HtmlElement("td").wrap
        headerMaterial = HtmlElements.wrapTable(headers, th)
        rowMaterial = HtmlElements.wrapTable(rows, td)
        material = HtmlElement("body").wrap(headerMaterial + rowMaterial)
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
            Rows and cells within them, both with CSS classes.
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


def asString(value, tight=False):
    """Join an iterable of strings or iterables into a string.

    And if the value is already a string, return it, and if it is `None`
    return the empty string.

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

    sep = E if tight else "\n"

    return (
        E
        if value is None
        else value
        if type(value) is str
        else sep.join(asString(val) for val in value)
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
