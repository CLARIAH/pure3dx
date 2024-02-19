import re
from copy import deepcopy
from datetime import datetime as dt

from pybars import Compiler
from markdown import markdown

from files import (
    dirContents,
    dirUpdate,
    dirNm,
    dirMake,
    dirRemove,
    dirAllFiles,
    dirCopy,
    dirExists,
    fileCopy,
    baseNm,
    stripExt,
    writeYaml,
    readYaml,
    readJson,
    writeJson,
    expanduser as ex,
)
from generic import AttrDict, deepAttrDict, deepdict
from helpers import console, prettify, genViewerSelector
from tailwind import Tailwind


COMMENT_RE = re.compile(r"""\{\{!--.*?--}}""", re.S)

ROOT_DIR = "/app"
CONFIG_FILE = "client.yaml"
FEATURED_FILE = "featured.yaml"
TAILWIND_CFG = "tailwind.config.js"
DB_FILE = "db.json"


class Publish:
    def __init__(self, Settings, Viewers, Messages, Mongo):
        """Publishing content as static pages.

        It is instantiated by a singleton object.

        Parameters
        ----------
        Settings: AttrDict
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Viewers: object
            Singleton instance of `control.viewers.Viewers`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        Mongo: object
            Singleton instance of `control.mongo.Mongo`.
        """
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)
        self.Mongo = Mongo
        self.Viewers = Viewers

        repoDir = Settings.repoDir
        pubModeDir = Settings.pubModeDir
        clientDir = f"{repoDir}/src/client"

        yamlDir = Settings.yamlDir
        yamlFile = f"{yamlDir}/{CONFIG_FILE}"
        cfg = readYaml(asFile=yamlFile)
        self.cfg = cfg

        featuredFile = f"{yamlDir}/{FEATURED_FILE}"
        featured = readYaml(asFile=featuredFile)
        self.featured = featured

        locations = cfg.locations
        self.locations = locations

        self.markdownKeys = set(cfg.markdown.keys)
        self.listKeys = set(cfg.listKeys.keys)

        for k, v in locations.items():
            v = (
                v.replace("«root»", ROOT_DIR)
                .replace("«client»", clientDir)
                .replace("«pub»", pubModeDir)
            )
            locations[k] = ex(v)

        locations.clientDir = clientDir

        self.Handlebars = Compiler()

        T = Tailwind(locations, TAILWIND_CFG)
        T.install()
        self.T = T

        self.dbData = AttrDict()
        self.data = AttrDict()

    def setPubNums(self, project, edition):
        """Determine project and edition publication numbers.

        Those numbers are inside the project and edition records in the database
        if the project/edition has been published before;
        otherwise we pick an unused number for the project;
        and within the project an unused edition number.

        When we look for those numbers, we look in the database records,
        and we look on the filesystem, and we take the number one higher than
        the maximum number used in the database and on the file system.
        """
        Mongo = self.Mongo
        locations = self.locations
        projectDir = locations.projectDir

        pPubNumLast = project.pubNum
        ePubNumLast = edition.pubNum

        def getNum(kind, item, pubNumLast, condition, itemsDir, prop):
            if pubNumLast is None:
                itemsDb = Mongo.getList(kind, stop=False, **condition)
                nDb = len(itemsDb)
                maxDb = 0 if nDb == 0 else max(r.pubNum or 0 for r in itemsDb)

                itemsFile = [int(n) for n in dirContents(itemsDir)[1] if n.isdecimal()]
                nFile = len(itemsFile)

                maxFile = 0 if nFile == 0 else max(itemsFile)
                pubNum = max((maxDb, maxFile)) + 1
                update = dict(pubNum=pubNum, **{prop: True})
                Mongo.updateRecord(kind, update, _id=item._id)
            else:
                pubNum = pubNumLast

            return pubNum

        kind = "project"
        item = project
        pubNumLast = pPubNumLast
        condition = {}
        itemsDir = projectDir
        prop = "isVisible"

        pPubNum = getNum(kind, item, pubNumLast, condition, itemsDir, prop)

        kind = "edition"
        item = edition
        pubNumLast = ePubNumLast
        condition = dict(projectId=project._id)
        itemsDir = f"{projectDir}/{pPubNum}/edition"
        prop = "isPublished"

        ePubNum = getNum(kind, item, pubNumLast, condition, itemsDir, prop)

        return (pPubNum, ePubNum)

    def updateEdition(self, site, project, edition, action):
        Messages = self.Messages

        if action not in {"add", "remove"}:
            Messages.error(msg=f"unknown action {action}")
            return

        processing = site.processing

        # quit early if another processing action is taking place

        if processing:
            Messages.warning(
                msg="Site is being published. Try again a minute later",
                logmsg=(
                    f"Refusing to publish {project._id}/{edition._id} "
                    "while site is being republished"
                ),
            )
            return

        Mongo = self.Mongo
        locations = self.locations
        projectDir = locations.projectDir

        def restore(table, record):
            key = "isVisible" if table == "project" else "isPublished"
            Mongo.updateRecord(
                table,
                {
                    "pubNum": record.pubNum,
                    "lastPublished": record.lastPublished,
                    key: record[key],
                },
                _id=record._id,
            )

        # quit early, without doing anything, if the action is not applicable

        if action == "remove":
            pPubNum = project.pubNum
            ePubNum = edition.pubNum

            if pPubNum is None:
                Messages.warning(
                    msg="Project was not published",
                    logmsg=f"Projects {project._id} was not published",
                )
                return

            if ePubNum is None:
                Messages.warning(
                    msg="Edition was not published",
                    logmsg=f"Edition {project._id}/{edition._id} was not published",
                )
                return

        # put a flag in the database that the site is publishing
        # this will prevent other publishing actions while this action is running

        last = site.lastPublished
        now = dt.utcnow().isoformat(timespec="seconds").replace(":", "-")

        Mongo.updateRecord(
            "site", dict(processing=True, lastPublished=now), _id=site._id
        )

        # make sure that if something fails, the publishing flag will be reset

        if action == "add":
            try:
                (pPubNum, ePubNum) = self.setPubNums(project, edition)

                # add an edition:
                # first make its project visible and link it to a publication number

                update = dict(pubNum=pPubNum, lastPublished=now, isVisible=True)
                Mongo.updateRecord("project", update, _id=project._id)

                # then publish the edition in the database

                update = dict(pubNum=ePubNum, lastPublished=now, isPublished=True)
                Mongo.updateRecord("edition", update, _id=edition._id)

                # now add the files

                thisProjectDir = f"{projectDir}/{pPubNum}"

                # update the site files (but not the files in the projects)
                self.addSiteFiles(site)

                # update the project files (but not the files in the editions)

                self.addProjectFiles(project, pPubNum)

                # put the edition files in place

                self.addEditionFiles(project, pPubNum, edition, ePubNum)

                Messages.info(
                    msg=f"Published as {pPubNum}/{ePubNum}",
                    logmsg=(
                        f"Published {project._id}/{edition._id} as {pPubNum}/{ePubNum}",
                    ),
                )

            except Exception as e:
                Messages.error(
                    msg="Publishing failed",
                    logmsg=f"Publishing failed with error {e}",
                )
                restore("project", project)
                restore("edition", edition)
                Mongo.updateRecord(
                    "site", dict(processing=False, lastPublished=last), _id=site._id
                )
                return

            # if all went well, pPubNum and ePubNum are defined

        else:
            try:
                # remove an edition from the database

                pPubNum = project.pubNum
                ePubNum = edition.pubNum

                update = dict(pubNum=None, isPublished=False)
                Mongo.updateRecord("edition", update, _id=edition._id)

                # remove the files of the edition in question

                self.removeEditionFiles(pPubNum, ePubNum)
                Messages.info(
                    msg=f"Unpublished edition {pPubNum}/{ePubNum}",
                    logmsg=(
                        f"Unpublished edition {pPubNum}/{ePubNum} = "
                        f"{project._id}/{edition._id}"
                    ),
                )
                ePubNum = None

                # check whether there are other published editions in this project
                # on the file system

                thisProjectDir = f"{projectDir}/{pPubNum}"
                theseEditions = dirContents(f"{thisProjectDir}/edition")[1]

                if len(theseEditions) == 0:
                    update = dict(pubNum=None, isVisible=False)
                    Mongo.updateRecord("project", update, _id=project._id)

                    # remove the files of the project in question

                    self.removeProjectFiles(pPubNum)

                    pPubNum = None

                    Messages.info(
                        msg=f"Unpublished project {pPubNum}",
                        logmsg=(f"Unpublished project {pPubNum} = {project._id}"),
                    )
                else:
                    Messages.info(
                        msg=(
                            f"Project {pPubNum} still has {len(theseEditions)} "
                            "published editions"
                        ),
                    )
                    # update the project files (but not the files in the editions)

                    self.addProjectFiles(project, pPubNum)

                # update the site files (but not the files in the projects)
                self.addSiteFiles(site)

            except Exception as e:
                Messages.error(
                    msg="Publishing failed",
                    logmsg=f"Publishing failed with error {e}",
                )
                restore("project", project)
                restore("edition", edition)
                Mongo.updateRecord(
                    "site", dict(processing=False, lastPublished=last), _id=site._id
                )
                return

            # if all went well, pPubNum may or may not be None and ePubNum is None

        # generate the html files: those of the project and edition in question
        # and some files at the site level that need to be updated

        self.genPages(pPubNum, ePubNum)

        # finish off with unsetting the processing flag in the database

        Mongo.updateRecord(
            "site", dict(processing=False, lastPublished=now), _id=site._id
        )

    def addSiteFiles(self, site):
        Settings = self.Settings
        workingDir = Settings.workingDir
        pubModeDir = Settings.pubModeDir

        (files, dirs) = dirContents(workingDir)

        for x in files:
            fileCopy(f"{workingDir}/{x}", f"{pubModeDir}/{x}")

        for x in dirs:
            if x in {"project", "meta"}:
                continue

            dirCopy(f"{workingDir}/{x}", f"{pubModeDir}/{x}")

        dirMake(f"{pubModeDir}/project")
        writeJson(deepdict(site), asFile=f"{pubModeDir}/{DB_FILE}")

    def addProjectFiles(self, project, pPubNum):
        Settings = self.Settings
        workingDir = Settings.workingDir
        pubModeDir = Settings.pubModeDir

        inDir = f"{workingDir}/project/{project._id}"
        outDir = f"{pubModeDir}/project/{pPubNum}"
        dirMake(outDir)

        (files, dirs) = dirContents(inDir)

        for x in files:
            fileCopy(f"{inDir}/{x}", f"{outDir}/{x}")

        for x in dirs:
            if x in {"edition", "meta"}:
                continue

            dirCopy(f"{inDir}/{x}", f"{outDir}/{x}")

        dirMake(f"{outDir}/edition")
        writeJson(deepdict(project), asFile=f"{outDir}/{DB_FILE}")

    def addEditionFiles(self, project, pPubNum, edition, ePubNum):
        Settings = self.Settings
        workingDir = Settings.workingDir
        pubModeDir = Settings.pubModeDir

        inDir = f"{workingDir}/project/{project._id}/edition/{edition._id}"
        outDir = f"{pubModeDir}/project/{pPubNum}/edition/{ePubNum}"

        (files, dirs) = dirContents(inDir)

        for x in files:
            fileCopy(f"{inDir}/{x}", f"{outDir}/{x}")

        for x in dirs:
            if x in {"meta"}:
                continue

            dirCopy(f"{inDir}/{x}", f"{outDir}/{x}")

        writeJson(deepdict(project), asFile=f"{outDir}/{DB_FILE}")

    def removeProjectFiles(self, pPubNum):
        Settings = self.Settings
        pubModeDir = Settings.pubModeDir

        outDir = f"{pubModeDir}/project/{pPubNum}"
        dirRemove(outDir)

    def removeEditionFiles(self, pPubNum, ePubNum):
        Settings = self.Settings
        pubModeDir = Settings.pubModeDir

        outDir = f"{pubModeDir}/project/{pPubNum}/edition/{ePubNum}"
        dirRemove(outDir)

    def genPages(self, pPubNum, ePubNum):
        # generate the html pages
        # concerning specific project and edition pages: restrict to given
        # project edition
        Settings = self.Settings
        locations = self.locations
        pubModeDir = Settings.pubModeDir
        templateDir = locations.templates
        yamlOutDir = f"{pubModeDir}/yaml"
        Handlebars = self.Handlebars
        partialsIn = locations.partialsIn
        T = self.T

        partials = {}
        compiledTemplates = {}

        def copyStaticFolder(kind):
            srcDir = locations[kind]
            dstDir = f"{pubModeDir}/{kind}"
            (good, c, d) = dirUpdate(srcDir, dstDir)
            report = f"{c:>3} copied, {d:>3} deleted"
            console(f"{'updated':<10} {kind:<12} {report:<24} to {dstDir}")
            return good

        def copyViewers():
            srcDir = locations.viewers
            dstDir = f"{pubModeDir}/viewers"

            viewersIn = dirContents(srcDir)[1]

            for viewer in viewersIn:
                viewerSrcDir = f"{srcDir}/{viewer}"
                viewerDstDir = f"{dstDir}/{viewer}"

                if dirExists(viewerDstDir):
                    versionsIn = dirContents(viewerSrcDir)

                    for version in versionsIn:
                        versionSrcDir = f"{viewerSrcDir}/{version}"
                        versionDstDir = f"{viewerDstDir}/{version}"

                        if not dirExists(versionDstDir):
                            dirCopy(versionSrcDir, versionDstDir)
                else:
                    dirCopy(viewerSrcDir, viewerDstDir)

        def registerPartials():
            good = True

            for partialFile in dirAllFiles(partialsIn):
                pDir = dirNm(partialFile).replace(partialsIn, "").strip("/")
                pFile = baseNm(partialFile)

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
                    console(f"{partial} : {str(e)}")
                    good = False

            report = f"{len(partials):<3} pieces"
            console(f"{'compiled':<10} {'partials':<12} {report:<24} to memory")
            return good

        def genCss():
            """Generate the CSS by means of tailwind."""
            return T.generate()

        def genTarget(target):
            items = self.getData(target)

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
                        console(f"{templateFile} : {str(e)}", error=True)
                        template = None

                    compiledTemplates[templateFile] = template

                if template is None:
                    failure += 1
                    good = False
                    continue

                try:
                    result = template(item, partials=partials)
                except Exception as e:
                    console(f"Template = {item.template}")
                    console(f"Item = {item}")
                    console(str(e))
                    failure += 1
                    good = False
                    continue

                for genDir, asYaml in ((pubModeDir, False), (yamlOutDir, True)):
                    path = f"{genDir}/{item.fileName}"
                    if asYaml:
                        path = path.rsplit(".", 1)[0] + ".yaml"
                    dirPart = dirNm(path)
                    dirMake(dirPart)

                    if asYaml:
                        writeYaml(deepdict(item), asFile=path)
                    else:
                        with open(path, "w") as fh:
                            fh.write(result)

                success += 1

            goodStr = f"{success:>3} ok"
            badStr = f"{failure:>3} XX" if failure else ""
            sep = ";" if failure else " "
            report = f"{goodStr}{sep} {badStr}"
            console(f"{'generated':<10} {target:<12} {report:<24} to {pubModeDir}")
            return good

        good = True

        for kind in ("js", "images"):
            if not copyStaticFolder(kind):
                good = False

        if not copyViewers():
            good = False

        if not registerPartials():
            good = False

        if not genCss():
            good = False

        self.getDbData()

        for target in """
            site
            textpages
            projects
            editions
            projectpages
            editionpages
        """.strip().split():
            if not genTarget(target):
                good = False

        if good:
            console("All tasks successful")
        else:
            console("Some tasks failed", error=True)
        return good

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
        dbData = self.dbData

        locations = self.locations
        pubModeDir = Settings.pubModeDir
        projectDir = locations.projectDir

        dbData["site"] = readJson(asFile=f"{pubModeDir}/{DB_FILE}")

        rProjects = {}
        dbData["project"] = rProjects

        rEditions = {}
        dbData["edition"] = rEditions

        for p in dirContents(projectDir)[1]:
            if not p.isdecimal():
                continue

            p = int(p)
            pPath = f"{projectDir}/{p}"
            rProjects[p] = readJson(asFile=f"{pPath}/{DB_FILE}")

            for e in dirContents(f"{pPath}/edition")[1]:
                if not e.isdecimal():
                    continue

                e = int(e)
                ePath = f"{pPath}/edition/{e}"
                rEditions.setdefault(p, {})[e] = readJson(asFile=f"{ePath}/{DB_FILE}")

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

    def getData(self, kind):
        """Prepares page data of a certain kind.

        Pages are generated by filling in templates and partials on the basis of
        JSON data. Pages may require several kinds of data.
        For example, the index page needs data to fill in a list of projects
        and editions. Other pages may need the same kind of data.
        So we store the gathered data under the kinds they have been gathered.

        Parameters
        ----------
        kind: string
            The kind of data we need to prepare.

        Returns
        -------
        dict or array
            The data itself.
            It is also stored in the member `data` of this object, under key
            `kind`. It will not be computed twice.
        """
        Settings = self.Settings
        cfg = self.cfg
        generation = cfg.generation
        dbData = self.dbData
        data = self.data

        if kind in data:
            return data[kind]

        def get_viewers():
            defaultViewer = Settings.viewerDefault

            result = []

            for viewer, viewerConfig in Settings.viewers:
                versions = viewerConfig.versions
                element = viewerConfig.read.element
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
            textDir = cfg.locations.texts
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
            dc = self.htmlify(info.dc)

            r = AttrDict()
            r.isHome = True
            r.template = "home.html"
            r.fileName = "index.html"
            r.name = dc.title
            r.contentdata = dc
            projects = self.getData("project")
            projectsIndex = {str(p.num): p for p in projects}
            projectsFeatured = []

            for p in featured.projects:
                if p not in projectsIndex:
                    console(f"WARNING: featured project {p} does not exist")
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
            r.projects = self.getData("project")

            return [r]

        def get_editions():
            r = AttrDict()
            r.isEdition = True
            r.name = "All Editions"
            r.template = "editions.html"
            r.fileName = "editions.html"
            r.editions = self.getData("edition")

            return [r]

        def get_project():
            info = dbData[kind]

            result = []

            for num, item in info.items():
                dc = self.htmlify(item.dc)

                r = AttrDict()
                r.name = item.title
                r.num = num
                r.fileName = f"project/{num}/index.html"
                r.description = dc.description
                r.abstract = dc.abstract
                r.subjects = dc.subject
                r.visible = item.isVisible
                result.append(r)

            return result

        def get_edition():
            info = dbData[kind]

            result = []

            for pNum, eNums in info.items():
                for eNum, item in eNums.items():
                    dc = self.htmlify(item.dc)

                    r = AttrDict()
                    r.projectNum = pNum
                    r.projectFileName = f"project/{pNum}.html"
                    r.name = item.title
                    r.num = eNum
                    r.fileName = f"project/{pNum}/edition/{eNum}/index.html"
                    r.abstract = dc.abstract
                    r.description = dc.description
                    r.subjects = dc.subject
                    r.published = item.isPublished
                    result.append(r)

            return result

        def get_projectpages():
            pInfo = dbData["project"]
            eInfo = dbData["edition"]

            result = []

            for pNo in sorted(pInfo):
                pItem = pInfo[pNo]
                pdc = self.htmlify(pItem.dc)
                fileName = f"project/{pNo}/index.html"

                pr = AttrDict()
                pr.template = "project.html"
                pr.fileName = fileName
                pr.num = pNo
                pr.name = pItem.title
                pr.visible = pItem.isVisible
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
                    er.published = eItem.isPublished

                    pr.editions.append(er)

                result.append(pr)

            return result

        def get_editionpages():
            viewers = self.getData("viewers")
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
                pItem = pInfo[pNo]
                projectFileName = f"project/{pNo}/index.html"
                projectName = pItem.get("title", pNo)

                thisEInfo = eInfo.get(pNo, {})

                for eNo in sorted(thisEInfo):
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
                    er.isPublished = eItem.ispublished
                    settings = eItem.settings
                    authorTool = settings.authorTool
                    origViewer = authorTool.name
                    origVersion = authorTool.name
                    er.sceneFile = authorTool.sceneFile

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

    def generate(self):
        Settings = self.Settings
        locations = self.locations
        dataInDir = locations.dataIn
        pubModeDir = Settings.pubModeDir
        filesInDir = f"{dataInDir}/files"
        projectInDir = f"{filesInDir}/project"
        templateDir = locations.templates
        filesOutDir = f"{pubModeDir}"
        projectOutDir = f"{filesOutDir}/project"
        yamlOutDir = f"{pubModeDir}/yaml"
        Handlebars = self.Handlebars
        partialsIn = locations.partialsIn
        T = self.T

        partials = {}
        compiledTemplates = {}

        def copyFromExport():
            """Copies the export data files to the static file area.

            The copy is incremental at the levels of projects and editions.

            That means: projects and editions will not be removed from the static file
            area.

            So if your export contains a single or a few projects and editions,
            they will be used to update the static file area without affecting material
            of the static file area that is outside these projects and editions.
            """

            goodOuter, cOuter, dOuter = dirUpdate(
                filesInDir, filesOutDir, recursive=False
            )
            c = cOuter
            d = dOuter

            pMap = {}
            eMap = {}
            self.pMap = pMap
            self.eMap = eMap

            pCount = 0

            for pNum in dirContents(projectOutDir)[1]:
                pId = readJson(asFile=f"{projectOutDir}/{pNum}/id.json").id
                pMap[pId] = pNum

            for pId in dirContents(projectInDir)[1]:
                if pId in pMap:
                    pNum = pMap[pId]
                else:
                    pCount += 1
                    pNum = pCount
                    pMap[pId] = pNum

                pInDir = f"{projectInDir}/{pId}"
                pOutDir = f"{projectOutDir}/{pNum}"
                goodProject, cProject, dProject = dirUpdate(
                    pInDir, pOutDir, recursive=False
                )
                c += cProject
                d += dProject
                writeJson(dict(id=pId), asFile=f"{projectOutDir}/{pNum}/id.json")

                editionInDir = f"{pInDir}/edition"
                editionOutDir = f"{pOutDir}/edition"

                eCount = 0

                thisEMap = {}

                for eNum in dirContents(editionOutDir)[1]:
                    eId = readJson(asFile=f"{editionOutDir}/{eNum}/id.json").id
                    thisEMap[eId] = eNum

                for eId in dirContents(editionInDir)[1]:
                    if eId in thisEMap:
                        eNum = thisEMap[eId]
                    else:
                        eCount += 1
                        eNum = eCount
                        thisEMap[eId] = eNum

                    eInDir = f"{editionInDir}/{eId}"
                    eOutDir = f"{editionOutDir}/{eNum}"
                    goodEdition, cEdition, dEdition = dirUpdate(eInDir, eOutDir)
                    c += cEdition
                    d += dEdition
                    writeJson(dict(id=eId), asFile=f"{editionOutDir}/{eNum}/id.json")

                eMap[pId] = thisEMap

            report = f"{c:>3} copied, {d:>3} deleted"
            console(f"{'updated':<10} {'data':<12} {report:<24} to {filesOutDir}")
            return goodOuter and goodProject

        def copyStaticFolder(kind):
            srcDir = locations[kind]
            dstDir = f"{pubModeDir}/{kind}"
            (good, c, d) = dirUpdate(srcDir, dstDir)
            report = f"{c:>3} copied, {d:>3} deleted"
            console(f"{'updated':<10} {kind:<12} {report:<24} to {dstDir}")
            return good

        def registerPartials():
            good = True

            for partialFile in dirAllFiles(partialsIn):
                pDir = dirNm(partialFile).replace(partialsIn, "").strip("/")
                pFile = baseNm(partialFile)
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
                    console(f"{partial} : {str(e)}")
                    good = False

            report = f"{len(partials):<3} pieces"
            console(f"{'compiled':<10} {'partials':<12} {report:<24} to memory")
            return good

        def genCss():
            """Generate the CSS by means of tailwind."""
            return T.generate()

        def genTarget(target):
            items = self.getData(target)

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
                        console(f"{templateFile} : {str(e)}", error=True)
                        template = None

                    compiledTemplates[templateFile] = template

                if template is None:
                    failure += 1
                    good = False
                    continue

                try:
                    result = template(item, partials=partials)
                except Exception as e:
                    console(f"Template = {item.template}")
                    console(f"Item = {item}")
                    console(str(e))
                    failure += 1
                    good = False
                    continue

                for genDir, asYaml in ((pubModeDir, False), (yamlOutDir, True)):
                    path = f"{genDir}/{item.fileName}"
                    if asYaml:
                        path = path.rsplit(".", 1)[0] + ".yaml"
                    dirPart = dirNm(path)
                    dirMake(dirPart)

                    if asYaml:
                        writeYaml(deepdict(item), asFile=path)
                    else:
                        with open(path, "w") as fh:
                            fh.write(result)

                success += 1

            goodStr = f"{success:>3} ok"
            badStr = f"{failure:>3} XX" if failure else ""
            sep = ";" if failure else " "
            report = f"{goodStr}{sep} {badStr}"
            console(f"{'generated':<10} {target:<12} {report:<24} to {pubModeDir}")
            return good

        good = True

        if not copyFromExport():
            good = False

        for kind in ("js", "images", "viewers"):
            if not copyStaticFolder(kind):
                good = False

        if not registerPartials():
            good = False

        if not genCss():
            good = False

        self.getDbData()

        for target in """
            site
            textpages
            projects
            editions
            projectpages
            editionpages
        """.strip().split():
            if not genTarget(target):
                good = False

        if good:
            console("All tasks successful")
        else:
            console("Some tasks failed", error=True)
        return good

    def build(self):
        return self.generate()
