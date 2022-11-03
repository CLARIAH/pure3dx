from markdown import markdown

from control.helpers.files import fileExists
from control.helpers.generic import AttrDict


COMPONENT = dict(
    me=(None, None, None, None),
    home=("texts/intro", "md", True, ""),
    about=("texts/about", "md", True, "## About\n\n"),
    intro=("texts/intro", "md", True, ""),
    usage=("texts/usage", "md", True, "## Guide\n\n"),
    description=("texts/description", "md", True, "## Description\n\n"),
    sources=("texts/sources", "md", True, "## Sources\n\n"),
    title=("meta/dc", "json", "dc.title", None),
    icon=("candy/icon", "png", None, None),
    list=(None, None, None, None),
)


class Content:
    def __init__(self, Settings, Viewers, Messages, Mongo):
        """Retrieving content from database and file system.

        This class has methods to retrieve various pieces of content
        from the data sources, and hand it over to the `control.pages.Pages`
        class that will compose a response out of it.

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
        self.Viewers = Viewers
        self.Messages = Messages
        Messages.debugAdd(self)
        self.Mongo = Mongo

    def addAuth(self, Auth):
        """Give this object a handle to the Auth object.

        Because of cyclic dependencies some objects require to be given
        a handle to Auth after their initialization.
        """
        self.Auth = Auth

    def getMeta(self, nameSpace, fieldPath, projectId=None, editionId=None, asMd=False):
        """Retrieve a metadata string.

        Metadata sits in a big, potentially deeply nested dictionary of keys
        and values.
        This function retrieves the information based on a path of keys.

        Parameters
        ----------
        nameSpace: string
            The first selector in the metadata, e.g. `dc` for Dublin Core.
        """
        Mongo = self.Mongo

        fields = fieldPath.split(".")

        meta = (
            Mongo.getRecord("editions", _id=editionId)
            if editionId is not None
            else Mongo.getRecord("projects", _id=projectId)
            if projectId is not None
            else Mongo.getRecord("meta")
        ).meta or {}
        text = meta.get(nameSpace, {}).get(fields[0], "" if len(fields) == 0 else {})

        for field in fields[1:]:
            text = text.get(field, {})
        if type(text) is not str:
            text = ""
        return markdown(text) if asMd else text

    def getSurprise(self):
        return "<h2>You will be surprised!</h2>"

    def getProjects(self):
        Mongo = self.Mongo
        Auth = self.Auth

        wrapped = []

        for row in Mongo.execute("projects", "find"):
            row = AttrDict(row)
            projectId = row._id
            permitted = Auth.authorise("view", project=projectId)
            if not permitted:
                continue

            title = row.title
            candy = row.candy

            projectUrl = f"/projects/{projectId}"
            projectName = row.name
            iconUrlBase = f"/data/projects/{projectName}/candy"
            caption = self.getCaption(title, candy, projectUrl, iconUrlBase)
            wrapped.append(caption)

        return "\n".join(wrapped)

    def getEditions(self, projectId):
        Mongo = self.Mongo
        Auth = self.Auth

        projectInfo = Mongo.getRecord("projects", _id=projectId)
        projectName = projectInfo.name

        wrapped = []

        for row in Mongo.execute("editions", "find", dict(projectId=projectId)):
            row = AttrDict(row)
            editionId = row._id
            permitted = Auth.authorise("view", project=projectId, edition=editionId)
            if not permitted:
                continue

            title = row.title
            candy = row.candy

            editionUrl = f"/editions/{editionId}"
            editionName = row.name
            iconUrlBase = f"/data/projects/{projectName}/editions/{editionName}/candy"
            caption = self.getCaption(title, candy, editionUrl, iconUrlBase)
            wrapped.append(caption)

        return "\n".join(wrapped)

    def getScenes(
        self,
        projectId,
        editionId,
        sceneId=None,
        viewer="",
        version="",
        action="view",
    ):
        Mongo = self.Mongo
        Auth = self.Auth
        Viewers = self.Viewers

        projectInfo = Mongo.getRecord("projects", _id=projectId)
        projectName = projectInfo.name
        editionInfo = Mongo.getRecord("editions", _id=editionId)
        editionName = editionInfo.name

        wrapped = []

        permitted = Auth.authorise("view", project=projectId, edition=editionId)
        if not permitted:
            return []

        action = Auth.checkModifiable(projectId, editionId, action)
        actions = ["view"]
        if Auth.isModifiable(projectId, editionId):
            actions.append("edit")

        (viewer, version) = Viewers.check(viewer, version)

        wrapped = []

        for row in Mongo.execute("scenes", "find", dict(editionId=editionId)):
            row = AttrDict(row)

            isSceneActive = sceneId is None and row.default or row._id == sceneId
            (frame, buttons) = Viewers.getButtons(
                row._id, actions, isSceneActive, viewer, version, action
            )

            sceneUrl = f"/scenes/{row._id}"
            iconUrlBase = f"/data/projects/{projectName}/editions/{editionName}/candy"
            caption = self.getCaption(
                row.name,
                row.candy,
                sceneUrl,
                iconUrlBase,
                active=isSceneActive,
                frame=frame,
                buttons=buttons,
            )
            wrapped.append(caption)

        return "\n".join(wrapped)

    def getCaption(
        self, title, candy, url, iconUrlBase, active=False, buttons="", frame=""
    ):
        icon = self.getIcon(candy)

        activeCls = "active" if active else ""
        start = f"""<div class="caption {activeCls}">"""
        visual = (
            f"""<img class="previewicon" src="{iconUrlBase}/{icon}">""" if icon else ""
        )
        heading = (
            f"""{frame}<a href="{url}">{title}</a>"""
            if frame
            else f"""<a href="{url}">{visual}{title}</a>"""
        )
        end = """</div>"""
        caption = f"""{start}{heading}{buttons}{end}"""
        return caption

    def getIcon(self, candy):
        if candy is None:
            return None
        first = [image for (image, isIcon) in candy.items() if isIcon]
        if first:
            return first[0]
        return None

    def getViewerFile(self, path):
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

        with open(dataPath, "rb") as fh:
            textData = fh.read()

        return textData

    def getData(self, path, projectName="", editionName=""):
        Settings = self.Settings
        Messages = self.Messages
        Auth = self.Auth

        dataDir = Settings.dataDir

        urlBase = (
            "texts"
            if projectName == "" and editionName == ""
            else f"projects/{projectName}"
            if editionName == ""
            else f"projects/{projectName}/editions/{editionName}"
        )

        dataPath = f"{dataDir}/{urlBase}/{path}"

        permitted = (
            True
            if urlBase == "texts"
            else Auth.authorise(
                "view", project=projectName, edition=editionName, byName=True
            )
        )

        fexists = fileExists(dataPath)
        if not permitted or not fexists:
            logmsg = f"Accessing {dataPath}: "
            if not permitted:
                logmsg = "not allowed. "
            if not fexists:
                logmsg += "does not exist. "
            Messages.error(
                msg="Accessing a file",
                logmsg=logmsg,
            )

        with open(dataPath, "rb") as fh:
            textData = fh.read()

        return textData

    def getRecord(self, *args, **kwargs):
        return self.Mongo.getRecord(*args, **kwargs)
