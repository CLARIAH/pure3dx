from textwrap import dedent
from flask import render_template, make_response
from control.mongo import castObjectId
from markdown import markdown

TABS = (
    ("home", "Home", True),
    ("about", "About", True),
    ("projects", "3D Projects", True),
    ("directory", "3D Directory", False),
    ("surpriseme", "Surprise Me", True),
    ("advancedsearch", "Advanced Search", False),
)

CAPTIONS = {
    "title": ("{}", True),
    "description.abstract": ("Intro", True),
    "description.description": ("Description", True),
    "provenance": ("About", True),
    "instructionalMethod": ("How to use", True),
}


class Pages:
    def __init__(self, Settings, Viewers, Messages, Content, Auth, Users):
        """Making responses that can be displayed as web pages.

        This class has methods that correspond to routes in the app,
        for which they get the data (using `control.content.Content`),
        which gets then wrapped in HTML.

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
        Users: object
            Singleton instance of `control.users.Users`.
        Content: object
            Singleton instance of `control.content.Content`.
        Auth: object
            Singleton instance of `control.auth.Auth`.
        Users: object
            Singleton instance of `control.users.Users`.
        """
        self.Settings = Settings
        self.Viewers = Viewers
        self.Messages = Messages
        Messages.debugAdd(self)
        self.Content = Content
        self.Auth = Auth
        self.Users = Users

    def home(self):
        left = self.putTexts("title@1 + description.abstract@2")
        return self.page("home", left=left)

    def about(self):
        left = self.putTexts("title@1 + description.abstract@2")
        right = self.putTexts(
            "description.description@2 + provenance@2"
        )
        return self.page("about", left=left, right=right)

    def surprise(self):
        Content = self.Content
        surpriseMe = Content.getSurprise()
        left = self.putTexts("title@1")
        right = surpriseMe
        return self.page("surpriseme", left=left, right=right)

    def projects(self):
        Content = self.Content
        projects = Content.getProjects()
        left = self.putTexts("title@2") + projects
        return self.page("projects", left=left)

    def project(self, projectId):
        Content = self.Content
        projectId = castObjectId(projectId)
        editions = Content.getEditions(projectId)
        left = self.putTexts("title@3", projectId=projectId) + editions
        right = self.putTexts(
            "description.abstract@4 + description.description@4 + "
            "provenance@4 + instructionalMethod@4",
            projectId=projectId,
        )
        return self.page("projects", left=left, right=right, projectId=projectId)

    def edition(self, editionId):
        Content = self.Content
        editionId = castObjectId(editionId)
        editionInfo = Content.getRecord("editions", _id=editionId)
        projectId = editionInfo.projectId
        return self.scenes(projectId, editionId, None, None, None, None)

    def scene(self, sceneId, viewer, version, action):
        Content = self.Content
        sceneId = castObjectId(sceneId)
        sceneInfo = Content.getRecord("scenes", _id=sceneId)
        projectId = sceneInfo.projectId
        editionId = sceneInfo.editionId
        return self.scenes(projectId, editionId, sceneId, viewer, version, action)

    def scenes(self, projectId, editionId, sceneId, viewer, version, action):
        Content = self.Content
        Auth = self.Auth

        action = Auth.checkModifiable(projectId, editionId, action)
        back = self.backLink(projectId)
        scenes = Content.getScenes(
            projectId,
            editionId,
            sceneId=sceneId,
            viewer=viewer,
            version=version,
            action=action,
        )
        left = (
            back
            + self.putTexts("title@4", projectId=projectId, editionId=editionId)
            + scenes
        )
        right = self.putTexts(
            "description.abstract@5 + description.description@5 + "
            "provenance@5 + instructionalMethod@5",
            projectId=projectId,
            editionId=editionId,
        )
        return self.page(
            "projects",
            left=left,
            right=right,
            projectId=projectId,
            editionId=editionId,
        )

    def viewerFrame(self, sceneId, viewer, version, action):
        Content = self.Content
        Viewers = self.Viewers
        Auth = self.Auth

        sceneId = castObjectId(sceneId)
        sceneInfo = Content.getRecord("scenes", _id=sceneId)
        sceneName = sceneInfo.name

        projectId = sceneInfo.projectId
        projectName = Content.getRecord("projects", _id=projectId).name

        editionId = sceneInfo.editionId
        editionName = Content.getRecord("editions", _id=editionId).name

        urlBase = f"projects/{projectName}/editions/{editionName}/"

        action = Auth.checkModifiable(projectId, editionId, action)

        viewerCode = Viewers.genHtml(urlBase, sceneName, viewer, version, action)
        return render_template("viewer.html", viewerCode=viewerCode)

    def viewerResource(self, path):
        Content = self.Content

        data = Content.getViewerFile(path)
        return make_response(data)

    def dataProjects(self, projectName, editionName, path):
        Content = self.Content

        data = Content.getData(path, projectName=projectName, editionName=editionName)
        return make_response(data)

    def page(
        self,
        url,
        projectId=None,
        editionId=None,
        left="",
        right="",
    ):
        Settings = self.Settings
        Messages = self.Messages
        Auth = self.Auth
        Users = self.Users

        userActive = Auth.user._id

        navigation = self.navigation(url)
        testUsers = Users.wrapTestUsers(userActive) if Settings.testMode else ""

        return render_template(
            "index.html",
            versionInfo=Settings.versionInfo,
            navigation=navigation,
            materialLeft=left,
            materialRight=right,
            messages=Messages.generateMessages(),
            testUsers=testUsers,
        )

    def navigation(self, url):
        search = dedent(
            """
            <span class="search-bar">
                <input
                    type="search"
                    name="search"
                    placeholder="search item"
                    class="button disabled"
                >
                <input type="submit" value="Search" class="button disabled">
            </span>
            """
        )
        html = ["""<div class="tabs">"""]

        for (tab, label, enabled) in TABS:
            active = "active" if url == tab else ""
            elem = "a" if enabled else "span"
            href = f""" href="/{tab}" """ if enabled else ""
            cls = active if enabled else "disabled"
            html.append(
                dedent(
                    f"""
                    <{elem}
                        {href}
                        class="button large {cls}"
                    >{label}</{elem}>
                    """
                )
            )
        html.append(search)
        html.append("</div>")
        return "\n".join(html)

    def backLink(self, projectId):
        projectUrl = f"/projects/{projectId}"
        cls = """ class="button" """
        href = f""" href="{projectUrl}" """
        text = """back to the project page"""
        return f"""<p><a {cls} {href}>{text}</a></p>"""

    def putText(self, field, level, projectId=None, editionId=None):
        Content = self.Content

        content = Content.getMeta("dc", field, projectId=projectId, editionId=editionId)
        info = CAPTIONS.get(field, None)

        if info is None:
            return content

        (heading, asMd) = info
        skip = "{}" in heading

        if asMd:
            heading = markdown(heading)
            content = markdown(content)

        return dedent(
            f"""
            <h{level}>{heading.format(content)}</h{level}>
            {"" if skip else content}
            """
        )

    def putTexts(self, fieldSpecs, projectId=None, editionId=None):
        return "\n".join(
            self.putText(
                *fieldSpec.strip().split("@", 1),
                projectId=projectId,
                editionId=editionId,
            )
            for fieldSpec in fieldSpecs.split("+")
        )
