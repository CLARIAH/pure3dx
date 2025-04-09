"""Periodically deletes stuff permanently that is marked as deleted.

This module takes care that mongodb records and file system folders
that are marked for deletion, are physically removed after 31 days.

It also visits the temp directory and removes all subdirectories starting
with `tmp` that are at least one one day old.

The sweeper is a function that is scheduled to run at a configured interval.
Each worker of the running website has the sweeper scheduled.

But before each sweeper job executes, it checks the time of last execution.
If that is less than a half interval ago, the sweeper job will return without
doing anything.

In this way there will be always sweeper jobs scheduled, and if there are multiple
workers, they will not do superfluous work.
Note that when workers are killed and started, it remains guaranteed that sweeping
will be done.

The timing of the sweeper is configured in the sweeper.yml file in the yaml
directory.

All values must be specified as an amount of seconds or days, e.g.

```
  delayUndel:
    amount: 30
    unit: d
```

(`d` is day, `s` is second).

There are separate settings for the development environment and production, so that
in development you can see the actions happen much more quickly and frequently.

Here are the timing keys:

*   `delayUndel`
    The grace period for restoring deleted items.

    Items that are marked as deleted less than this ago, can still be restored.

*   `delayDel`
    The grace period for permanently deleting deleted items.

    Items that are marked as deleted less than this ago, will be permanently deleted
    by the next sweeping action.

*   `delayTmp`
    The grace period for deleting temp directories.

    Sometimes temporary directories are not wiped properly after they have been used.
    Those directories will be wiped after this period.

*   `interval`
    The interval between invocations of the sweeper function.

    When workers schedule the sweeper job, they use this as the interval.
"""

import os
from apscheduler.schedulers.background import BackgroundScheduler

from .files import dirContents, fileExists, dirRemove
from .generic import lessAgo, mTime, isonow
from .mongo import MDELDT
from .files import FDEL
from .flask import runInfo

ON = True
"""Whether to invoke the sweeper or not.

Sometimes, for debugging or testing, it is handy to not start the sweeping process.
"""

DRY = False
"""Whether to perform the wipes on records and directories, or suppress the execution.

If True, all wipes will be announced, but not performed.
"""

DRYREP = "(dry)" if DRY else ""


class Sweeper:
    def __init__(self, Settings, Messages, Mongo):
        self.Settings = Settings
        self.Mongo = Mongo
        self.Messages = Messages
        Messages.debugAdd(self)

        scheduler = BackgroundScheduler()
        self.scheduler = scheduler

    def maySchedule(self):
        """Whether a process is allowed to schedule the sweeper.

        Scheduling is suppressed if `ON` is False.

        Also, when Flask runs in debug mode, there are two processes working.
        The second process is the one that gets restarted when errors occur or
        code is updated. It is this process that may schedule sweepers, not the
        first process.
        """
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

    def showConfig(self):
        Messages = self.Messages
        Settings = self.Settings
        sweeperCfg = Settings.sweeper

        head = f"SWEEPER{DRYREP} config: "
        day = 24 * 3600
        sec = 1 / day

        for k in ("interval", "lee", "delayDel", "delayTmp"):
            v = sweeperCfg[k]

            if v < 3600 * sec:
                v = int(round(v * day))
                v = f"{v:>4}   s"
            else:
                v = f"  {v:>5.2f}d"

            Messages.info(logmsg=f"{head}{k:<10} = {v}")

    def start(self):
        """Schedules the sweeper job.
        """
        if self.maySchedule():
            self.showConfig()
            Settings = self.Settings
            interval = Settings.sweeper.intervalDict
            scheduler = self.scheduler
            sweeper = self.clean()
            scheduler.add_job(sweeper, "interval", **interval)
            scheduler.start()

    def clean(self):
        """Provides the sweeper function.

        This method is not the sweeper function itself, but it *returns*
        the sweeper function, which has some variables from the rest of the
        program bound in.

        The sweeper function has three separate parts:

        *   *sweepMongo* (for the database records)
        *   *sweepDirectories* (for the project/edition directories)
        *   *sweepTemp* (for the temporary directories)
        """
        Messages = self.Messages
        Mongo = self.Mongo
        Messages = self.Messages
        Settings = self.Settings
        siteCrit = Settings.siteCrit
        lee = Settings.sweeper.lee

        def mayExecute():
            if not ON:
                return False

            site = Mongo.getRecord("site", siteCrit)
            sstm = site.sweeperStartTm or None
            head = f"SWEEPER{DRYREP} by worker {os.getpid()}: "

            now = isonow()

            if sstm is None or not lessAgo(lee, sstm, iso=True):
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
        """Permanently deletes records marked as deleted in all tables.
        """
        Settings = self.Settings
        delayDel = Settings.sweeper.delayDel

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
                if not lessAgo(delayDel, r.get(MDELDT, None))
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
        """Wipes all project/edition directories that are marked as deleted.

        Such directories are marked as deleted if they contain a file named
        `__deleted__.txt`.

        Note that it should not occur that projects are marked as deleted while
        they contain editions that are not deleted. But in case this should happen,
        the deletion of the project directory is prevented.
        """
        Settings = self.Settings
        delayDel = Settings.sweeper.delayDel

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
                    delayDel, mTime(eDelFile), iso=False
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
                delayDel, mTime(pDelFile), iso=False
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
        """Wipes all temporary directories of a certain age, typically 1 day.

        These directories all resides at the toplevel of the temp dir, and their
        names start with `tmp`.
        """
        Settings = self.Settings
        delayTmp = Settings.sweeper.delayTmp

        Messages = self.Messages
        Settings = self.Settings
        tempDir = Settings.tempDir

        head = f"SWEEPER{DRYREP}-TMP: "

        nT = 0

        tmpDirs = dirContents(tempDir)[1]
        Messages.info(logmsg=f"Found {len(tmpDirs)} temp dirs")

        for tmp in dirContents(tempDir)[1]:
            tmpd = f"{tempDir}/{tmp}"

            if tmp.startswith("tmp") and not lessAgo(delayTmp, mTime(tmpd), iso=False):
                nT += 1
                Messages.info(logmsg=f"About to remove {tmpd}")
                Messages.info(logmsg=f"{head}tempdir {tmp}")

                if not DRY:
                    try:
                        dirRemove(tmpd)
                    except Exception as e:
                        Messages.error(
                            logmsg=f"{head}Failed to remove {tmpd} " f"because of {e}"
                        )

        if nT > 0:
            plural = "" if nT == 1 else "s"
            Messages.info(logmsg=f"{head}deleted {nT:>3} tempdir{plural}")
