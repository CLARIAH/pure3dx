import re
from copy import deepcopy

from markdown import markdown

from control.files import (
    fileNm,
    dirNm,
    dirUpdate,
    dirAllFiles,
    dirContents,
    dirMake,
    stripExt,
    readJson,
    readYaml,
    writeJson,
)
from control.generic import AttrDict, deepAttrDict, deepdict
from control.helpers import prettify, genViewerSelector
from control.precheck import Precheck as PrecheckCls


COMMENT_RE = re.compile(r"""\{\{!--.*?--}}""", re.S)
CONFIG_FILE = "client.yml"


class Static:
    def __init__(self, Settings, Messages, Viewers, Tailwind, Handlebars):
        """All about generating static pages."""
        self.Settings = Settings
        self.Tailwind = Tailwind
        self.Handlebars = Handlebars
        self.Messages = Messages
        Messages.debugAdd(self)

        self.Precheck = PrecheckCls(Settings, Messages, Viewers)

        yamlDir = Settings.yamlDir
        yamlFile = f"{yamlDir}/{CONFIG_FILE}"
        cfg = readYaml(asFile=yamlFile)
        self.cfg = cfg
        self.markdownKeys = set(cfg.markdown.keys)
        self.listKeys = set(cfg.listKeys.keys)

        self.data = AttrDict()
        self.dbData = AttrDict()

    def sanitizeDC(self, table, dc):
        """Checks for missing (sub)-fields in the Dublin Core.

        Parameters
        ----------
        table: string
            The kind of info: site, project, or edition. This influences
            which fields should be present.
        dc: dict
            The Dublin Core info

        Returns
        -------
        void
            The dict is changed in place.
        """
        if table == "site":
            return
        if table == "project":
            return
        if table == "edition":
            k = "rights"

            if k not in dc:
                dc[k] = {}

            for k1, default in (
                ("license", "All rights reserved"),
                ("holder", "Unknown"),
            ):
                if k1 not in dc[k]:
                    dc[k][k1] = default

            return

    def htmlify(self, info):
        """Translate fields in a dict into html.

        Certain fields will trigger a markdown to html conversion.

        Certain fields will be normalized to lists:
        if the type of such a field is not list, it will be turned into a one-element
        list.

        There will also be generated a field whose name has the string `Comma` appended,
        it will be a comma-separated list of the items in that field.

        Parameters
        ----------
        info: dict
            The input data

        Returns
        -------
        AttrDict
            The resulting data. NB: it is brand-new data which does not share
            any data with the input data. Fields are either transformed from markdown
            to HTML, or copied.
        """
        listKeys = self.listKeys
        markdownKeys = self.markdownKeys

        r = AttrDict()

        for k, v in info.items():
            if k in listKeys:
                if type(v) is not list:
                    v = [v]

                r[f"{k}Comma"] = (
                    ""
                    if len(v) == 0
                    else str(v[0])
                    if len(v) == 1
                    else ", ".join(str(e) for e in v[0:-1]) + f" and {v[-1]}"
                )

            if k in markdownKeys:
                v = (
                    "<br>\n".join(markdown(e) for e in v)
                    if type(v) is list
                    else markdown(v)
                )

            r[k] = v

        return r

    def genPages(self, pPubNum, ePubNum, featured=[1, 2, 3]):
        """Generate html pages for a published edition.

        We assume the data of the projects and editions is already in place.
        As to the viewers: we compare the viewers and versions in the
        `data/viewers` directory with the viewers and versions in the
        `published/viewers` directory, and we copy viewer versions that are missing
        in the latter from the former.

        Exactly what will be generated depends on the parameters.

        There are the following things to generate:

        *   **S**: site wide files, outside projects
        *   **P**: project wide files, outside editions
        *   **E**: edition pages

        **S** will always be (re)generated.

        If a particular project is specified, the **P** for that project will
        also be (re)generated.

        If a particular edition is specified, the **E** for that edition will
        also be (re)generated.

        Parameters
        ----------
        pPubNUm, ePubNUm: integer or boolean or void
            Specifies which project and edition must be (re)generated, if they are
            integers.
            The integers is the numbers of the published project and edition.

            The following combinations are possible:

            *   `None`, `None`: only **S** is (re)generated;
            *   `p`, `None`: **S** and **P** for project with number `p` are
                (re)generated;
            *   `p`, `e`: **S** and **P** and **E** are (re)generated for project
                with number `p` and edition with number `e` within that project;
            *   `True`, `True`: everything will be regenerated.

        Returns
        -------
        boolean
            Whether the generation was successful.
        """
        Messages = self.Messages
        Settings = self.Settings
        Tailwind = self.Tailwind
        Handlebars = self.Handlebars
        viewerDir = Settings.viewerDir
        pubModeDir = Settings.pubModeDir
        dataOutDir = f"{pubModeDir}/json"

        templateDir = Settings.templateDir
        partialsIn = Settings.partialsIn
        jsDir = Settings.jsDir
        imageDir = Settings.imageDir

        partials = {}
        compiledTemplates = {}

        if type(featured) is list:
            msg = "skipping featured project '{}'"
            featuredParsed = set()

            for f in featured:
                if type(f) is int:
                    featuredParsed.add(f)
                elif type(f) is str:
                    if f.isdecimal():
                        featuredParsed.add(int(f))
                    else:
                        Messages.warning(msg=msg.format(f))
                else:
                    Messages.warning(msg=msg.format(f))

            featured = sorted(featuredParsed)

        else:
            Messages.warning(
                msg="The featured projects are not given as list, will be set to 1,2,3"
            )
            featured = [1, 2, 3]

        Messages.special(
            msg=f"Featured projects: {', '.join(str(f) for f in featured)}"
        )
        self.featured = featured

        def updateStatic(kind, srcDr):
            """Copy over static files.

            We are careful: instead of copying a folder, we merge, recursively,
            the source folder into the destination folder, and we do not delete
            anything from the destination.

            Hence the parameters `delete=False` and `level=-1` to
            `dirUpdate()`.

            We do this, because older parts of the site may depend on older
            static files.
            """
            dstDir = f"{pubModeDir}/{kind}"
            (good, c, d) = dirUpdate(srcDr, dstDir, level=-1, delete=False)
            report = f"{c:>3} copied, {d:>3} deleted"
            Messages.info(logmsg=f"{'updated':<10} {kind:<12} {report:<24} to {dstDir}")
            return good

        def updateViewers():
            """Copy over viewer versions.

            We are careful: instead of copying the folder with viewers from source to
            destination, we merge the source viewers with the destination viewers,
            without deleting destination viewers.
            And per viewer, instaead of copying the viewer folder from source
            to destination, we merge the source versions of that viewer with the
            destination versions of that viewer, without deleting destination versions.

            But per version we just copy, and stop the recursive merging, because each
            viewer version is an integral whole, and we do not support that the same
            version of the same viewer is different between source and destination.
            """
            srcDr = viewerDir
            dstDir = f"{pubModeDir}/viewers"
            (good, c, d) = dirUpdate(srcDr, dstDir, level=2, delete=False)
            report = f"{c:>3} copied, {d:>3} deleted"
            Messages.info(logmsg=f"{'updated':<10} {kind:<12} {report:<24} to {dstDir}")
            return good

        def registerPartials():
            good = True

            for partialFile in dirAllFiles(partialsIn):
                pDir = dirNm(partialFile).replace(partialsIn, "").strip("/")
                pFile = fileNm(partialFile)

                if pFile.startswith("."):
                    continue

                pName = stripExt(pFile)
                sep = "" if pDir == "" else "/"
                partial = f"{pDir}{sep}{pName}"

                with open(partialFile) as fh:
                    pContent = COMMENT_RE.sub("", fh.read())

                try:
                    partials[partial] = Handlebars.compile(pContent)
                except Exception as e:
                    Messages.error(
                        f"Error in register partial {partial} : {str(e)}", stop=False
                    )
                    good = False

            report = f"{len(partials):<3} pieces"
            Messages.info(
                logmsg=f"{'compiled':<10} {'partials':<12} {report:<24} to memory"
            )
            return good

        def genTarget(target, pNum, eNum):
            items = self.getData(target, pNum, eNum)

            success = 0
            failure = 0
            good = True

            for item in items:
                templateFile = f"{templateDir}/{item.template}"

                if templateFile in compiledTemplates:
                    template = compiledTemplates[templateFile]
                else:
                    with open(templateFile) as fh:
                        tContent = COMMENT_RE.sub("", fh.read())

                    try:
                        template = Handlebars.compile(tContent)
                    except Exception as e:
                        Messages.error(
                            logmsg=(
                                f"Error compiling template {templateFile} : {str(e)}"
                            ),
                            stop=False,
                        )
                        template = None

                    compiledTemplates[templateFile] = template

                if template is None:
                    failure += 1
                    good = False
                    continue

                try:
                    result = template(item, partials=partials)
                except Exception as e:
                    Messages.error(
                        logmsg=(f"Error filling template {item.template} : {str(e)}"),
                        stop=False,
                    )
                    failure += 1
                    good = False
                    continue

                for genDir, asData in ((pubModeDir, False), (dataOutDir, True)):
                    path = f"{genDir}/{item.fileName}"
                    if asData:
                        ext = ".json"
                        path = path.rsplit(".", 1)[0] + ext
                    dirPart = dirNm(path)
                    dirMake(dirPart)

                    if asData:
                        writeJson(deepdict(item), asFile=path)
                    else:
                        with open(path, "w") as fh:
                            fh.write(result)

                success += 1

            goodStr = f"{success:>3} ok"
            badStr = f"{failure:>3} XX" if failure else ""
            sep = ";" if failure else " "
            report = f"{goodStr}{sep} {badStr}"
            Messages.info(
                logmsg=f"{'generated':<10} {target:<12} {report:<24} to {pubModeDir}"
            )
            return good

        pType = type(pPubNum)
        eType = type(ePubNum)
        pIsInt = pType is int
        eIsInt = eType is int
        pNo = pPubNum is None
        eNo = ePubNum is None
        pAll = pPubNum is True
        eAll = ePubNum is True

        task = (
            ("site",)
            if pNo and eNo
            else ("project", pPubNum)
            if pIsInt and eNo
            else ("edition", pPubNum, ePubNum)
            if pIsInt and eIsInt
            else ("all",)
            if pAll and eAll
            else ("none",)
        )

        if task[0] == "none":
            Messages.error(
                msg="Page generation failed",
                logmsg=(
                    "Page generation failed because of illegal parameter combination: "
                    f"project {pPubNum}: {pType} and edition {ePubNum}: {eType}"
                ),
                stop=False,
            )
            return

        # site
        # project p
        # edition p e
        # all
        # none

        kind = task[0]

        targets = []

        targets.append(("site", None, None))
        targets.append(("textpages", None, None))
        targets.append(("projects", None, None))
        targets.append(("editions", None, None))

        if kind == "all":
            targets.append(("projectpages", None, None))
            targets.append(("editionpages", None, None))

        elif kind in {"project", "edition"}:
            targets.append(("projectpages", pPubNum, None))

            if kind == "edition":
                targets.append(("editionpages", pPubNum, ePubNum))

        good = True

        for kind, srcDir in (("js", jsDir), ("images", imageDir)):
            if not updateStatic(kind, srcDir):
                good = False

        if not updateViewers():
            good = False

        if not registerPartials():
            good = False

        if not Tailwind.generate():
            good = False

        self.getDbData()

        for target in targets:
            if not genTarget(*target):
                good = False

        if good:
            msg = "All tasks successful"
            Messages.info(logmsg=msg)
        else:
            msg = "Page generation failed"
            Messages.error(logmsg=msg, msg=msg, stop=False)
        return good

    def getData(self, kind, pNumGiven, eNumGiven):
        """Prepares page data of a certain kind.

        Pages are generated by filling in templates and partials on the basis of
        JSON data. Pages may require several kinds of data.
        For example, the index page needs data to fill in a list of projects
        and editions. Other pages may need the same kind of data.
        So we store the gathered data under the kinds they have been gathered.

        For some kinds we may restrict the data fetching to specified items:
        for `projectpages` and `editionpages`.

        When an edition has changed, we want to restrict the regeneration of
        pages to only those pages that need to change. And we also update things outside
        the projects and editions.

        Still, when an edition changes, the page with All editions also has to change.
        And if the edition was the first in a project to be published, a new project
        will be published as well, and hence the `All projects` page needs to change.

        If an edition is published next to other editions in a project, the project
        page needs to change, since it contains thumbnails of all its editions.

        So, the general rule is that we will always regenerate the thumbnails and the
        All-projects and All-edition pages, but not all of the project pages and edition
        pages.

        !!! note "Not all kinds will be restricted"
            The kinds `viewers`, `textpages`, `site` will never be restricted.

            The kinds `projects`, `editions` are needed for thumbnails, and are
            never restricted.

            The kinds `project`, `edition` are called by the collection of kinds
            `project` and `edition`, and are also not restricted.

            That leaves only the `projectpages` and `editionpages` needing to be
            restricted.

        Parameters
        ----------
        kind: string
            The kind of data we need to prepare.
        pNumGiven: integer or void
            Restricts the data fetching to projects with this publication number
        eNumGiven: integer or void
            Restricts the data fetching to editions with this publication number

        Returns
        -------
        dict or array
            The data itself.
            It is also stored in the member `data` of this object, under key
            `kind`. It will not be computed twice.
        """
        Settings = self.Settings
        Messages = self.Messages
        Precheck = self.Precheck
        textDir = Settings.textDir

        cfg = self.cfg
        generation1 = cfg.generation
        dbData = self.dbData
        data = self.data

        if kind in data:
            return data[kind]

        def get_viewers():
            defaultViewer = Settings.viewerDefault

            result = []

            for viewer, viewerConfig in Settings.viewers.items():
                versions = viewerConfig.versions
                element = viewerConfig.modes.read.element
                isDefault = viewer == defaultViewer

                result.append(
                    AttrDict(
                        name=viewer,
                        element=element,
                        isDefault=isDefault,
                        versions=[AttrDict(name=version) for version in versions],
                    )
                )
                result[-1].versions[0].isDefault = True

            return result

        def get_textpages():
            textFiles = dirContents(textDir)[0]

            def getLinks(textFile):
                return [
                    dict(text=prettify(t.removesuffix(".html")), link=t)
                    for t in textFiles
                    if t != textFile
                ]

            result = []

            for textFile in textFiles:
                r = AttrDict()
                r.template = "text.html"
                r.name = prettify(textFile.removesuffix(".html"))
                r["is" + r.name] = True
                r.fileName = textFile
                r.links = getLinks(textFile)

                with open(f"{textDir}/{textFile}") as fh:
                    r.content = fh.read()

                result.append(r)

            return result

        def get_site():
            featured = self.featured

            info = dbData[kind]
            dc = info.dc
            self.sanitizeDC("site", dc)
            dc = self.htmlify(dc)

            r = AttrDict()
            r.isHome = True
            r.template = "home.html"
            r.fileName = "index.html"
            r.name = dc.title
            r.contentdata = dc
            projects = self.getData("project", None, None)
            projectsIndex = {p.num: p for p in projects}
            projectsFeatured = []

            for p in featured:
                if p not in projectsIndex:
                    Messages.warning(f"WARNING: featured project {p} does not exist")
                    continue

                projectsFeatured.append(projectsIndex[p])

            r.projects = projectsFeatured

            return [r]

        def get_projects():
            r = AttrDict()
            r.isProject = True
            r.name = "All Projects"
            r.template = "projects.html"
            r.fileName = "projects.html"
            r.projects = self.getData("project", None, None)

            return [r]

        def get_editions():
            r = AttrDict()
            r.isEdition = True
            r.name = "All Editions"
            r.template = "editions.html"
            r.fileName = "editions.html"
            r.editions = self.getData("edition", None, None)

            return [r]

        def get_project():
            info = dbData[kind]

            result = []

            for num, item in info.items():
                dc = item.dc
                self.sanitizeDC("project", dc)
                dc = self.htmlify(dc)

                r = AttrDict()
                r.name = item.title
                r.num = num
                r.fileName = f"project/{num}/index.html"
                r.description = dc.description
                r.abstract = dc.abstract
                r.subjects = dc.subject
                r.visible = item.isVisible or False
                result.append(r)

            return result

        def get_edition():
            info = dbData[kind]

            result = []

            for pNum, eNums in info.items():
                for eNum, item in eNums.items():
                    dc = item.dc
                    self.sanitizeDC("edition", dc)
                    dc = self.htmlify(dc)

                    r = AttrDict()
                    r.projectNum = pNum
                    r.projectFileName = f"project/{pNum}.html"
                    r.name = item.title
                    r.num = eNum
                    r.fileName = f"project/{pNum}/edition/{eNum}/index.html"
                    r.abstract = dc.abstract
                    r.description = dc.description
                    r.subjects = dc.subject
                    r.published = item.isPublished or False
                    result.append(r)

            return result

        def get_projectpages():
            pInfo = dbData["project"]
            eInfo = dbData["edition"]

            result = []

            for pNo in sorted(pInfo):
                if pNumGiven is not None and pNo != pNumGiven:
                    continue

                pItem = pInfo[pNo]
                pdc = self.htmlify(pItem.dc)
                fileName = f"project/{pNo}/index.html"

                pr = AttrDict()
                pr.template = "project.html"
                pr.fileName = fileName
                pr.num = pNo
                pr.name = pItem.title
                pr.visible = pItem.isVisible or False
                pr.contentdata = pdc
                pr.editions = []

                thisEInfo = eInfo.get(pNo, {})

                for eNo in sorted(thisEInfo):
                    eItem = thisEInfo[eNo]
                    edc = self.htmlify(eItem.dc)

                    er = AttrDict()
                    er.projectNum = pNo
                    er.projectFileName = f"project/{pNo}/index.html"
                    er.fileName = f"project/{pNo}/edition/{eNo}/index.html"
                    er.num = eNo
                    er.name = eItem.title
                    er.contentdata = edc
                    er.published = eItem.isPublished or False

                    pr.editions.append(er)

                result.append(pr)

            return result

        def get_editionpages():
            viewers = self.getData("viewers", None, None)
            viewersLean = tuple(
                (
                    vw.name,
                    vw.isDefault,
                    tuple((vv.name, vv.isDefault) for vv in vw.versions),
                )
                for vw in viewers
            )

            pInfo = dbData["project"]
            eInfo = dbData["edition"]

            result = []

            for pNo in sorted(pInfo):
                if pNumGiven is not None and pNo != pNumGiven:
                    continue

                pItem = pInfo[pNo]
                projectFileName = f"project/{pNo}/index.html"
                projectName = pItem.get("title", pNo)

                thisEInfo = eInfo.get(pNo, {})

                for eNo in sorted(thisEInfo):
                    if eNumGiven is not None and eNo != eNumGiven:
                        continue

                    eItem = thisEInfo[eNo]
                    edc = self.htmlify(eItem.dc)

                    er = AttrDict()
                    er.template = "edition.html"
                    er.projectNum = pNo
                    er.projectName = projectName
                    er.projectFileName = projectFileName
                    fileBase = f"project/{pNo}/edition/{eNo}/index"
                    er.num = eNo
                    er.name = eItem.title
                    er.contentdata = edc
                    er.isPublished = eItem.ispublished or False
                    settings = eItem.settings
                    authorTool = settings.authorTool
                    origViewer = authorTool.name
                    origVersion = authorTool.name
                    er.sceneFile = authorTool.sceneFile
                    er.toc = Precheck.checkEdition(pNo, eNo, eItem, asPublished=True)

                    for viewerInfo in viewers:
                        viewer = viewerInfo.name
                        element = viewerInfo.element
                        versions = viewerInfo.versions
                        isDefaultViewer = viewerInfo.isDefault

                        for versionInfo in versions:
                            version = versionInfo.name
                            isDefault = versionInfo.isDefault
                            ver = deepAttrDict(deepcopy(deepdict(er)))
                            ver.viewer = viewer
                            ver.version = version
                            ver.element = element
                            ver.fileName = f"{fileBase}-{viewer}-{version}.html"
                            isDefault = isDefaultViewer and isDefault

                            viewerSelector = genViewerSelector(
                                viewersLean,
                                viewer,
                                version,
                                origViewer,
                                origVersion,
                                fileBase,
                            )

                            ver.viewerSelector = viewerSelector
                            result.append(ver)

                            if isDefault:
                                ver = deepAttrDict(deepcopy(deepdict(ver)))
                                ver.fileName = f"{fileBase}.html"
                                result.append(ver)

            return result

        getFunc = locals().get(f"get_{kind}", None)

        result = getFunc() if getFunc is not None else []

        data[kind] = result
        return result

    def getDbData(self):
        """Get the raw data contained in the json export from Mongo DB.

        This is the metadata of the site, the projects, and the editions.
        We store them as is in member `dbData`.

        Later we distil page data from this, i.e. the data that is ready to fill
        in the variables of the templates.

        We assume this data has been exported when projects and editions got published,
        into files named `db.json`.
        """
        Settings = self.Settings
        dbFile = Settings.dbFile

        dbData = self.dbData

        pubModeDir = Settings.pubModeDir
        projectDir = f"{pubModeDir}/project"

        dbData["site"] = readJson(asFile=f"{pubModeDir}/{dbFile}")

        rProjects = {}
        dbData["project"] = rProjects

        rEditions = {}
        dbData["edition"] = rEditions

        for p in dirContents(projectDir)[1]:
            if not p.isdecimal():
                continue

            p = int(p)
            pPath = f"{projectDir}/{p}"
            rProjects[p] = readJson(asFile=f"{pPath}/{dbFile}")

            for e in dirContents(f"{pPath}/edition")[1]:
                if not e.isdecimal():
                    continue

                e = int(e)
                ePath = f"{pPath}/edition/{e}"
                rEditions.setdefault(p, {})[e] = readJson(asFile=f"{ePath}/{dbFile}")
