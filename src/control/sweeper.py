"""Takes care of permanently deleting items that are marked as deleted.

This module takes care that mongodb records and file system folders
that are marked for deletion, are physically removed after 31 days.
"""

import os
from apscheduler.schedulers.background import BackgroundScheduler

from .files import dirContents, fileExists, dirRemove
from .generic import lessAgo, mTime, isonow
from .mongo import MDELDT
from .files import FDEL
from .flask import runInfo

ON = True
DRY = False
DRYREP = "(dry)" if DRY else ""

SEC = 1 / 24 / 3600

if DRY:
    DELAY_UNDEL = 3600 * SEC
    DELAY_DEL = 55 * SEC
    DELAY_TMP = 35 * SEC
    INTERVAL = dict(seconds=10)
else:
    DELAY_UNDEL = 30
    DELAY_DEL = 31
    DELAY_TMP = 1
    INTERVAL = dict(days=1)

SWEEP_LEE = (
    0.4 * INTERVAL["days"]
    if "days" in INTERVAL
    else SEC * INTERVAL["seconds"] if "seconds" in INTERVAL else 0.5
)


class Sweeper:
    def __init__(self, Settings, Messages, Mongo):
        self.Settings = Settings
        self.Mongo = Mongo
        self.Messages = Messages
        Messages.debugAdd(self)

        scheduler = BackgroundScheduler()
        self.scheduler = scheduler

    def maySchedule(self):
        if not ON:
            return False

        Messages = self.Messages
        Settings = self.Settings
        debugMode = Settings.debugMode

        runMain = runInfo()
        startIt = debugMode and runMain or not debugMode
        head = f"SWEEPER{DRYREP} by worker {os.getpid()}: "

        if startIt:
            now = isonow()
            Messages.info(logmsg=f"{head}scheduled at {now}")
        else:
            Messages.info(logmsg=f"{head}deferred to debug instance")
        return startIt

    def start(self):
        if self.maySchedule():
            scheduler = self.scheduler
            sweeper = self.clean()
            scheduler.add_job(sweeper, "interval", **INTERVAL)
            scheduler.start()

    def clean(self):
        Messages = self.Messages
        Mongo = self.Mongo
        Messages = self.Messages
        Settings = self.Settings
        siteCrit = Settings.siteCrit

        def mayExecute():
            if not ON:
                return False

            site = Mongo.getRecord("site", siteCrit)
            sstm = site.sweeperStartTm or None
            head = f"SWEEPER{DRYREP} by worker {os.getpid()}: "

            now = isonow()

            if sstm is None or not lessAgo(SWEEP_LEE, sstm, iso=True):
                Mongo.updateRecord("site", siteCrit, dict(sweeperStartTm=now))
                result = True
            else:
                Messages.info(
                    logmsg=f"{head}skipped sweeping at {now} "
                    f"because too close to last sweep at {sstm}"
                )
                result = False

            return result

        def sweeper():
            if mayExecute():
                head = f"SWEEPER{DRYREP}: "
                self.sweepMongo()
                self.sweepDirectories()
                self.sweepTemp()
                now = isonow()
                Messages.info(logmsg=f"{head}sweep completed at {now}")

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
                if not lessAgo(DELAY_DEL, r.get(MDELDT, None))
            ]

            n = len(recordIds)

            if n:
                plural = "" if n == 1 else "s"
                Messages.info(logmsg=f"{head}{n:>3} {table} record{plural} to be wiped")

                if DRY:
                    for recordId in recordIds:
                        Messages.info(logmsg=f"{head}delete {table} record {recordId}")
                else:
                    Mongo.hardDeleteRecords(
                        table, dict(_id={"$in": recordIds}), "sweeper"
                    )

    def sweepDirectories(self):
        Messages = self.Messages
        Settings = self.Settings
        workingDir = Settings.workingDir
        projectsDir = f"{workingDir}/project"

        nP = 0
        nE = 0

        head = f"SWEEPER{DRYREP}-FOLDERS"

        for project in dirContents(projectsDir)[1]:
            headProj = f"{head} project/{project}"
            projectDir = f"{projectsDir}/{project}"
            editionsDir = f"{projectDir}/edition"

            for edition in dirContents(editionsDir)[1]:
                headEd = f"{headProj}/edition/{edition}"
                editionDir = f"{editionsDir}/{edition}"
                eDelFile = f"{editionDir}/{FDEL}"

                if fileExists(eDelFile) and not lessAgo(
                    DELAY_DEL, mTime(eDelFile), iso=False
                ):
                    nE += 1

                    if DRY:
                        Messages.info(logmsg=headEd)
                    else:
                        try:
                            dirRemove(editionDir)
                            Messages.info(logmsg=f"{headEd}: wiped")
                        except Exception as e:
                            Messages.error(
                                logmsg=f"{headEd}: failed to wipe because of {e}"
                            )

            pDelFile = f"{projectDir}/{FDEL}"

            if fileExists(pDelFile) and not lessAgo(
                DELAY_DEL, mTime(pDelFile), iso=False
            ):
                if len(dirContents(editionsDir)[1]):
                    Messages.error(
                        logmsg=f"{headProj}: will not wipe because it is not empty"
                    )
                else:
                    nP += 1

                    if DRY:
                        Messages.info(logmsg=headProj)
                    else:
                        try:
                            dirRemove(projectDir)
                            Messages.info(logmsg=f"{headProj}: wiped")
                        except Exception as e:
                            Messages.error(
                                logmsg=f"{headProj}: failed to wipe because of {e}"
                            )

        if nP > 0:
            plural = "" if nP == 1 else "s"
            Messages.info(logmsg=f"{head}: deleted {nP:>3} project{plural}")

        if nE > 0:
            plural = "" if nE == 1 else "s"
            Messages.info(logmsg=f"{head}: deleted {nE:>3} edition{plural}")

    def sweepTemp(self):
        Messages = self.Messages
        Settings = self.Settings
        tempDir = Settings.tempDir

        head = f"SWEEPER{DRYREP}-TMP: "

        nT = 0

        for tmp in dirContents(tempDir)[1]:
            tmpd = f"{tempDir}/{tmp}"

            if tmp.startswith("tmp") and not lessAgo(DELAY_TMP, mTime(tmpd), iso=False):
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

        if nT > 0:
            plural = "" if nT == 1 else "s"
            Messages.info(logmsg=f"{head}deleted {nT:>3} tempdir{plural}")
