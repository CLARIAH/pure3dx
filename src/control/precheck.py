import re
import collections
from urllib.parse import unquote_plus as uq
from unicodedata import normalize as un

from control.files import dirContents, fileExists


class Precheck:
    def __init__(self, Settings, Messages):
        """All about checking the files of an edition prior to publishing."""
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)

    def checkEdition(self, project, edition, asPublished=False):
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
        Messages = self.Messages
        Settings = self.Settings
        H = Settings.H
        workingDir = Settings.workingDir
        pubModeDir = Settings.pubModeDir
        tocFile = Settings.tocFile
        unusedDir = Settings.unusedDir

        if asPublished:
            editionDir = f"{pubModeDir}/project/{project}/edition/{edition}"
        else:
            editionDir = f"{workingDir}/project/{project._id}/edition/{edition._id}"
            editionUrl = f"/data/project/{project._id}/edition/{edition._id}"

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
        references = []
        mediaFiles = []
        media = collections.defaultdict(list)

        targetA = {} if asPublished else dict(target="article")
        targetM = {} if asPublished else dict(target="media")
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

        def wrapMedia():
            items = []

            for i, (mediaFile, referents) in enumerate(
                sorted(media.items(), key=lambda x: (-len(x[1]), x[0].lower()))
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
                        H.a(mediaFile, f"{preUrl}{mediaFile}", **targetM),
                        H.ul(
                            H.a(
                                f"{refFile} : {refStr}", f"{preUrl}{refFile}", **targetA
                            )
                            for (refFile, refStr) in sorted(
                                refs.items(), key=lambda x: (x[0].lower(), x[1].lower())
                            )
                        ),
                        f"media-{i}",
                    )
                )
            return H.details(
                "Media files and the files that refer to them", items, "media"
            )

        def wrapReport():
            return (
                H.h(3, "Table of contents")
                + wrapToc(tocInfo, outer=True)
                + H.h(3, "Table of Media")
                + wrapMedia()
            )

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

            if nPath:
                for name in files:
                    if name.lower().endswith(".html"):
                        checkFile(path, name)
                        toc[name] = pathRep
                    elif name not in SKIP:
                        mediaFiles.append((path, name))

            for name in dirs:
                subToc = checkFiles(path + (name,))

                if len(subToc):
                    toc[name] = subToc

            return toc

        def checkLinks():
            unused = f"/{unusedDir}/"
            links = collections.defaultdict(
                lambda: collections.defaultdict(lambda: collections.defaultdict(list))
            )

            for path, name in mediaFiles:
                nPath = len(path)
                pathRep = "/".join(path)
                sep = "/" if nPath > 0 else ""
                media[un("NFC", f"{pathRep}{sep}{name}")] = []

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
                    if refPath not in media:
                        status = 4
                    else:
                        status = 0
                        media[refPath].append((filePath, ln))
                else:
                    status = 1

                links[status][url][filePath].append(ln)

            good = True

            stats = collections.Counter()

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
                    Messages.message(kind, f"-- {url}", None, stop=False)

                    for fp, lns in sorted(locData.items(), key=lambda x: x[0].lower()):
                        Messages.message(
                            kind,
                            f"in {fp} at line {', '.join(str(ln + 1) for ln in lns)}",
                            None,
                            stop=False,
                        )

            if not asPublished:
                unReferenced = sorted(
                    (f for (f, m) in media.items() if len(m) == 0 and unused not in f),
                    key=lambda x: x.lower(),
                )
                nUnReferenced = len(unReferenced)
                unUsed = sum(
                    1 for (f, m) in media.items() if len(m) == 0 and unused in f
                )
                onceReferenced = sum(1 for m in media.values() if len(m) == 1)
                multiReferenced = sum(1 for m in media.values() if len(m) > 1)

                Messages.info(msg=f"{len(media)} media files of which:")
                Messages.info(msg=f"{multiReferenced} referenced more than once")
                Messages.info(msg=f"{onceReferenced} referenced exactly once")
                Messages.message(
                    "warning" if unUsed > 0 else "info",
                    f"{unUsed} not referenced, but in an {unusedDir} directory",
                    None,
                )
                Messages.message(
                    "error" if nUnReferenced > 0 else "info",
                    f"{nUnReferenced} not referenced at all",
                    None,
                    stop=False,
                )

                if nUnReferenced > 0:
                    good = False
                    for f in unReferenced:
                        Messages.error(msg=f"-- {f}", stop=False)

            return good

        tocInfo = checkFiles(())

        good = checkLinks()

        toc = wrapReport()

        if asPublished:
            return toc

        with open(f"{editionDir}/{tocFile}", "w") as fh:
            fh.write(toc)

        if good:
            Messages.good(msg="All checks OK")
        else:
            Messages.error(msg="Some checks failed", stop=False)

        return good
