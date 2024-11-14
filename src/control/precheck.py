import re
import collections
from urllib.parse import unquote_plus as uq
from unicodedata import normalize as un

from .files import (
    dirNm,
    dirContents,
    dirRemove,
    fileRemove,
    fileExists,
    readJson,
    writeYaml,
)
from .helpers import showDict, htmlUnEsc


ONLINE_RE = re.compile(r"""^https?://""", re.I)
MAILTO_RE = re.compile(r"""^mailto:""", re.I)

STATUS = dict(
    unconfined=("error", "link(s) to  a file outside the edition"),
    external=("good", "external link(s)"),
    resolved=("good", "resolved link(s)"),
    missing=("error", "link(s) with missing target"),
    unreferenced=("warning", "file(s) that are not referenced from anywhere"),
)

SKIP = set(
    """
 .DS_Store
""".strip().split()
)


class Precheck:
    def __init__(self, Settings, Messages, Content, Viewers):
        """All about checking the files of an edition prior to publishing."""
        self.Settings = Settings
        self.Messages = Messages
        self.Content = Content
        self.Viewers = Viewers
        Messages.debugAdd(self)

    def checkEdition(self, site, project, edition, eInfo, asPublished=False):
        """Checks the article and media files in an editon and produces a toc.

        Articles and media are files and directories that the user creates through
        the Voyager interface.

        Before publishing we want to make sure that these files pass some basic
        sanity checks:

        *   All links in the articles are either external links, or they point at an
            existing file within the edition.
        *   All non-html files are referred to by a link in an html file.
            Not meeting this requirement does not block publishing, but
            unreferenced files will not be published.

        We also create a table of contents of all html files in the edition, so they
        can be inspected outside the Voyager.

        To that, we add a table of the media files, together with the information
        which html files refer to them.

        The table of contents in the Pure3d author app is slightly different from
        that in the Pure3d pub app, because the internal links work differently.

        You can trigger the generation of a toc that works for the published edition
        as well.

        Parameters
        ----------
        site: AttrDict | void
            The site record. If `asPublished` is passed with True, this parameter
            is not used and can be passed as None
        project: string | ObjectId | AttrDict | int
            The id of the project in question.
        edition: string | ObjectId | AttrDict | int
            The id of the edition in question.
        asPublished: boolean, optional False
            If False, the project and edition refer to the project and edition in the
            Pure3D author app, and the toc file will be created there.

            If True, the project and edition are numbers that refer to the
            published edition;
            it is assumed that all checks pass and the only task is
            to create a toc that is valid in the published edition.

        Returns
        -------
        boolean | string
            If `asPublished` is True, it returns the toc as a string, otherwise
            it returns whether the edition passed all checks.
        """
        Viewers = self.Viewers
        Content = self.Content
        Messages = self.Messages
        Settings = self.Settings
        H = Settings.H
        workingDir = Settings.workingDir
        pubModeDir = Settings.pubModeDir
        tocFile = Settings.tocFile
        article = Settings.article
        media = Settings.media

        if asPublished:
            editionDir = f"{pubModeDir}/project/{project}/edition/{edition}"
        else:
            editionDir = f"{workingDir}/project/{project._id}/edition/{edition}"
            editionUrl = f"/data/project/{project._id}/edition/{edition}"

        sceneFile = Viewers.getViewInfo(eInfo)[1]
        scenePath = f"{editionDir}/{sceneFile}"

        REF_RE = re.compile(
            r"""
            \b(src|href)
            =
            ['"]
            ([^'"]*)
            ['"]
            """,
            re.X | re.I,
        )

        sceneInfo = []
        references = []

        filesFound = dict(media=[], articles=[], models=[])
        filesReferenced = collections.defaultdict(collections.Counter)
        filesIssues = dict(
            unconfined=collections.defaultdict(collections.Counter),
            missing=collections.defaultdict(collections.Counter),
        )
        statusIndex = dict(
            unconfined=0, external=0, resolved=0, missing=0, unreferenced=0
        )
        targetA = {} if asPublished else dict(target=article)
        targetM = {} if asPublished else dict(target=media)
        preUrl = "" if asPublished else f"{editionUrl}/"

        def getUris(data, underUri):
            td = type(data)

            if td is list:
                return set().union(*(getUris(item, underUri) for item in data))

            if td is dict:
                return set().union(
                    *(
                        getUris(item, underUri or k in {"uri", "uris", "url", "urls"})
                        for (k, item) in data.items()
                    )
                )

            if td is str and underUri:
                return {data}

            return set()

        def removeEmptyDirs(base):
            (files, dirs) = dirContents(base)

            for fl in files:
                if fl in SKIP:
                    fileRemove(f"{base}/{fl}")
            for dr in dirs:
                removeEmptyDirs(f"{base}/{dr}")

            (files, dirs) = dirContents(base)

            if len(files) == 0 and len(dirs) == 0:
                dirRemove(base)

        def checkScene():
            scene = readJson(asFile=scenePath, plain=True)
            sceneYaml = scenePath.removesuffix("json") + "yaml"
            writeYaml(scene, asFile=sceneYaml)

            for uri in sorted(getUris(scene, False)):
                references.append((sceneFile, "models", un("NFC", htmlUnEsc(uri))))

            return scene

        def checkFile(target):
            sep = "/" if editionDir else ""

            with open(f"{editionDir}{sep}{target}") as fh:
                for i, line in enumerate(fh):
                    for kind, url in REF_RE.findall(line):
                        references.append((target, kind, un("NFC", htmlUnEsc(url))))

        def checkFiles(path):
            nPath = len(path)
            pathRep = "/".join(path)
            sep = "/" if nPath > 0 and editionDir else ""
            (files, dirs) = dirContents(f"{editionDir}{sep}{pathRep}")

            for name in files:
                namel = name.lower()
                nPath = len(path)
                pathRep = "/".join(path)
                sep = "/" if nPath > 0 else ""
                target = un("NFC", f"{pathRep}{sep}{name}")

                if nPath > 0 and namel.endswith(".html"):
                    checkFile(target)
                    filesFound["articles"].append(target)
                elif nPath == 0 and (namel.endswith(".glb") or namel.endswith("gltf")):
                    filesFound["models"].append(target)
                elif nPath > 0 and name not in SKIP:
                    filesFound["media"].append(target)

            for name in dirs:
                checkFiles(path + (name,))

        def checkMeta():
            if asPublished:
                return True

            good = True

            for table, record in (
                ("site", site),
                ("project", project),
                ("edition", eInfo),
            ):
                for metaKey in Content.checkMetaFields(table):
                    value = Content.getValue(table, record, metaKey, manner="logical")

                    if value:
                        # Messages.good(f"{table}:{metaKey} is present")
                        pass
                    else:
                        if metaKey == "dateCreated":
                            Messages.error(
                                f"{table} has no date created. "
                                f"Just edit any {table} field to set it to today"
                            )

                        Messages.error(
                            f"This {table} has no metadata field {metaKey}", stop=False
                        )
                        good = False

            if good:
                Messages.good("All required metadata fields are present")

            return good

        def checkLinks():
            for kind, thisFileList in filesFound.items():
                for target in thisFileList:
                    filesReferenced[target] = collections.Counter()

            for source, kind, url in references:
                sourcePath = source
                sourceDir = dirNm(sourcePath)
                sep = "/" if sourceDir and url else ""
                targetPath = un("NFC", f"{sourceDir}{sep}{uq(url)}")
                sep1 = "/" if targetPath and editionDir else ""

                if url.startswith(".."):
                    status = "unconfined"
                    filesIssues[status][targetPath][sourcePath] += 1
                elif ONLINE_RE.match(url) or MAILTO_RE.match(url):
                    status = "external"
                elif fileExists(f"{editionDir}{sep1}{targetPath}"):
                    status = "resolved"
                    kind = (
                        "articles"
                        if targetPath.endswith(".html")
                        else (
                            "models"
                            if targetPath.endswith(".glb")
                            or targetPath.endswith("gltf")
                            else "media"
                        )
                    )
                    filesReferenced[targetPath][sourcePath] += 1
                else:
                    status = "missing"
                    filesIssues[status][targetPath][sourcePath] += 1

                statusIndex[status] += 1

            good = True

            if asPublished:
                nUnref = 0

                for target, sources in filesReferenced.items():
                    if len(sources) > 0:
                        continue

                    fPath = f"{editionDir}/{target}"
                    fileRemove(fPath)
                    nUnref += 1

                removeEmptyDirs(editionDir)

                if nUnref:
                    Messages.warning(
                        f"Edition {project}/{edition}: {nUnref} unreferenced files "
                        "skipped from being published"
                    )
            else:
                Messages.special(msg="Quality control report")

                for sources in filesReferenced.values():
                    if len(sources) == 0:
                        statusIndex["unreferenced"] += 1

                for kind, n in statusIndex.items():
                    (msgKind, kindRep) = STATUS[kind]
                    if msgKind in {"error", "warning"} and n == 0:
                        msgKind = "good"
                    Messages.message(msgKind, f"{n} {kindRep}", None, stop=False)

                    if msgKind == "error":
                        good = False

            return good

        def wrapScene(sceneInfo):
            issues = {}

            for status, theseFiles in filesIssues.items():
                for file in theseFiles:
                    issues[file] = STATUS[status][0]

            return showDict(sceneFile, sceneInfo, issues=issues)

        def wrapFiles(kind):
            items = []

            theseFiles = filesFound[kind]

            outerCls = ""

            for i, target in enumerate(sorted(theseFiles, key=lambda x: x.lower())):
                sources = filesReferenced[target]

                total = sum(sources.values())
                cls = "warning" if total == 0 else "" if total == 1 else "special"

                if (
                    cls == "warning"
                    and outerCls == ""
                    or cls == "error"
                    and outerCls != "error"
                ):
                    outerCls = cls

                entryHead = H.a(target, f"{preUrl}{target}", **targetM, cls=cls)
                sourceEntries = H.ul(
                    H.li(
                        [
                            H.a(s, f"{preUrl}{s}", **targetA),
                            H.span(f" - {n} x", cls="small mono"),
                        ],
                    )
                    for (s, n) in sorted(sources.items(), key=lambda x: x[0].lower())
                )
                items.append(
                    H.li(
                        H.div(entryHead)
                        if total == 0
                        else H.details(entryHead, sourceEntries, f"{kind}-{i}")
                    )
                )
            kindRep = kind[0].upper() + kind[1:]
            return H.details(
                H.b(f"Table of {kindRep}", cls=outerCls), H.ul(items), kind
            )

        def wrapIssues(status):
            items = []

            theseFiles = filesIssues[status]

            if len(theseFiles) == 0:
                return ""

            for i, target in enumerate(sorted(theseFiles, key=lambda x: x.lower())):
                sources = theseFiles[target]

                cls = "error"

                entryHead = H.a(target, f"{preUrl}{target}", **targetM, cls=cls)
                sourceEntries = H.ul(
                    H.li(
                        [
                            H.a(s, f"{preUrl}{s}", **targetA),
                            H.span(f" - {n} x", cls="small mono"),
                        ],
                    )
                    for (s, n) in sorted(sources.items(), key=lambda x: x[0].lower())
                )
                items.append(H.li(H.details(entryHead, sourceEntries, f"issues-{i}")))
            statusRep = STATUS[status][1]
            return H.details(H.b(f"Table of {statusRep}", cls=cls), H.ul(items), status)

        def wrapReport():
            return (
                H.h(3, "Scene information")
                + wrapScene(sceneInfo)
                + wrapFiles("models")
                + wrapFiles("articles")
                + wrapFiles("media")
                + wrapIssues("unconfined")
                + wrapIssues("missing")
            )

        sceneInfo = checkScene()
        checkFiles(())
        good = checkMeta() and checkLinks()
        allTocs = wrapReport()

        if asPublished:
            return allTocs

        with open(f"{editionDir}/{tocFile}", "w") as fh:
            fh.write(allTocs)

        Messages.special(msg="Outcome")

        if good:
            Messages.good(msg="All checks OK")
        else:
            Messages.error(msg="Some checks failed", stop=False)

        return good
