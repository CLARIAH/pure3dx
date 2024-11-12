import os

from .generic import utcnow
from .files import dirExists, dirCopy, dirRemove


class Backup:
    def __init__(self, Settings, Messages, Mongo):
        """User-triggered backup operations

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
        """
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)
        self.Mongo = Mongo

    def addAuth(self, Auth):
        """Give this object a handle to the Auth object.

        Because of cyclic dependencies some objects require to be given
        a handle to Auth after their initialization.
        """
        self.Auth = Auth

    def getBackups(self, project=None):
        """Produce a backup button and an overview of existing backups.

        Only if it is relevant to the current user in the current run mode.

        The existing backups will be presented as link: a click will trigger a restore
        from that backup. There will also be delete buttons for each backup.

        Parameters
        ----------
        project: AttrDict | ObjectId | string, optional None
            If None, we deal with site-wide backup.
            Otherwise we get the backups of this project.
        """
        Auth = self.Auth
        if not Auth.mayBackup(project=project):
            return ""

        Settings = self.Settings
        Mongo = self.Mongo
        H = Settings.H
        Messages = self.Messages

        dataDir = Settings.dataDir
        runMode = Settings.runMode
        backupBase = f"{dataDir}/backups/{runMode}"
        projectSlug = ""

        if project is not None:
            (projectId, project) = Mongo.get("project", project)
            if projectId is None:
                return ""
            projectSlug = f"/{projectId}"
            backupBase += f"/project{projectSlug}"

        backups = []

        if dirExists(backupBase):
            with os.scandir(backupBase) as dh:
                for entry in dh:
                    if entry.is_dir():
                        name = entry.name
                        if name != "project":
                            backups.append(name)
            backups = list(reversed(sorted(backups)))

        title = "restore this backup"
        msgs = Messages.client("info", "wait for restore to complete ...", replace=True)
        backups = (
            H.div(H.small(H.i("No backups")))
            if len(backups) == 0
            else H.div(
                [
                    [
                        H.a(
                            backup,
                            f"/restore/{backup}{projectSlug}",
                            title=title,
                            cls="button small",
                            **msgs,
                        ),
                        H.nbsp,
                        H.iconx(
                            "delete",
                            href=f"/delbackup/{backup}{projectSlug}",
                            cls="button small",
                        ),
                        H.br(),
                    ]
                    for backup in backups
                ]
            )
        )

        title = (
            "make a backup of "
            + ("all" if project is None else "this project")
            + "data as stored in files and the database"
        )
        return H.details(
            H.a(
                "Make backup",
                f"/backup{projectSlug}",
                title=title,
                cls="button small",
                **Messages.client(
                    "info", "wait for backup to complete ...", replace=True
                ),
            ),
            backups,
            "backups",
        )

    def mkBackup(self, project=None):
        """Makes a backup of data as found in files and db.

        We do site-wide backups and project-specific backups.

        Site-wide backups take the complete working directory on the file system,
        and the complete relevant database in MongoDb.

        Project-specific backups take only the project directory on the file system,
        and the relevant project record plus the relevant edition records in MongoDb.

        !!! caution "Site-wide backups affect user data"
            The set of users and their permissions may be different across backups.
            After restoring a snaphot, the user that restored it may no longer exist,
            or have different rights.

        !!! caution "Project backups do not affect user data"
            No user data nor any coupling between users and the project and its editions
            are modified.

            A consequence is that a backup may contain editions that do not
            exist anymore and to which no users are coupled.
            It may be needed to assign current users to editions after a restore.

        Backups are stored in the data directory of the server under `backups` and then
        the run mode (`pilot`, `test`, `prod`).
        The site-wide backups are stores under `site`, the project backups
        under `project/`*projectId*.

        The directory name of the backup is
        the current date-time up to the second in iso format, but with the `:`
        replaced by `-`.

        Below that we have directories:

        *   `files`: contains the complete contents of the working directory of
            the current run mode.
        *   `db`: a backup of the complete contents of the MongoDb database of the
            current run mode.
            In there again a subdivision:

            * [`bson`](https://www.mongodb.com/basics/bson)
            * `json`

            The name indicates the file format of the backup.
            In both cases, the data ends up in folders per table,
            and within those folders we have files per record.

        Parameters
        ----------
        project: string, optional None
            If given, only backs up the given project.
        """
        Messages = self.Messages
        Auth = self.Auth

        if not Auth.mayBackup(project=project):
            Messages.warning(
                msg="Making a backup is not allowed",
                logmsg=("Making a backup is not allowed"),
            )
            return False

        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo

        dataDir = Settings.dataDir
        workingDir = Settings.workingDir
        runMode = Settings.runMode
        activeDir = workingDir
        backupBase = f"{dataDir}/backups/{runMode}"

        now = utcnow().isoformat(timespec="seconds").replace(":", "-")

        if project is not None:
            (projectId, project) = Mongo.get("project", project)
            if projectId is None:
                return False
            activeDir = f"{workingDir}/project/{projectId}"
            backupBase += f"/project/{projectId}"

        backupDir = f"{backupBase}/{now}"
        backupFileDir = f"{backupDir}/files"
        backupDbDir = f"{backupDir}/db"

        label = "system wide" if project is None else "project"
        Messages.info(
            msg=f"Making backup {now}",
            logmsg=f"Making {label} backup to {backupDir}",
        )
        Messages.info(msg="backup of database ...")
        good = Mongo.mkBackup(backupDbDir, project=project, asJson=True)
        if not good:
            return False

        Messages.info(msg="backup of files ...")
        dirCopy(activeDir, backupFileDir)
        Messages.info(msg="backup completed.")
        return True

    def restoreBackup(self, backup, project=None):
        """Restores data to files and db, from a backup.

        See also `mkBackup()`.

        First a new backup of the current situation will be made.

        Parameters
        ----------
        backup: string
            Name of a backup. The backup must exist.
        project: string, optional None
            If given, only restores the given project.

        """
        Messages = self.Messages
        Auth = self.Auth

        if not Auth.mayBackup(project=project):
            Messages.warning(
                msg="Restoring from a backup is not allowed",
                logmsg=("Restoring from a backup is not allowed"),
            )
            return False

        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo

        dataDir = Settings.dataDir
        runMode = Settings.runMode
        workingDir = Settings.workingDir
        activeDir = workingDir
        backupBase = f"{dataDir}/backups/{runMode}"

        if project is not None:
            (projectId, project) = Mongo.get("project", project)
            if projectId is None:
                return False
            activeDir = f"{workingDir}/project/{projectId}"
            backupBase += f"/project/{projectId}"

        backupDir = f"{backupBase}/{backup}"
        backupFileDir = f"{backupDir}/files"
        backupDbDir = f"{backupDir}/db"

        good = True
        if not dirExists(backupDir):
            Messages.warning(
                msg="backup to restore from does not exist",
                logmsg=f"Backup to restore from ({backupDir}) does not exist",
            )
            good = False
        elif not dirExists(backupFileDir):
            Messages.warning(
                msg="backup to restore from does not have file data",
                logmsg=(
                    f"Backup to restore from ({backupDir}) " f"does not have file data"
                ),
            )
            good = False
        elif not dirExists(backupDbDir):
            Messages.warning(
                msg="backup to restore from does not have db data",
                logmsg=(
                    f"Backup to restore from ({backupDir}) " "does not have db data"
                ),
            )
            good = False
        if not good:
            return False

        good = self.mkBackup(project=project)
        if not good:
            return False

        label = "system wide" if project is None else "project"
        Messages.info(
            msg=f"Restoring backup {backup}",
            logmsg=f"Restoring {label} backup {backupDir}",
        )
        Messages.info(msg="restore database ...")
        good = Mongo.restoreBackup(backupDbDir, project=project, clean=True)
        if not good:
            return False

        Messages.info(msg="restore files ...")
        dirCopy(backupFileDir, activeDir)
        Messages.info(msg="backup completed.")
        return True

    def delBackup(self, backup, project=None):
        """Deletes a backup.

        See also `mkBackup()`.

        Parameters
        ----------
        backup: string
            Name of a backup. The backup must exist.
        project: string, optional None
            If given, only deletes the backup of this project.

        """
        Messages = self.Messages
        Auth = self.Auth

        if not Auth.mayBackup(project=project):
            Messages.warning(
                msg="Deleting a backup is not allowed",
                logmsg=("Deleting a backup is not allowed"),
            )
            return False

        Settings = self.Settings
        Messages = self.Messages
        Mongo = self.Mongo

        dataDir = Settings.dataDir
        runMode = Settings.runMode
        backupBase = f"{dataDir}/backups/{runMode}"

        if project is not None:
            (projectId, project) = Mongo.get("project", project)
            backupBase += f"/project/{projectId}"

        backupDir = f"{backupBase}/{backup}"

        if not dirExists(backupDir):
            Messages.warning(
                msg="backup to delete does not exist",
                logmsg=f"Backup to delete ({backupDir}) does not exist",
            )
            return False

        label = "system wide" if project is None else "project"
        Messages.info(
            msg=f"Deleting backup {backup}",
            logmsg=f"Deleting {label} backup {backupDir}",
        )
        dirRemove(backupDir)
        Messages.info(msg="backup completed.")
        return True
