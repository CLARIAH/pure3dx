import sys
import re
from subprocess import run as run_cmd, CalledProcessError

from files import unexpanduser as ux


def lcFirst(x):
    if not x:
        return ""

    return x[0].upper() + x[1:]


def prettify(x):
    return " ".join(lcFirst(w) for w in x.split("_"))


VERSION_RE = re.compile(r"""^([0-9]*)(.*)""")


def versionRepl(part):
    match = VERSION_RE.match(part)
    return tuple(match.group(1, 2))


def dottedKey(version):
    return tuple(versionRepl(part) for part in version.split("."))


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
