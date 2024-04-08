import sys
from subprocess import run as run_cmd, CalledProcessError

from control.files import unexpanduser as ux


def ucFirst(x):
    if not x:
        return ""

    return x[0].upper() + x[1:]


def prettify(x):
    return " ".join(ucFirst(w) for w in x.split("_"))


def genViewerSelector(
    allViewers,
    chosenViewer,
    chosenVersion,
    origViewer,
    origVersion,
    fileBase,
):
    html = []

    for viewer, vwDefault, versions in allViewers:
        viewerRep = f"<b>{viewer}</b>" if vwDefault else viewer
        viewerRep = f"<i>{viewerRep}</i>" if viewer == origViewer else viewerRep
        html.append(f"""<details><summary>{viewerRep}</summary>""")

        for version, vvDefault in versions:
            versionRep = f"<b>{version}</b>" if vwDefault and vvDefault else version
            versionRep = (
                f"<i>{versionRep}</i>"
                if viewer == origViewer and version == origVersion
                else versionRep
            )
            entry = (
                f"""<span>{versionRep}</span>"""
                if viewer == chosenViewer and version == chosenVersion
                else (
                    f"""<a href="/{fileBase}-{viewer}-{version}.html">"""
                    f"""{versionRep}</a>"""
                )
            )
            html.append(f"<div>{entry}</div>")

        html.append("</details>")

    return "\n".join(html)


def console(*msg, error=False, newline=True):
    msg = " ".join(m if type(m) is str else repr(m) for m in msg)
    msg = "" if not msg else ux(msg)
    msg = msg[1:] if msg.startswith("\n") else msg
    msg = msg[0:-1] if msg.endswith("\n") else msg
    target = sys.stderr if error else sys.stdout
    nl = "\n" if newline else ""
    target.write(f"{msg}{nl}")
    target.flush()


def run(cmdline, workDir=None):
    """Runs a shell command and returns all relevant info.

    The function runs a command-line in a shell, and returns
    whether the command was successful, and also what the output was, separately for
    standard error and standard output.

    Parameters
    ----------
    cmdline: string
        The command-line to execute.
    workDir: string, optional None
        The working directory where the command should be executed.
        If `None` the current directory is used.
    """
    try:
        result = run_cmd(
            cmdline,
            shell=True,
            cwd=workDir,
            check=True,
            capture_output=True,
        )
        stdOut = result.stdout.decode("utf8").strip()
        stdErr = result.stderr.decode("utf8").strip()
        good = True
    except CalledProcessError as e:
        stdOut = e.stdout.decode("utf8").strip()
        stdErr = e.stderr.decode("utf8").strip()
        good = False

    return (good, stdOut, stdErr)


