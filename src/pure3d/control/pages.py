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

        Most methods generate a response that contains the content of a complete
        page. For those methods we do not document the return value.

        Some methods return something different.
        If so, it the return value will be documented.

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
        """The site-wide home page."""
        left = self.putTexts("title@1 + description.abstract@2")
        return self.page("home", left=left)

    def about(self):
        """The site-wide about page."""
        left = self.putTexts("title@1 + description.abstract@2")
        right = self.putTexts("description.description@2 + provenance@2")
        return self.page("about", left=left, right=right)

    def surprise(self):
        """The "surprise me!" page."""
        Content = self.Content
        surpriseMe = Content.getSurprise()
        left = self.putTexts("title@1")
        right = surpriseMe
        return self.page("surpriseme", left=left, right=right)

    def projects(self):
        """The page with the list of projects."""
        Content = self.Content
        projects = Content.getProjects()
        left = self.putTexts("title@2") + projects
        return self.page("projects", left=left)

    def project(self, projectId):
        """The landing page of a project.

        Parameters
        ----------
        projectId: ObjectId
            The project in question.
        """
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
        """The landing page of an edition.

        This page contains a list of scenes.
        One of these scenes will be loaded in a 3D viewer.
        It is dependent on defaults which scene in which viewer/version/mode.

        Parameters
        ----------
        editionId: ObjectId
            The edition in question.
            From the edition record we can find the project too.
        """
        Content = self.Content
        editionId = castObjectId(editionId)
        editionInfo = Content.getRecord("editions", _id=editionId)
        projectId = editionInfo.projectId
        return self.scenes(projectId, editionId, None, None, None, None)

    def scene(self, sceneId, viewer, version, action):
        """The landing page of an edition, but with a scene marked as active.

        This page contains a list of scenes.
        One of these scenes is chosen as the active scene and
        will be loaded in a 3D viewer.
        It is dependent on the parameters and/or defaults
        in which viewer/version/mode.

        Parameters
        ----------
        sceneId: ObjectId
            The active scene in question.
            From the scene record we can find the edition and the project too.
        viewer: string or None
            The viewer to use.
        version: string or None
            The version to use.
        action: string or None
            The mode in which the viewer is to be used (`view` or `edit`).
        """
        Content = self.Content
        sceneId = castObjectId(sceneId)
        sceneInfo = Content.getRecord("scenes", _id=sceneId)
        projectId = sceneInfo.projectId
        editionId = sceneInfo.editionId
        return self.scenes(projectId, editionId, sceneId, viewer, version, action)

    def scenes(self, projectId, editionId, sceneId, viewer, version, action):
        """Workhorse for `Pages.edition()` and `Pages.scene()`.

        The common part between the two functions mentioned.
        """
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
        """The page loaded in an iframe where a 3D viewer operates.

        Parameters
        ----------
        sceneId: ObjectId
            The scene that is shown.
        viewer: string or None
            The viewer to use.
        version: string or None
            The version to use.
        action: string or None
            The mode in which the viewer is to be used (`view` or `edit`).
        """
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
        """Components requested by viewers.

        This is the javascript code, the css, and other resources
        that are part of the 3D viewer software.

        Parameters
        ----------
        path: string
            Path on the file system under the viewers base directory
            where the resource resides.
        """
        Content = self.Content

        data = Content.getViewerFile(path)
        return make_response(data)

    def dataProjects(self, projectName, editionName, path):
        """Data content requested by viewers.

        This is the material belonging to the scene,
        the scene json itself and additional resources,
        that are part of the user contributed content that is under
        control of the viewer: annotations, media, etc.

        Parameters
        ----------
        projectName: string or None
            If not None, the name of a project under which the resource
            is to be found.
        editionName: string or None
            If not None, the name of an edition under which the resource
            is to be found.
        path: string
            Path on the file system under the data directory
            where the resource resides.
            If there is a project and or edition given,
            the path is relative to those.
        """
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
        """Workhorse function to get content on the page.

        Parameters
        ----------
        url: string
            Initial part of the url that triggered the page function.
            This part is used to make one of the tabs on the web page active.
        projectId: ObjectId, optional None
            The project in question, if any.
            Maybe needed for back links to the project.
        editionId: ObjectId, optional None
            The edition in question, if any.
            Maybe needed for back links to the edition.
        left: string, optional ""
            Content for the left column of the page.
        right: string, optional ""
            Content for the right column of the page.
        """
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

    def authWebdav(self, projectName, editionName, path, action):
        """Authorises a webdav request.

        When a viewer makes a WebDAV request to the server,
        that request is first checked here for authorisation.

        See `control.webdavapp.dispatchWebdav()`.

        Parameters
        ----------
        projectName: string
            The project in question.
        editionName: string
            The edition in question.
        path: string
            The path relative to the directory of the edition.
        action: string
            The operation that the WebDAV request wants to do on the data
            (`view` or `edit`).

        Returns
        -------
        boolean
            Whether the action is permitted on ths data by the current user.
        """
        Messages = self.Messages
        Auth = self.Auth

        permitted = Auth.authorise(
            action,
            project=projectName,
            edition=editionName,
            byName=True,
        )
        if not permitted:
            Messages.info(
                logmsg=f"WEBDAV unauthorised by user {Auth.user}"
                f" on {projectName=} {editionName=} {path=}"
            )
        return permitted

    def navigation(self, url):
        """Generates the navigation controls.

        Especially the tab bar.

        Parameters
        ----------
        url: string
            Initial part of the url on the basis of which one of the
            tabs can be made active.

        Returns
        -------
        string
            The HTML of the navigation.
        """
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
        """Makes a link to the landing page of a project.

        Parameters
        ----------
        projectId: ObjectId
            The project in question.
        """
        projectUrl = f"/projects/{projectId}"
        cls = """ class="button" """
        href = f""" href="{projectUrl}" """
        text = """back to the project page"""
        return f"""<p><a {cls} {href}>{text}</a></p>"""

    def putText(self, nameSpace, fieldPath, level, projectId=None, editionId=None):
        """Puts a piece of metadata on the web page.

        The meta data is retrieved and then wrapped accordingly.

        Parameters
        ----------
        nameSpace: string
            The namespace of the metadata, e.g. `dc` (Dublin Core)
        fieldPath: string
            `.`-separated list of fields into a metadata structure.
        level: integer 1-6
            The heading level in which the text must be wrapped.
        projectId: ObjectId or None
            The project in question
        editionId: ObjectId or None
            The edition in question

        Returns
        -------
        string
            The HTML of the formatted text.
        """
        Content = self.Content

        content = Content.getMeta(
            nameSpace, fieldPath, projectId=projectId, editionId=editionId
        )
        info = CAPTIONS.get(fieldPath, None)

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

    def putTexts(self, nameSpace, fieldSpecs, projectId=None, editionId=None):
        """Puts a several pieces of metadata on the web page.

        See `Pages.putText()` for the parameter specifications.

        One difference:

        Parameters
        ----------
        fieldSpecs: string
            `,`-separated list of fieldSpecs

        Returns
        -------
        string
            The join of the individual results of `Pages.putText`.
        """
        return "\n".join(
            self.putText(
                nameSpace,
                *fieldSpec.strip().split("@", 1),
                projectId=projectId,
                editionId=editionId,
            )
            for fieldSpec in fieldSpecs.split("+")
        )
