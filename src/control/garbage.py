"""Takes care of garbage collection.

This module takes care that mongodb records and file system directories
that are marked for deletion, are physically removed after 31 days.
"""

from apscheduler.schedulers.background import BackgroundScheduler

from .files import dirContents, fileExists, dirRemove
from .generic import lessAgo, mTime, isonow
from .mongo import MDELDT
from .files import FDEL
from .flask import runInfo

ON = True
DRY = True
DRYREP = "(dry)" if DRY else ""

SEC = 1 / 24 / 3600

if DRY:
    DELAY_UNDEL = 60 * SEC
    DELAY_DEL = 120 * SEC
    DELAY_TMP = 30 * SEC
    INTERVAL = dict(seconds=20)
else:
    DELAY_UNDEL = 30
    DELAY_DEL = 31
    DELAY_TMP = 1
    INTERVAL = dict(days=1)

START_LEE = 10 * SEC


class Garbage:
    def __init__(self, Settings, Messages, Mongo):
        self.Settings = Settings
        self.Mongo = Mongo
        self.Messages = Messages
        Messages.debugAdd(self)

        scheduler = BackgroundScheduler()
        self.scheduler = scheduler

    def mayStart(self):
        Mongo = self.Mongo
        Messages = self.Messages
        Settings = self.Settings
        debugMode = Settings.debugMode

        runMain = runInfo()
        doIt = debugMode and runMain or not debugMode

        if not doIt:
            Messages.info(logmsg=f"SWEEPER{DRYREP}: deferred to debug instance")
            return False

        siteCrit = Settings.siteCrit
        site = Mongo.getRecord("site", siteCrit)
        sstm = site.sweeperStartTm or None

        if sstm is None or not lessAgo(START_LEE, sstm):
            now = isonow()
            Mongo.updateRecord("site", siteCrit, dict(sweeperStartTm=now))
            Messages.info(logmsg=f"SWEEPER{DRYREP}: scheduled at {now}")
            return True

        Messages.info(logmsg=f"SWEEPER{DRYREP}: was already started at {sstm}")
        return False

    def start(self):
        if ON:
            if self.mayStart():
                scheduler = self.scheduler
                sweeper = self.clean()
                scheduler.add_job(sweeper, "interval", **INTERVAL)
                scheduler.start()

    def clean(self):
        Messages = self.Messages

        def sweeper():
            head = f"SWEEPER{DRYREP}: "
            Messages.info(logmsg=f"{head}STARTED")
            self.sweepMongo()
            self.sweepDirectories()
            self.sweepTemp()
            Messages.info(logmsg=f"{head}DONE")

        return sweeper

    def sweepMongo(self):
        Mongo = self.Mongo
        Messages = self.Messages

        tables = """
            edition
            editionUser
            keyword
            project
            projectUser
            site
            user
        """.strip().split()

        head = f"SWEEPER{DRYREP}-MONGO: "

        for table in tables:
            recordIds = [
                r._id
                for r in Mongo.getList(table, {}, deleted=True)
                if lessAgo(DELAY_DEL, r.get(MDELDT, None))
            ]

            n = len(recordIds)

            if n:
                Messages.info(
                    logmsg=f"{head}{n:>3} {table} records to be permanently deleted"
                )
                if DRY:
                    for recordId in recordIds:
                        Messages.info(logmsg=f"{head}delete {table} record {recordId}")
                else:
                    Mongo.hardDeleteRecords(table, dict(_id={"$in", recordIds}))

    def sweepDirectories(self):
        Messages = self.Messages
        Settings = self.Settings
        workingDir = Settings.workingDir
        projectsDir = f"{workingDir}/project"

        nP = 0
        nE = 0

        head = f"SWEEPER{DRYREP}-MONGO: "

        for project in dirContents(projectsDir)[1]:
            projectDir = f"{projectsDir}/{project}"
            editionsDir = f"{projectDir}/edition"

            for edition in dirContents(editionsDir)[1]:
                editionDir = f"{editionsDir}/{edition}"
                eDelFile = f"{editionDir}/{FDEL}"

                if fileExists(eDelFile) and not lessAgo(
                    DELAY_DEL, mTime(eDelFile), iso=False
                ):
                    nE += 1

                    if DRY:
                        Messages.info(logmsg=f"{head}edition {project}/{edition}")
                    else:
                        try:
                            dirRemove(editionDir)
                        except Exception as e:
                            Messages.error(
                                logmsg=f"{head}Failed to remove {project}/{edition} "
                                f"because of {e}"
                            )

            pDelFile = f"{projectDir}/{FDEL}"

            if fileExists(pDelFile) and not lessAgo(
                DELAY_DEL, mTime(pDelFile), iso=False
            ):
                if len(dirContents(editionsDir)[1]):
                    Messages.error(
                        logmsg=f"{head}Will not remove project {project} "
                        "because it is not empty"
                    )
                else:
                    nP += 1

                    if DRY:
                        Messages.info(logmsg=f"{head}project {project}")
                    else:
                        try:
                            dirRemove(projectDir)
                        except Exception as e:
                            Messages.error(
                                logmsg=f"{head}Failed to remove {project} "
                                f"because of {e}"
                            )

        Messages.info(logmsg=f"{head}deleted {nP:>3} projects")
        Messages.info(logmsg=f"{head}deleted {nE:>3} editions")

    def sweepTemp(self):
        Messages = self.Messages
        Settings = self.Settings
        tempDir = Settings.tempDir

        head = f"SWEEPER{DRYREP}-TMP: "

        nT = 0

        for tmp in dirContents(tempDir)[1]:
            tmpd = f"{tempDir}/{tmp}"

            if tmpd.startswith("tmp") and not lessAgo(
                DELAY_TMP, mTime(tmpd), iso=False
            ):
                nT += 1

                if DRY:
                    Messages.info(logmsg=f"{head}tempdir {tmp}")
                else:
                    try:
                        dirRemove(tmpd)
                    except Exception as e:
                        Messages.error(
                            logmsg=f"{head}Failed to remove {tmpd} " f"because of {e}"
                        )

        Messages.info(logmsg=f"{head}deleted {nT:>3} tempdirs")