def htmlEsc(val):
    """Escape certain HTML characters by HTML entities.

    To prevent them to be interpreted as HTML
    in cases where you need them literally.

    Parameters
    ----------
    val: string
        The input value
    """

    return (
        ""
        if val is None
        else str(val)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def htmlUnEsc(val):
    """Unescape certain HTML entities by their character values.

    Parameters
    ----------
    val: string
        The input value
    """

    return (
        ""
        if val is None
        else str(val)
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
        .replace("&amp;", "&")
    )


ISSUE_KEYS = {"url", "urls", "uri", "uris"}


def hEmpty(x):
    return (
        "<i>no value</i>"
        if x is None
        else """<code>0</code>"""
        if x == 0
        else """<code>''</code>"""
        if x == ""
        else f"""<code>{str(x)}</code>"""
    )


def hScalar(x, issues={}, isIssueKey=False):
    if type(x) is str:
        x = htmlEsc(x)
        if "\n" in x:
            x = x.replace("\n", "<br>")

    cls = issues[x] if isIssueKey and x in issues else ""
    xRep = f"""<code class="{cls}">{x}</code>"""
    return (len(x) < 60 if type(x) is str else True, xRep, cls)


def hScalar0(x, tight=True, issues={}, isIssueKey=False):
    tpv = type(x)

    if tpv is dict:
        (k, v) = list(x.items())[0]
        label = f"<b>{k}</b>"
        cls = ""
    else:
        v = list(x)[0]
        label = ""
        cls = issues[v] if isIssueKey and v in issues else ""

    (simple, vRep, clsDeep) = hData(v, issues=issues, isIssueKey=False)

    html = (
        (
            f"{{<b>{k}</b>: {vRep}}}"
            if tpv is dict
            else f"""[<span class="{cls}">{vRep}</span>]"""
            if tpv is list
            else f"""(<span class="{cls}">{vRep}</span>)"""
            if tpv is tuple
            else f"""{{<span class="{cls}">{vRep}</span>}}"""
        )
        if simple
        else (
            f"""<li><details open>
                <summary>{label}:</summary>
                <span class="{cls}">{vRep}</span>
                </details></li>"""
            if tight
            else f"""<li>{label}: {vRep}</li>"""
        )
    )
    return (simple, html, cls)


def hList(x, outer=False, tight=True, issues={}, isIssueKey=False):
    elem = f"{'o' if outer else 'u'}l"
    html = []
    html.append(f"<{elem}>")

    outerCls = ""

    for i, v in enumerate(x):
        (simple, vRep, cls) = hData(v, issues=issues, isIssueKey=isIssueKey)

        if (
            outerCls == ""
            and cls == "warning"
            or outerCls != "error"
            and cls == "error"
        ):
            outerCls = cls

        if simple:
            html.append(f"""<li>{vRep}</li>""")
        else:
            if type(v) is dict:
                idStr = f"""(#{v["id"]})""" if "id" in v else ""
                nameStr = f"""({v["name"]})""" if "name" in v else ""
                titleStr = ""

                if "titles" in v:
                    titles = v["titles"]

                    if type(titles) is dict:
                        titleStr = (
                            titles["EN"]
                            if "EN" in titles
                            else ""
                            if len(titles) == 0
                            else titles[sorted(titles.keys())[0]]
                        )
                        if titleStr == "":
                            titleStr = "??"

                head = " ".join(x for x in (idStr, nameStr, titleStr) if x != "")
            else:
                head = f"{i + 1}"

            html.append(
                (
                    f"""<li><details><summary class="{cls}">{head}:</summary>"""
                    f"""{vRep}</details></li>"""
                )
                if tight
                else f"""<li class="{cls}">{head}: {vRep}</li>"""
            )

    html.append(f"</{elem}>")

    return ("".join(html), outerCls)


def hDict(x, outer=False, tight=True, issues={}):
    html = []

    elem = f"{'o' if outer else 'u'}l"
    html.append(f"<{elem}>")

    outerCls = ""

    for k, v in sorted(x.items(), key=lambda y: str(y)):
        (simple, vRep, cls) = hData(
            v, tight=tight, issues=issues, isIssueKey=k in ISSUE_KEYS
        )
        if (
            outerCls == ""
            and cls == "warning"
            or outerCls != "error"
            and cls == "error"
        ):
            outerCls = cls

        if simple:
            html.append(f"""<li><b class="{cls}">{k}</b>: {vRep}</li>""")
        else:
            html.append(
                (
                    f"""<li><details><summary><b class="{cls}">{k}</b>:</summary>"""
                    f"""{vRep}</details></li>"""
                )
                if tight
                else f"""<li><b class="{cls}">{k}</b>: {vRep}</li>"""
            )

    html.append(f"</{elem}>")

    return ("".join(html), outerCls)


def hData(x, tight=True, issues={}, isIssueKey=False):
    if not x:
        return (True, hEmpty(x), "")

    tpv = type(x)

    if tpv is str or tpv is float or tpv is int or tpv is bool:
        return hScalar(x, issues=issues, isIssueKey=isIssueKey)

    if tpv is list or tpv is tuple or tpv is set or tpv is dict:
        return (
            (True, hEmpty(x), "")
            if len(x) == 0
            else hScalar0(x, tight=tight, issues=issues, isIssueKey=isIssueKey)
            if len(x) == 1 and tpv is not dict
            else (False, *hDict(x, tight=tight, issues=issues))
            if tpv is dict
            else (False, *hList(x, tight=tight, issues=issues, isIssueKey=isIssueKey))
        )
    return hScalar(x, issues=issues, isIssueKey=isIssueKey)


def showDict(title, data, *keys, tight=True, issues={}):
    """Shows selected keys of a dictionary in a pretty way.

    Parameters
    ----------
    keys: iterable of string
        For each key passed to this function, the information for that key
        will be displayed. If no keys are passed, all keys will be displayed.

    tight: boolean, optional True
        Whether to use the details element to compactify the representation.

    Returns
    -------
    displayed HTML
        An expandable list of the key-value pair for the requested keys.
    """

    keys = set(keys)

    (html, cls) = hDict(
        {k: v for (k, v) in data.items() if not keys or k in keys},
        outer=True,
        tight=tight,
        issues=issues,
    )
    openRep = "open" if keys else ""
    html = (
        (
            f"""<details {openRep}><summary class="{cls}">{title}</summary>"""
            f"""{html}</details>"""
        )
        if tight
        else f"""<div class="{cls}">{title}</div><div>{html}</div>"""
    )

    return html
