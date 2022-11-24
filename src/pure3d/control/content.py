from control.generic import AttrDict
from control.files import fileExists

from control.datamodel import Datamodel


class Content(Datamodel):
    def __init__(self, Settings, Viewers, Messages, Mongo):
        """Retrieving content from database and file system.

        This class has methods to retrieve various pieces of content
        from the data sources, and hand it over to the `control.pages.Pages`
        class that will compose a response out of it.

        It is instantiated by a singleton object.

        Parameters
        ----------
        Settings: `control.helpers.generic.AttrDict`
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Viewers: object
            Singleton instance of `control.viewers.Viewers`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        Mongo: object
            Singleton instance of `control.mongo.Mongo`.
        """
        super().__init__(Settings, Messages, Mongo)
        self.Viewers = Viewers

    def addAuth(self, Auth):
        """Give this object a handle to the Auth object.

        Because of cyclic dependencies some objects require to be given
        a handle to Auth after their initialization.
        """
        self.Auth = Auth

    def addFieldHandler(self, key):
        pass

    def getValue(self, key, projectId=None, editionId=None, level=None):
        """Retrieve a metadata value.

        Metadata sits in a big, potentially deeply nested dictionary of keys
        and values.
        These locations are known to the system (based on `fields.yml`).
        This function retrieves the information from those known locations.

        Parameters
        ----------
        key: an identifier for the meta data field.
        projectId: ObjectId, optional None
            The project whose metadata we need. If it is None, we need metadata
            outside all of the projects.
        editionId: ObjectId, optional None
            The edition whose metadata we need. If it is None, we need metadata of
            a project or outer metadata.

        Returns
        -------
        string
            It is assumed that the metadata value that is addressed exists
            and is a string. If not, we return the empty string.
        """
        Mongo = self.Mongo
        Auth = self.Auth

        if editionId is not None:
            table = "editions"
            crit = dict(_id=editionId)
        elif projectId is not None:
            table = "projects"
            crit = dict(_id=projectId)
        else:
            table = "meta"
            crit = dict(name="site")

        record = Mongo.getRecord(table, **crit) or AttrDict()
        recordId = record._id
        meta = record.meta

        permissions = Auth.authorise(table, recordId=recordId, projectId=projectId)

        if "view" not in permissions:
            return None

        button = self.actionButton(
            "edit",
            table,
            recordId=recordId,
            key=key,
            projectId=projectId,
            editionId=editionId,
        )

        F = self.makeField(key)

        return F.formatted(meta, level=level, button=button)

    def getSurprise(self):
        """Get the data that belongs to the surprise-me functionality."""
        return "<h2>You will be surprised!</h2>"

    def getProjects(self):
        """Get the list of all projects.

        Well, the list of all projects visible to the current user.
        Unpublished projects are only visible to users that belong to that project.

        Visible projects are each displayed by means of an icon and a title.
        Both link to a landing page for the project.

        Returns
        -------
        string
            A list of captions of the projects,
            wrapped in a HTML string.
        """
        Mongo = self.Mongo
        Auth = self.Auth

        wrapped = []
        wrapped.append(self.actionButton("create", "projects"))

        for record in Mongo.getList("projects"):
            projectId = record._id
            permitted = Auth.authorise("projects", recordId=projectId, action="view")
            if not permitted:
                continue

            title = record.title
            candy = record.candy

            projectUrl = f"/projects/{projectId}"
            iconUrlBase = f"/data/projects/{projectId}/candy"
            button = self.actionButton(
                "delete",
                "projects",
                recordId=projectId,
            )
            caption = self.getCaption(title, candy, button, projectUrl, iconUrlBase)

            wrapped.append(caption)

        return "\n".join(wrapped)

    def insertProject(self):
        Mongo = self.Mongo
        Auth = self.Auth

        permitted = Auth.authorise("projects")
        if not permitted:
            return None

        User = Auth.myDetails()
        user = User.sub
        name = User.nickname

        title = "No title"

        dcMeta = dict(
            title=title,
            description=dict(abstract="No intro", description="No description"),
            creator=name,
        )
        projectId = Mongo.insertRecord("projects", title=title, meta=dict(dc=dcMeta))
        Mongo.insertRecord(
            "projectUsers",
            projectId=projectId,
            user=user,
            role="creator",
        )
        return projectId

    def getEditions(self, projectId):
        """Get the list of the editions of a project.

        Well, only if the project is visible to the current user.
        See `Content.getProjects()`.

        Editions are each displayed by means of an icon and a title.
        Both link to a landing page for the edition.

        Parameters
        ----------
        projectId: ObjectId
            The project in question.

        Returns
        -------
        string
            A list of captions of the editions of the project,
            wrapped in a HTML string.
        """
        Mongo = self.Mongo
        Auth = self.Auth

        wrapped = []

        for record in Mongo.getList("editions", projectId=projectId):
            editionId = record._id
            permitted = Auth.authorise("editions", recordId=editionId, action="view")
            if not permitted:
                continue

            title = record.title
            candy = record.candy

            editionUrl = f"/editions/{editionId}"
            iconUrlBase = f"/data/projects/{projectId}/editions/{editionId}/candy"
            button = self.actionButton(
                "delete",
                "editions",
                recordId=editionId,
            )
            caption = self.getCaption(title, candy, button, editionUrl, iconUrlBase)
            wrapped.append(caption)

        wrapped.append(self.actionButton("create", "editions", projectId=projectId))
        return "\n".join(wrapped)

    def insertEdition(self, projectId):
        Mongo = self.Mongo
        Auth = self.Auth

        permitted = Auth.authorise("editions", projectId=projectId)
        if not permitted:
            return None

        User = Auth.myDetails()
        name = User.nickname

        title = "No title"

        dcMeta = dict(
            title=title,
            description=dict(
                abstract="No intro",
                description="No description",
                provenance="No sources",
            ),
            creator=name,
        )
        editionId = Mongo.insertRecord(
            "editions", title=title, projectId=projectId, meta=dict(dc=dcMeta)
        )
        return editionId

    def getScenes(
        self,
        projectId,
        editionId,
        sceneId=None,
        viewer=None,
        version=None,
        action=None,
    ):
        """Get the list of the scenes of an edition of a project.

        Well, only if the project is visible to the current user.
        See `Content.getProjects()`.

        Scenes are each displayed by means of an icon a title and a row of buttons.
        The title is the file name (without the `.json` extension) of the scene.
        Both link to a landing page for the edition.

        One of the scenes is made *active*, i.e.
        it is loaded in a specific version of a viewer in a specific
        mode (`view` or `edit`).

        Which scene is loaded in which viewer and version in which mode,
        is determined by the parameters.
        If the parameters do not specify values, sensible defaults are chosen.

        Parameters
        ----------
        projectId: ObjectId
            The project in question.
        editionId: ObjectId
            The edition in question.
        sceneId: ObjectId, optional None
            The active scene. If None the default scene is chosen.
            A scene record specifies whether that scene is the default scene for
            that edition.
        viewer: string, optional None
            The viewer to be used for the 3D viewing. It should be a supported viewer.
            If None, the default viewer is chosen.
            The list of those viewers is in the `yaml/viewers.yml` file,
            which also specifies what the default viewer is.
        version: string, optional None
            The version of the chosen viewer that will be used.
            If no version or a non-existing version are specified,
            the latest existing version for that viewer will be chosen.
        action: string, optional `"view"`
            The mode in which the viewer should be opened.
            If the mode is `edit`, the viewer is opened in edit mode.
            All other modes lead to the viewer being opened in read-only
            mode.

        Returns
        -------
        string
            A list of captions of the scenes of the edition,
            with one caption replaced by a 3D viewer showing the scene.
            The list is wrapped in a HTML string.
        """
        Mongo = self.Mongo
        Auth = self.Auth
        Viewers = self.Viewers

        wrapped = []

        actions = Auth.authorise("editions", recordId=editionId)
        if "view" not in actions:
            return ""

        (viewer, version) = Viewers.check(viewer, version)

        wrapped = []

        for record in Mongo.getList("scenes", editionId=editionId):
            thisSceneId = record._id
            candy = record.candy

            isSceneActive = sceneId is None and record.default or record._id == sceneId
            titleText = f"""<span class="entrytitle">{record.name}</span>"""
            button = self.actionButton(
                "delete",
                "scenes",
                recordId=thisSceneId,
            )

            if isSceneActive:
                (frame, buttons) = Viewers.getFrame(
                    thisSceneId, actions, viewer, version, action
                )
                title = f"""<span class="entrytitle">{titleText}</span>"""
                content = f"""{frame}{title}{buttons}"""
                caption = self.wrapCaption(content, button, active=True)
            else:
                sceneUrl = f"/scenes/{record._id}"
                iconUrlBase = f"/data/projects/{projectId}/editions/{editionId}/candy"
                caption = self.getCaption(
                    titleText, candy, button, sceneUrl, iconUrlBase
                )

            wrapped.append(caption)

        wrapped.append(
            self.actionButton(
                "create", "scenes", projectId=projectId, editionId=editionId
            )
        )
        return "\n".join(wrapped)

    def insertScene(self, projectId, editionId):
        Mongo = self.Mongo
        Auth = self.Auth

        permitted = Auth.authorise("scenes", projectId=projectId)
        if not permitted:
            return None

        User = Auth.myDetails()
        name = User.nickname

        title = "No title"

        dcMeta = dict(
            title=title,
            creator=name,
        )
        sceneId = Mongo.insertRecord(
            "scenes",
            name=title,
            projectId=projectId,
            editionId=editionId,
            meta=dict(dc=dcMeta),
        )
        return sceneId

    def wrapCaption(self, content, button, active=False):
        activeCls = "active" if active else ""
        start = f"""<div class="captioncontent"><div class="caption {activeCls}">"""
        end = """</div>"""
        return f"""{start}{content}{end}{button}{end}"""

    def getCaption(self, titleText, candy, button, url, iconUrlBase):
        icon = self.getIcon(candy)
        title = f"""<span class="entrytitle">{titleText}</span>"""

        visual = (
            f"""<img class="previewicon" src="{iconUrlBase}/{icon}">""" if icon else ""
        )
        content = f"""<a class="entry" href="{url}">{visual}{title}</a>"""
        return self.wrapCaption(content, button)

    def getIcon(self, candy):
        """Select an icon from a set of candidates.

        Parameters
        ----------
        candy: dict
            A set of candidates, given as a dict, keyed by file names
            (without directory information) and valued by a boolean that
            indicates whether the image may act as an icon.

        Returns
        -------
        string or None
            The first candidate in candy that is an icon.
            If there are no candidates that qualify, None is returned.
        """

        if candy is None:
            return None
        first = [image for (image, isIcon) in candy.items() if isIcon]
        if first:
            return first[0]
        return None

    def getViewerFile(self, path):
        """Gets a viewer-related file from the file system.

        This is about files that are part of the viewer software.

        The viewer software is located in a specific directory on the server.
        This is the viewer base.

        Parameters
        ----------
        path: string
            The path of the viewer file within viewer base.

        Returns
        -------
        string
            The full path to the viewer file, if it exists.
            Otherwise, we raise an error that will lead to a 404 response.
        """
        Settings = self.Settings
        Messages = self.Messages

        dataDir = Settings.dataDir

        dataPath = f"{dataDir}/viewers/{path}"

        if not fileExists(dataPath):
            logmsg = f"Accessing {dataPath}: "
            logmsg += "does not exist. "
            Messages.error(
                msg="Accessing a file",
                logmsg=logmsg,
            )

        return dataPath

    def getData(self, path, projectId, editionId=None):
        """Gets a data file from the file system.

        All data files are located under a specific directory on the server.
        This is the data directory.
        Below that the files are organized by projects and editions.

        Parameters
        ----------
        path: string
            The path of the data file within project/edition directory
            within the data directory.
        projectId: ObjectId
            The id of the project in question.
        editionId: ObjectId, optional None
            The id of the edition in question.

        Returns
        -------
        string
            The full path of the data file, if it exists.
            Otherwise, we raise an error that will lead to a 404 response.
        """
        Settings = self.Settings
        Messages = self.Messages
        Auth = self.Auth

        dataDir = Settings.dataDir

        urlBase = (
            f"projects/{projectId}"
            if editionId is None
            else f"projects/{projectId}/editions/{editionId}"
        )

        dataPath = (
            f"{dataDir}/{urlBase}" if path is None else f"{dataDir}/{urlBase}/{path}"
        )

        if editionId is None:
            table = "projects"
            recordId = projectId
        else:
            table = "editions"
            recordId = editionId
        permitted = Auth.authorise(table, recordId=recordId, action="view")

        fexists = fileExists(dataPath)
        if not permitted or not fexists:
            logmsg = f"Accessing {dataPath}: "
            if not permitted:
                logmsg += "not allowed. "
            if not fexists:
                logmsg += "does not exist. "
            Messages.error(
                msg="Accessing a file",
                logmsg=logmsg,
            )

        return dataPath

    def getRecord(self, *args, **kwargs):
        """Get a record from MongoDb.

        This is just a rather trivial wrapper around a method with the same
        name `control.mongo.Mongo.getRecord`.

        We have this for reasons of abstraction:
        the `control.pages.Pages` object relies
        on this Content object to retrieve content,
        and does not want to know where the content comes from.
        """
        return self.Mongo.getRecord(*args, **kwargs)

    def actionButton(
        self, action, table, recordId=None, key=None, projectId=None, editionId=None
    ):
        """Puts a button on the interface, if that makes sense.

        The button, when pressed, will lead to an action on certain content.
        It will be checked first if that action is allowed for the current user.
        If not the button will not be shown.

        !!! note "Delete buttons"
            Even if a user is authorised to delete a record,
            it is not allowed to delete master records if its detail records
            still exist.
            In that case, no delete button is displayed. Instead we display a count
            of detail records.

        Parameters
        ----------
        action: string, optional None
            The type of action that will be performed if the button triggered.
        table: string
            the table to which the action applies;
        recordId: ObjectId, optional None
            the record in question
        projectId: ObjectId, optional None
            The project in question, if any.
            Needed to determine whether a press on the button is permitted.
        editionId: ObjectId, optional None
            The edition in question, if any.
            Needed to determine whether a press on the button is permitted.
        key: string, optional None
            If present, it identifies a metadata field that is stored inside the
            record. From the key, the value can be found.
        """
        Auth = self.Auth

        urlInsert = "/"
        if projectId is not None:
            urlInsert += f"projects/{projectId}/"
        if editionId is not None:
            urlInsert += f"editions/{editionId}/"

        permitted = Auth.authorise(
            table, recordId=recordId, projectId=projectId, action=action
        )

        if not permitted:
            return ""

        Settings = self.Settings
        actions = Settings.auth.actions

        disable = False
        report = ""

        if action == "delete":
            details = self.getDetailRecords(table, recordId)
            if len(details):
                disable = True
                report = ["<div>"]
                for (detailTable, detailRecords) in details.items():
                    nDetails = len(detailRecords)
                    plural = "" if nDetails == 1 else "s"
                    detailRep = detailTable.rstrip("s") + plural

                    report.append(
                        """<span class="dreport">"""
                        f"""{nDetails}&nbsp;{detailRep}</span><br>"""
                    )
                report.append("</div>")
                report = "<br>" + "\n".join(report)

        text = actions.get(action, action)
        tableItem = table.rstrip("s")
        keyRepTip = "" if key is None else f" {key} of"
        keyRepUrl = "" if key is None else f"/{key}"
        recordIdRep = "" if recordId is None else f"/{recordId}"
        can = "Cannot " if disable else ""
        elem = "span" if disable else "a"
        cls = " disabled" if disable else ""
        tip = (
            f"{action} new {tableItem}"
            if action == "create"
            else f"{can}{action}{keyRepTip} this {tableItem}"
        )
        href = (
            ""
            if disable
            else 'href="'
            + (
                f"{urlInsert}{table}/insert"
                if action == "create"
                else f"/{table}{recordIdRep}{keyRepUrl}/{action}"
            )
            + '"'
        )

        return f"""
            <{elem} title="{tip}" {href} class="button large {cls}">{text}</{elem}>
            {report}
        """
