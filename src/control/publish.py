from datetime import datetime as dt
from traceback import format_exception

from control.files import (
    dirContents,
    dirMake,
    dirRemove,
    dirCopy,
    fileCopy,
    fileExists,
    fileRemove,
    readYaml,
    writeJson,
)
from control.generic import deepdict
from control.precheck import Precheck
from control.generate import Generate


CONFIG_FILE = "client.yml"


class Publish(Precheck, Generate):
    def __init__(self, Settings, Messages, Mongo, Tailwind):
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
        Messages.debugAdd(self)
        Messages.debugAdd(self)
        self.Mongo = Mongo

        Precheck.__init__(self)
        Generate.__init__(self, Tailwind)

        yamlDir = Settings.yamlDir
        yamlFile = f"{yamlDir}/{CONFIG_FILE}"
        cfg = readYaml(asFile=yamlFile)
        self.cfg = cfg

        self.markdownKeys = set(cfg.markdown.keys)
        self.listKeys = set(cfg.listKeys.keys)

    def getPubNums(self, project, edition):
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
        Settings = self.Settings
        pubModeDir = Settings.pubModeDir
        projectDir = f"{pubModeDir}/project"

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

    def updateEdition(self, site, project, edition, action, again=False):
        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo

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
        now = dt.utcnow().isoformat(timespec="seconds").replace(":", "-")

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
                    "lastPublished": record.lastPublished,
                    key: record[key] or False,
                },
                _id=record._id,
            )

        # quit early, without doing anything, if the action is not applicable

        good = True

        if action == "add":
            thisGood = self.checkEdition(project, edition)

            if thisGood:
                Messages.info("Article validation OK")
            else:
                Messages.info("Article validation not OK")
                good = False

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

            if action == "add":
                try:
                    stage = f"set pubnum for project to {pPubNum}"
                    update = dict(pubNum=pPubNum, lastPublished=now, isVisible=True)
                    Mongo.updateRecord("project", update, _id=project._id)

                    stage = f"set pubnum for edition to {ePubNum}"
                    update = dict(pubNum=ePubNum, lastPublished=now, isPublished=True)
                    Mongo.updateRecord("edition", update, _id=edition._id)

                    stage = "add site files"
                    self.addSiteFiles(site)

                    stage = f"add project files to {pPubNum}"
                    self.addProjectFiles(project, pPubNum)

                    stage = f"add edition files to {pPubNum}/{ePubNum}"
                    self.addEditionFiles(project, pPubNum, edition, ePubNum)

                    stage = f"generate static pages for {pPubNum}/{ePubNum}"

                    try:
                        thisGood = self.genPages(pPubNum, ePubNum)

                        if thisGood:
                            Messages.info(
                                msg=f"Published edition to {pPubNum}/{ePubNum}",
                                logmsg=(
                                    f"Published {project._id}/{edition._id} "
                                    f"as {pPubNum}/{ePubNum}"
                                ),
                            )
                        else:
                            good = False

                    except Exception as e1:
                        Messages.error(logmsg="".join(format_exception(e1)), stop=False)
                        good = False

                except Exception as e:
                    Messages.error(
                        msg="Publishing of edition failed",
                        logmsg=(
                            f"Publishing {project._id}/{edition._id} "
                            f"as {pPubNum}/{ePubNum} failed with error {e}",
                            f"at stage '{stage}'",
                        ),
                        stop=False,
                    )
                    good = False

                if not good and not again:
                    self.removeEditionFiles(pPubNum, ePubNum)
                    theseEditions = dirContents(f"{thisProjectDir}/edition")[1]

                    if len(theseEditions) == 0:
                        self.removeProjectFiles(pPubNum)

            elif action == "remove":
                try:
                    stage = f"unset pubnum for edition from {ePubNum} to None"
                    update = dict(pubNum=None, isPublished=False)
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
                        stage = f"unset pubnum for project from {pPubNum} to None"
                        update = dict(pubNum=None, isVisible=False)
                        Mongo.updateRecord("project", update, _id=project._id)

                        stage = f"remove project files {pPubNum}"
                        self.removeProjectFiles(pPubNum)

                        pPubNumNew = None

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

                    try:
                        thisGood = self.genPages(pPubNumNew, ePubNumNew)

                        if thisGood:
                            Messages.info(
                                msg=f"Unpublished project {pPubNum}",
                                logmsg=(
                                    f"Unpublished project {pPubNum} = {project._id}"
                                ),
                            )
                        else:
                            good = False

                    except Exception as e1:
                        Messages.error(logmsg="".join(format_exception(e1)), stop=False)
                        good = False
                        raise e1

                except Exception as e:
                    Messages.error(
                        msg="Unpublishing of edition failed",
                        logmsg=(
                            f"Unpublishing edition {pPubNum}/{ePubNum} = "
                            f"{project._id}/{edition._id} failed with error {e}."
                            f"at stage '{stage}'",
                        ),
                        stop=False,
                    )
                    good = False

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
            if x in {"project", "meta"}:
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
            if x in {"edition", "meta"}:
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
            if x in {"meta"}:
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
