from traceback import format_exception
from .mongo import Mongo

from .files import (
    dirContents,
    dirMake,
    dirRemove,
    dirCopy,
    fileCopy,
    fileExists,
    fileRemove,
    writeJson,
)
from .generic import deepdict, isonow
from .precheck import Precheck as PrecheckCls
from .static import Static as StaticCls


class Publish:
    def __init__(
        self, Settings, Messages, Viewers, Mongo: Mongo, Content, Tailwind, Handlebars
    ):
        """Publishing content as static pages.

        It is instantiated by a singleton object.

        Parameters
        ----------
        Settings: AttrDict
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        Mongo: object
            Singleton instance of `control.mongo.Mongo`.
        Tailwind: object
            Singleton instance of `control.tailwind.Tailwind`.
        """
        self.Settings = Settings
        self.Messages = Messages
        self.Viewers = Viewers
        self.Mongo = Mongo
        self.Content = Content
        self.Tailwind = Tailwind
        self.Handlebars = Handlebars
        Messages.debugAdd(self)
        Content.addPublish(self)

        self.Precheck = (
            None
            if Content is None
            else PrecheckCls(Settings, Messages, Content, Viewers)
        )

    def getPubNums(self, project, edition):
        """Determine project and edition publication numbers.

        Those numbers are inside the project and edition records in the database
        if the project/edition has been published before;
        otherwise we pick an unused number for the project;
        and within the project an unused edition number.

        When we look for those numbers, we look in the database records,
        and we look on the filesystem, and we take the number one higher than
        the maximum number used in the database and on the file system.

        **N.B.:** This practice has the flaw that numbers used for publishing projects
        and editions may get reused when you unpublish and/or delete published editions.

        We store the used publishing numbers for projects and editions in the
        `site` record, as a dictionary named pubNums, keyed by project numbers, and
        valued by the maximum edition pubNum for that project.

        The `pubNums` dictionary will never lose keys, and its values will
        never be lowered when projects or editions are removed.

        So new projects and editions always get numbers that have never been used before
        for publishing.

        We also copy the `pubNum` field of a project or edition into the field
        `pubNumLast` when we unpublish such an item, thereby nulling the `pubNum` field.
        When we republish the item, its `pubNumLast` is restored to the `pubNum`
        field.
        """
        Mongo = self.Mongo
        Settings = self.Settings
        pubModeDir = Settings.pubModeDir
        projectDir = f"{pubModeDir}/project"

        pPubNumLast = project.pubNum
        ePubNumLast = edition.pubNum

        def getNum(kind, pubNumLast, condition, itemsDir):
            if pubNumLast is None:
                itemsDb = Mongo.getList(kind, stop=False, **condition)
                nDb = len(itemsDb)
                maxDb = 0 if nDb == 0 else max(r.pubNum or 0 for r in itemsDb)

                itemsFile = [int(n) for n in dirContents(itemsDir)[1] if n.isdecimal()]
                nFile = len(itemsFile)

                maxFile = 0 if nFile == 0 else max(itemsFile)
                pubNum = max((maxDb, maxFile)) + 1
            else:
                pubNum = pubNumLast

            return pubNum

        if pPubNumLast is None:
            # because there is only 1 site in the database,
            # we can retrieve it without paramaters
            site = Mongo.getRecord("site")

            if "publishedProjectCount" in site:
                pPubNum = site["publishedProjectCount"] + 1
            else:
                # Determine project publish number the old way,
                # to make sure no two project have the same pubNum
                pPubNum = getNum("project", pPubNumLast, {}, projectDir)

            Mongo.updateRecord("site", {"publishedProjectCount": pPubNum})

        else:
            pPubNum = pPubNumLast

        if ePubNumLast is None:
            if "publishedEditionCount" in project:
                ePubNum = project["publishedEditionCount"] + 1
            else:
                # use get num for existing projects
                kind = "edition"
                pubNumLast = ePubNumLast
                condition = dict(projectId=project._id)
                itemsDir = f"{projectDir}/{pPubNum}/edition"

                ePubNum = getNum(kind, pubNumLast, condition, itemsDir)

            Mongo.updateRecord(
                "project", {"publishedEditionCount": ePubNum}, _id=project._id
            )
        else:
            ePubNum = ePubNumLast

        return (pPubNum, ePubNum)

    def generatePages(self, pPubNum, ePubNum):
        Settings = self.Settings
        Messages = self.Messages
        Viewers = self.Viewers
        Content = self.Content
        Tailwind = self.Tailwind
        Handlebars = self.Handlebars

        site = Content.relevant()[-1]
        featured = Content.getValue("site", site, "featured", manner="logical")

        Static = StaticCls(Settings, Messages, Content, Viewers, Tailwind, Handlebars)

        try:
            good = Static.genPages(pPubNum, ePubNum, featured=featured)

        except Exception as e1:
            Messages.error(logmsg="".join(format_exception(e1)), stop=False)
            good = False

        return good

    def updateEdition(self, site, project, edition, action, force=False, again=False):
        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo
        Precheck = self.Precheck

        if action not in {"add", "remove"}:
            Messages.error(msg=f"unknown action {action}", stop=False)
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

        # put a flag in the database that the site is publishing
        # this will prevent other publishing actions while this action is running

        last = site.lastPublished
        now = isonow()

        Mongo.updateRecord(
            "site", dict(processing=True, lastPublished=now), _id=site._id
        )

        # make sure that if something fails, the publishing flag will be reset

        pubModeDir = Settings.pubModeDir
        projectDir = f"{pubModeDir}/project"

        def restore(table, record):
            key = "isVisible" if table == "project" else "isPublished"
            Mongo.updateRecord(
                table,
                {
                    "pubNum": record.pubNum,
                    key: record[key] or False,
                },
                _id=record._id,
            )

        # quit early, without doing anything, if the action is not applicable

        good = True

        if action == "add":
            thisGood = Precheck.checkEdition(project, edition._id, edition)

            if thisGood:
                Messages.info("Edition validation OK")
            else:
                Messages.info("Edition validation not OK")
                good = False

                if force:
                    Messages.info("Continuing nevertheless")
                    good = True

            (pPubNum, ePubNum) = self.getPubNums(project, edition)

            if pPubNum is None:
                Messages.error(
                    msg="Could not find a publication number for project",
                    logmsg=f"Could not find a pubnum for project {project._id}",
                    stop=False,
                )
                good = False

            if ePubNum is None:
                Messages.error(
                    msg="Could not find a publication number for edition",
                    logmsg=f"Could not find a pubnum for {project._id}/{edition._id}",
                    stop=False,
                )
                good = False

            # if all went well, pPubNum and ePubNum are defined

        elif action == "remove":
            pPubNum = project.pubNum
            ePubNum = edition.pubNum
            pPubNumNew = pPubNum
            ePubNumNew = ePubNum

            if pPubNum is None:
                Messages.warning(
                    msg="Project is not a published one and cannot be unpublished",
                    logmsg=f"Project {project._id} has no pubnum",
                )
                good = False

            if ePubNum is None:
                Messages.warning(
                    msg="Edition is not a published one and cannot be unpublished",
                    logmsg=f"Edition {project._id}/{edition._id} has no pubnum",
                )
                good = False

        if good:
            thisProjectDir = f"{projectDir}/{pPubNum}"
            logmsg = None

            if action == "add":
                againRep = "Re-" if again else ""
                try:
                    stage = f"set pubnum for project to {pPubNum}"
                    update = dict(pubNum=pPubNum, isVisible=True)
                    Mongo.updateRecord("project", update, _id=project._id)

                    stage = f"set pubnum for edition to {ePubNum}"
                    update = {
                        "pubNum": ePubNum,
                        "isPublished": True,
                        "dc.datePublished": now,
                        "dc.dateUnPublished": None,
                    }
                    Mongo.updateRecord("edition", update, _id=edition._id)

                    stage = "add site files"
                    self.addSiteFiles(site)

                    stage = f"add project files to {pPubNum}"
                    self.addProjectFiles(project, pPubNum)

                    stage = f"add edition files to {pPubNum}/{ePubNum}"
                    self.addEditionFiles(project, pPubNum, edition, ePubNum)

                    stage = f"generate static pages for {pPubNum}/{ePubNum}"

                    if self.generatePages(pPubNum, ePubNum):
                        Messages.info(
                            msg=f"{againRep}Published edition to {pPubNum}/{ePubNum}",
                            logmsg=(
                                f"{againRep}Published {project._id}/{edition._id} "
                                f"as {pPubNum}/{ePubNum}"
                            ),
                        )
                    else:
                        good = False

                except Exception as e:
                    good = False
                    logmsg = (
                        f"{againRep}Publishing {project._id}/{edition._id} "
                        f"as {pPubNum}/{ePubNum} failed with error {e}"
                        f"at stage '{stage}'"
                    )

                if not good:
                    Messages.error(
                        msg=f"{againRep}Publishing of edition failed",
                        logmsg=logmsg,
                        stop=False,
                    )
                    self.removeEditionFiles(pPubNum, ePubNum)
                    theseEditions = dirContents(f"{thisProjectDir}/edition")[1]

                    if len(theseEditions) == 0:
                        self.removeProjectFiles(pPubNum)

            elif action == "remove":
                try:
                    stage = f"unset pubnum for edition from {ePubNum} to None"
                    update = {
                        "isPublished": False,
                        "dc.dateUnPublished": now,
                    }
                    Mongo.updateRecord("edition", update, _id=edition._id)

                    stage = f"remove edition files {pPubNum}/{ePubNum}"
                    self.removeEditionFiles(pPubNum, ePubNum)
                    Messages.info(
                        msg=f"Unpublished edition {pPubNum}/{ePubNum}",
                        logmsg=(
                            f"Unpublished edition {pPubNum}/{ePubNum} = "
                            f"{project._id}/{edition._id}"
                        ),
                    )
                    ePubNumNew = None

                    # check whether there are other published editions in this project
                    # on the file system

                    stage = f"check remaining editions in project {pPubNum}"
                    theseEditions = dirContents(f"{thisProjectDir}/edition")[1]

                    if len(theseEditions) == 0:
                        stage = f"make project with {pPubNum} invisible"
                        update = dict(isVisible=False)
                        Mongo.updateRecord("project", update, _id=project._id)

                        stage = f"remove project files {pPubNum}"
                        self.removeProjectFiles(pPubNum)
                    else:
                        Messages.info(
                            msg=(
                                f"Project {pPubNum} still has {len(theseEditions)} "
                                "published editions"
                            ),
                        )

                    pNumRep = (
                        pPubNum if pPubNumNew == pPubNum else f"{pPubNum}=>{pPubNumNew}"
                    )
                    eNumRep = (
                        ePubNum if ePubNumNew == ePubNum else f"{ePubNum}=>{ePubNumNew}"
                    )

                    stage = f"regenerate static pages for {pNumRep}/{eNumRep}"

                    if self.generatePages(pPubNum, ePubNum):
                        Messages.info(
                            msg=f"Unpublished project {pPubNum}",
                            logmsg=(f"Unpublished project {pPubNum} = {project._id}"),
                        )
                    else:
                        good = False

                except Exception as e:
                    good = False
                    logmsg = (
                        f"Unpublishing edition {pPubNum}/{ePubNum} = "
                        f"{project._id}/{edition._id} failed with error {e}."
                        f"at stage '{stage}'"
                    )

                if not good:
                    Messages.error(
                        msg="Unpublishing of edition failed",
                        logmsg=logmsg,
                        stop=False,
                    )

        # finish off with unsetting the processing flag in the database

        if good:
            lastPublished = now
        else:
            restore("project", project)
            restore("edition", edition)
            lastPublished = last

        Mongo.updateRecord(
            "site", dict(processing=False, lastPublished=lastPublished), _id=site._id
        )

    def addSiteFiles(self, site):
        Settings = self.Settings
        workingDir = Settings.workingDir
        pubModeDir = Settings.pubModeDir
        dbFile = Settings.dbFile

        dirMake(pubModeDir)

        (files, dirs) = dirContents(workingDir)

        for x in files:
            fileCopy(f"{workingDir}/{x}", f"{pubModeDir}/{x}")

        for x in dirs:
            if x in {"project", "db"}:
                continue

            dirCopy(f"{workingDir}/{x}", f"{pubModeDir}/{x}")

        dirMake(f"{pubModeDir}/project")
        writeJson(deepdict(site), asFile=f"{pubModeDir}/{dbFile}")

    def addProjectFiles(self, project, pPubNum):
        Settings = self.Settings
        workingDir = Settings.workingDir
        pubModeDir = Settings.pubModeDir
        dbFile = Settings.dbFile

        inDir = f"{workingDir}/project/{project._id}"
        outDir = f"{pubModeDir}/project/{pPubNum}"
        dirMake(outDir)

        (files, dirs) = dirContents(inDir)

        for x in files:
            fileCopy(f"{inDir}/{x}", f"{outDir}/{x}")

        for x in dirs:
            if x in {"edition", "db"}:
                continue

            dirCopy(f"{inDir}/{x}", f"{outDir}/{x}")

        writeJson(deepdict(project), asFile=f"{outDir}/{dbFile}")

    def addEditionFiles(self, project, pPubNum, edition, ePubNum):
        Settings = self.Settings
        workingDir = Settings.workingDir
        pubModeDir = Settings.pubModeDir
        tocFile = Settings.tocFile
        dbFile = Settings.dbFile

        inDir = f"{workingDir}/project/{project._id}/edition/{edition._id}"
        outDir = f"{pubModeDir}/project/{pPubNum}/edition/{ePubNum}"
        dirMake(outDir)
        tocPath = f"{outDir}/{tocFile}"

        if fileExists(tocPath):
            fileRemove(tocPath)

        (files, dirs) = dirContents(inDir)

        for x in files:
            fileCopy(f"{inDir}/{x}", f"{outDir}/{x}")

        for x in dirs:
            if x in {"db"}:
                continue

            dirCopy(f"{inDir}/{x}", f"{outDir}/{x}")

        writeJson(deepdict(edition), asFile=f"{outDir}/{dbFile}")

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
