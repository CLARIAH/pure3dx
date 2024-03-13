import re
import collections
from urllib.parse import unquote_plus as uq
from unicodedata import normalize as un

from control.files import (
    dirNm,
    dirContents,
    dirMake,
    dirRemove,
    fileNm,
    fileMove,
    fileRemove,
    fileExists,
    readJson,
    writeYaml,
)
from control.helpers import showDict


class Precheck:
    def __init__(self, Settings, Messages, Content):
        """All about checking the files of an edition prior to publishing."""
        self.Settings = Settings
        self.Messages = Messages
        self.Content = Content
        Messages.debugAdd(self)

    def checkEdition(self, project, edition, eInfo, asPublished=False):
        """Checks the article and media files in an editon and produces a toc.

        Articles and media are files and directories that the user creates through
        the Voyager interface.

        Before publishing we want to make sure that these files pass some basic
        sanity checks:

        *   All links in the articles are either external links, or they point at an
            existing file within the edition.
        *   All non-html files are referred to by a link in an html file. However,
            you may put unreferenced files in a directory called *unused* to
            ignore this requirement.

        We also create a table of contents of all html files in the edition, so they
        can be inspected outside the Voyager.

        To that, we add a table of the media files, together with the information
        which html files refer to them.

        The table of contents in the Pure3d edit app is slightly different from
        that in the Pure3d pub app, because the internal links work differently.

        You can trigger the generation of a toc that works for the published edition
        as well.

        Parameters
        ----------
        project: string | ObjectId | AttrDict | int
            The id of the project in question.
        edition: string | ObjectId | AttrDict | int
            The id of the edition in question.
        asPublished: boolean, optional False
            If False, the project and edition refer to the edition in the
            Pure3D edit app, and the toc file will be created there.

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
        Content = self.Content
        Messages = self.Messages
        Settings = self.Settings
        H = Settings.H
        workingDir = Settings.workingDir
        pubModeDir = Settings.pubModeDir
        tocFile = Settings.tocFile
        unusedDir = Settings.unusedDir
        article = Settings.article
        media = Settings.media

        if asPublished:
            editionDir = f"{pubModeDir}/project/{project}/edition/{edition}"
        else:
            editionDir = f"{workingDir}/project/{project._id}/edition/{edition}"
            editionUrl = f"/data/project/{project._id}/edition/{edition}"

        sceneFile = Content.getViewInfo(eInfo)[1]
        self.debug(f"{edition=} {eInfo=} {sceneFile=}")
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

        ONLINE_RE = re.compile(r"""^https?://""", re.I)
        MAILTO_RE = re.compile(r"""^mailto:""", re.I)

        STATUS = {
            0: ("good", "resolved"),
            1: ("error", "missing"),
            2: ("good", "outside Pure3d"),
            3: ("error", "outside the article files"),
            4: ("warning", "exists but non-exact reference"),
        }

        SKIP = set(
            """
         .DS_Store
        """.strip().split()
        )

        tocInfo = []
        sceneInfo = []
        references = []

        fileList = dict(
            media=[],
            article=[],
            model=[],
        )
        fileIndex = dict(
            media=collections.defaultdict(list),
            article=collections.defaultdict(list),
            model=collections.defaultdict(list),
        )

        targetA = {} if asPublished else dict(target=article)
        targetM = {} if asPublished else dict(target=media)
        preUrl = "" if asPublished else f"{editionUrl}/"

        def wrapToc(toc, outer=False):
            items = []

            for i, name in enumerate(sorted(toc, key=lambda f: f.lower())):
                subToc = toc[name]

                if type(subToc) is str:
                    sep = "" if subToc == "" else "/"
                    item = H.a(
                        name.removesuffix(".html"),
                        f"{preUrl}{subToc}{sep}{name}",
                        **targetA,
                    )
                else:
                    item = H.details(name, wrapToc(subToc), f"toc-{i}")

                items.append(item)

            return (H.content if outer else H.ul)(items)

        def wrapFiles(kind):
            items = []

            for i, (file, referents) in enumerate(
                sorted(
                    fileIndex[kind].items(), key=lambda x: (-len(x[1]), x[0].lower())
                )
            ):
                refsDict = collections.defaultdict(list)

                for refFile, ln in referents:
                    refsDict[refFile].append(ln)

                refs = {}

                for refFile, lns in refsDict.items():
                    n = len(lns)
                    cls = "error" if n == 0 else "info" if n == 1 else "special"
                    refStr = H.span(", ".join(str(ln) for ln in sorted(lns)), cls=cls)
                    refs[refFile] = refStr

                items.append(
                    H.details(
                        H.a(file, f"{preUrl}{file}", **targetM),
                        H.ul(
                            H.a(
                                f"{refFile} : {refStr}", f"{preUrl}{refFile}", **targetA
                            )
                            for (refFile, refStr) in sorted(
                                refs.items(), key=lambda x: (x[0].lower(), x[1].lower())
                            )
                        ),
                        f"{kind}-{i}",
                    )
                )
            return H.details(
                f"{kind} files and the files that refer to them", items, kind
            )

        def wrapScene(sceneInfo):
            return showDict(sceneFile, sceneInfo)

        def wrapReport():
            return (
                H.h(3, "Scene information")
                + wrapScene(sceneInfo)
                + H.h(3, "Table of Models")
                + wrapFiles("model")
                + H.h(3, "Table of contents")
                + wrapToc(tocInfo, outer=True)
                + H.h(3, "Table of Media")
                + wrapFiles("media")
            )

        def getUris(data, underUri):
            td = type(data)

            if td is list:
                return set().union(*(getUris(item, underUri) for item in data))

            if td is dict:
                return set().union(
                    *(
                        getUris(item, underUri or k == "uri" or k == "uris")
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
                self.debug(f"REMOVE {base}")
                dirRemove(base)

        def checkScene():
            scene = readJson(asFile=scenePath, plain=True)
            writeYaml(scene, asFile=scenePath.removesuffix("json") + "yaml")

            for uri in sorted(getUris(scene, False)):
                references.append(("", sceneFile, "uri", "model", uri))

            return scene

        def checkFile(path, name):
            nPath = len(path)
            pathRep = "/".join(path)
            sep1 = "/" if nPath > 0 and editionDir else ""
            sep2 = "/" if nPath > 0 or editionDir else ""

            with open(f"{editionDir}{sep1}{pathRep}{sep2}{name}") as fh:
                for i, line in enumerate(fh):
                    for kind, url in REF_RE.findall(line):
                        references.append((path, name, i, kind, url))

        def checkFiles(path):
            nPath = len(path)
            pathRep = "/".join(path)
            sep = "/" if nPath > 0 and editionDir else ""
            (files, dirs) = dirContents(f"{editionDir}{sep}{pathRep}")

            toc = {}

            for name in files:
                namel = name.lower()
                if nPath > 0 and namel.endswith(".html"):
                    checkFile(path, name)
                    toc[name] = pathRep
                    fileList["article"].append((path, name))
                elif (nPath == 0 or nPath == 1 and path[0] == unusedDir) and (
                    namel.endswith(".glb") or namel.endswith("gltf")
                ):
                    fileList["model"].append((path, name))
                elif nPath > 0 and name not in SKIP:
                    fileList["media"].append((path, name))

            for name in dirs:
                subToc = checkFiles(path + (name,))

                if len(subToc):
                    toc[name] = subToc

            return toc

        def checkLinks():
            unusedMiddle = f"/{unusedDir}/"
            unusedStart = f"{unusedDir}/"

            links = collections.defaultdict(
                lambda: collections.defaultdict(lambda: collections.defaultdict(list))
            )

            for kind, thisFileList in fileList.items():
                thisFileIndex = fileIndex[kind]

                for path, name in thisFileList:
                    nPath = len(path)
                    pathRep = "/".join(path)
                    sep = "/" if nPath > 0 else ""
                    thisFileIndex[un("NFC", f"{pathRep}{sep}{name}")] = []

            for path, name, ln, kind, url in references:
                nPath = len(path)
                pathRep = "/".join(path)
                sep = "" if nPath == 0 else "/"
                filePath = f"{pathRep}{sep}{name}"
                refPath = un("NFC", f"{pathRep}{sep}{uq(url)}")
                sep1 = "/" if refPath and editionDir else ""

                if url.startswith(".."):
                    status = 3
                elif ONLINE_RE.match(url) or MAILTO_RE.match(url):
                    status = 2
                elif fileExists(f"{editionDir}{sep1}{refPath}"):
                    if all(refPath not in fileIndex[kind] for kind in fileIndex):
                        status = 4
                    else:
                        status = 0
                        kind = (
                            "article"
                            if refPath.endswith(".html")
                            else "model"
                            if refPath.endswith(".glb") or refPath.endswith("gltf")
                            else "media"
                        )
                        fileIndex[kind][refPath].append((filePath, ln))
                else:
                    status = 1

                links[status][url][filePath].append(ln)

            good = True

            stats = collections.Counter()

            Messages.special(msg="Quality control report")

            for status, linkData in sorted(links.items()):
                (kind, statusRep) = STATUS[status]

                stats[kind] += 1

                if kind == "good":
                    continue
                elif kind == "error":
                    good = False

                msg = f"{statusRep} links:"
                Messages.message(kind, msg, None, stop=False)

                for url, locData in sorted(
                    linkData.items(), key=lambda x: x[0].lower()
                ):
                    Messages.plain(msg=f"* {url}")

                    for fp, lns in sorted(locData.items(), key=lambda x: x[0].lower()):
                        Messages.plain(
                            msg=f"in {fp} at "
                            + (
                                ", ".join(
                                    f"{ln + 1}" if type(ln) is int else ln for ln in lns
                                )
                            )
                        )

            if asPublished:
                nUnusedF = 0

                for kind, thisFileIndex in fileIndex.items():
                    for f, m in thisFileIndex.items():
                        if len(m) > 0:
                            continue
                        if not f.startswith(unusedStart) and unusedMiddle not in f:
                            continue

                        fPath = f"{editionDir}/{f}"
                        fileRemove(fPath)
                        nUnusedF += 1

                removeEmptyDirs(editionDir)

                if nUnusedF:
                    Messages.warning(
                        f"{nUnusedF} unreferenced files prevented from being published"
                    )

            else:
                for kind, thisFileIndex in fileIndex.items():
                    nMoved = 0
                    nUnused = 0

                    for f, m in thisFileIndex.items():
                        if len(m) > 0:
                            continue
                        if f.startswith(unusedStart) or unusedMiddle in f:
                            nUnused += 1
                            continue

                        fPath = f"{editionDir}/{f}"
                        parent = dirNm(fPath)
                        name = fileNm(fPath)
                        dirMake(f"{parent}/{unusedDir}")
                        fileMove(fPath, f"{parent}/{unusedDir}/{name}")
                        nMoved += 1

                    onceReferenced = sum(
                        1 for m in thisFileIndex.values() if len(m) == 1
                    )
                    multiReferenced = sum(
                        1 for m in thisFileIndex.values() if len(m) > 1
                    )

                    Messages.special(msg=f"{len(thisFileIndex)} {kind} files of which:")
                    Messages.good(msg=f"{multiReferenced} referenced more than once")
                    Messages.good(msg=f"{onceReferenced} referenced exactly once")
                    if nUnused == 0 and nMoved == 0:
                        Messages.good(msg="No unreferenced files")
                    else:
                        Messages.warning(
                            msg=f"{nUnused} not referenced, put in {unusedDir}",
                        )

            return good

        sceneInfo = checkScene()
        tocInfo = checkFiles(())

        good = checkLinks()

        toc = wrapReport()

        if asPublished:
            return toc

        with open(f"{editionDir}/{tocFile}", "w") as fh:
            fh.write(toc)

        Messages.special(msg="Outcome")

        if good:
            Messages.good(msg="All checks OK")
        else:
            Messages.error(msg="Some checks failed", stop=False)

        return good
