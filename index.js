URLS=[
"control/index.html",
"control/webdavapp.html",
"control/auth.html",
"control/collect.html",
"control/editsessions.html",
"control/config.html",
"control/users.html",
"control/mongo.html",
"control/pages.html",
"control/content.html",
"control/messages.html",
"control/app.html",
"control/viewers.html",
"control/helpers/index.html",
"control/helpers/files.html",
"control/helpers/generic.html",
"control/prepare.html"
];
INDEX=[
{
"ref":"control",
"url":0,
"doc":""
},
{
"ref":"control.webdavapp",
"url":1,
"doc":""
},
{
"ref":"control.webdavapp.getWebdavApp",
"url":1,
"doc":"Configure a webapp that provides WebDAV. We get the WebDAV app ready-made from [WsgiDav](https: wsgidav.readthedocs.io/en/latest/), and configure it here.",
"func":1
},
{
"ref":"control.webdavapp.dispatchWebdav",
"url":1,
"doc":"Combines the main app with the webdavapp. A WSGI app is essentially a function that takes a request environment and a start-response function and produces a response. We combine two wsgi apps by defining a new WSGI function out of the WSGI functions of the component apps. We call this function the dispatcher. The combined function works so that requests with urls starting with a certain prefix are dispatched to the webdav app, while all other requests are handled by the main app. However, we must do proper authorisation for the calls that are sent to the webdav app. But the business-logic for authorisation is in the main app, while we want to leave the code of the webdav app untouched. We solve this by making the dispatcher so that it feeds every WebDAV request to the main app first. We mark those requests by prepending  /auth in front of the original url. The main app is programmed to react to such requests by returning a boolean to the dispatcher, instead of sending a response to the client. See  control.pages.Pages.authWebdav . The dispatcher interprets this boolean as telling whether the request is authorized. If so, it sends the original request to the webdav app. If not, it prepends  /no to the original url and sends the request to the main app, which is programmed to respond with a 404 to such requests.",
"func":1
},
{
"ref":"control.webdavapp.appFactory",
"url":1,
"doc":"Make a WebDAV enabled app.  Combine the main app with an other wsgi app that can handle WebDAV requests. There is a Python module that offers a wsgi app out of the box that can talk WebDAV, we configure it in  getWebdavApp() . The  dispatchWebdav() function combines the current app with this WebDAV app at a deep level, before requests are fed to either app.  ! note \"Authorisation\" Authorisation of WebDAV requests happens in the main app. See  dispatchWebdav() .",
"func":1
},
{
"ref":"control.auth",
"url":2,
"doc":""
},
{
"ref":"control.auth.Auth",
"url":2,
"doc":"All about authorised data access. This class knows users and content, and decides whether the current user is authorised to perform certain actions on content in question. It is instantiated by a singleton object. This object has a member  user that contains the data of the current user if there is a current user. Parameters      Settings:  control.helpers.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo . Users: object Singleton instance of  control.users.Users . Content: object Singleton instance of  control.content.Content ."
},
{
"ref":"control.auth.Auth.clearUser",
"url":2,
"doc":"Clear current user. The  user member of Auth is cleard. Note that it is not deleted, only its members are removed.",
"func":1
},
{
"ref":"control.auth.Auth.getUser",
"url":2,
"doc":"Get user data. Parameters      userId: ObjectId The id of a user in the users table of the MongoDb database. Returns    - boolean Whether a user with that id has been found. The data of the user record that has been found is stored in the  user member of Auth.",
"func":1
},
{
"ref":"control.auth.Auth.checkLogin",
"url":2,
"doc":"Get user data. Retrieves a user id from the current session, looks up the corresponding user, and fills the  user member of Auth accordingly. In test mode, the user id is obtained from the query string. There is a list of test user buttons on the interface, and they all pass a user id in the querystring of their  href attribute. In production mode, the current session will be inspected for data that corresponds with the logged in user. Returns    - boolean Whether a user with a valid id has been found in the current session.",
"func":1
},
{
"ref":"control.auth.Auth.authenticate",
"url":2,
"doc":"Authenticates the current user. Checks whether there is a current user and whether that user is fully known, i.e. in the users collection of the mongoDb. If there is a current user unknown in the database, the current user will be cleared. Parameters      login: boolean, optional False Use True to deal with a user that has just logged in. It will retrieve the corresponding user data from MongoDb and populate the  user member of Auth. Returns    - boolean Whether the current user is authenticated.",
"func":1
},
{
"ref":"control.auth.Auth.authenticated",
"url":2,
"doc":"Cheap check whether there is a current authenticated user. The  user member of Auth is inspected: does it contain an id? If so, that is taken as proof that we have a valid user.  ! hint \"auhtenticate versus authenticated\" We try to enforce at all times that if there is data in the  user member of Auth, it is the correct data of an authenticated user. But there may arise edge cases, e.g. when a user is successfully authenticated, but then removed from the database by an admin. Good practice is: in every request that needs an authenticated user:  call  Auth.authenticate() the first time  call  authenticated after that. With this practice, we can shield a lot of code with the cheaper  Auth.authenticated() function.",
"func":1
},
{
"ref":"control.auth.Auth.deauthenticate",
"url":2,
"doc":"Logs off the current user. That means that the  user memebr of Auth is cleared, and the current session is popped.",
"func":1
},
{
"ref":"control.auth.Auth.authorise",
"url":2,
"doc":"Authorise the current user to access a piece of content.  ! note \"Requests may come from different senders\" When 3D viewers are active, they may fire their own requests to this app. These 3D viewers do not know about MongoDb ids, all they know are the names of files and directories. Parameters      action: string The kind of access:  view ,  edit , etc. project: string or ObjectId The project that is being accessed, if any. edition: string or ObjectId The edition that is being accessed, if any. byName: boolean, optional False Whether the project and edition parameters contain an ObjectId. If not, it is assumed they contain a name. Sometimes we know projects and editions by their id, especially when we have retrieved them from MongoDb. But some routes access projects and editions on the file system, and then we have only their names. This happens in case the 3D viewers access the file system directly. Returns    - boolean Whether the current user is authorised.",
"func":1
},
{
"ref":"control.auth.Auth.isModifiable",
"url":2,
"doc":"Whether the current user may modify content. The content may be outside any project (both  projectId and  editionId are None), within a project but outside any edition ( editionId is None), or within an edition ( editionId is not None). Parameters      projectId: ObjectId or None MongoDB id of the project in question. editionId: ObjectId or None MongoDB id of the edition in question.",
"func":1
},
{
"ref":"control.auth.Auth.checkModifiable",
"url":2,
"doc":"Like  Auth.isModifiable() , but returns an allowed action. This function \"demotes\" an action to an allowed action if the action itself is not allowed. Parameters      action: string An intended action. Returns    - string If the action is a modifying action, but the content is not modifiable, it returns  view . Otherwise it returns the action itself.",
"func":1
},
{
"ref":"control.auth.Auth.user",
"url":2,
"doc":"Data of the current user. If there is no current user, it is has no members. Otherwise, it has member  _id , the mongodb id of the current user. It may also have additional members, such as  name and  role ."
},
{
"ref":"control.collect",
"url":3,
"doc":""
},
{
"ref":"control.collect.Collect",
"url":3,
"doc":"Provides initial data collection into MongoDb. Normally, this does not have to run, since the MongoDb is persistent. Only when the MongoDb of the Pure3D app is fresh, or when the MongoDb is out of sync with the data on the filesystem it must be initialized. It reads:  configuration data of the app,  project data on the file system  workflow data on the file system  3D-viewer code on file system The project-, workflow, and viewer data should be placed on the same share in the file system, by a provision step that is done on the host. The data for the supported viewers is in repo  pure3d-data , under  viewers . For testing, there is  exampledata in the same  pure3d-data repo. The provision step should copy the contents of  exampledata to the  data directory of this repo ( pure3dx ). If data collection is triggered in test mode, the user table will be wiped, and the test users present in the example data will be imported. Otherwise the user table will be left unchanged. Parameters      Settings:  control.helpers.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo ."
},
{
"ref":"control.collect.Collect.trigger",
"url":3,
"doc":"Determines whether data collection should be done. We only do data collection if the environment variable  docollect has the value  v . We also prevent this from happening twice, which occurs when Flask runs in debug mode, since then the code is loaded twice. We guard against this by inspecting the environment variable  WERKZEUG_RUN_MAIN . If it is set, we are already running the app, and data collection should be inhibited, because it has been done just before Flask started running.",
"func":1
},
{
"ref":"control.collect.Collect.fetch",
"url":3,
"doc":"Performs a data collection, but only if triggered by the right conditions. See also  Collect.trigger() ",
"func":1
},
{
"ref":"control.collect.Collect.clearDb",
"url":3,
"doc":"Clears selected collections in the MongoDb. All collections that will be filled with data from the filesystem will be wiped.  ! \"Users collection will be wiped in test mode\" If in test mode, the  users collection will be wiped, and then filled from the example data.",
"func":1
},
{
"ref":"control.collect.Collect.doOuter",
"url":3,
"doc":"Collects data not belonging to specific projects.",
"func":1
},
{
"ref":"control.collect.Collect.doProjects",
"url":3,
"doc":"Collects data belonging to projects.",
"func":1
},
{
"ref":"control.collect.Collect.doProject",
"url":3,
"doc":"Collects data belonging to a specific project. Parameters      projectsPath: string Path on the filesystem to the projects directory projectName: string Directory name of the project to collect.",
"func":1
},
{
"ref":"control.collect.Collect.doEditions",
"url":3,
"doc":"Collects data belonging to the editions of a project. Parameters      projectId: ObjectId MongoId of the project to collect. projectPath: string Path on the filesystem to the directory of this project",
"func":1
},
{
"ref":"control.collect.Collect.doEdition",
"url":3,
"doc":"Collects data belonging to a specific edition. Parameters      projectId: ObjectId MongoId of the project to which the edition belongs. editionsPath: string Path on the filesystem to the editions directory within this project. editionName: string Directory name of the edition to collect.",
"func":1
},
{
"ref":"control.collect.Collect.doWorkflow",
"url":3,
"doc":"Collects workflow information from yaml files.  ! note \"Test users\" This includes test users when in test mode.",
"func":1
},
{
"ref":"control.editsessions",
"url":4,
"doc":""
},
{
"ref":"control.editsessions.EditSessions",
"url":4,
"doc":"Managing edit sessions of users. This class has methods to create and delete edit sessions for users, which guard them from overwriting each other's data. Edit sessions prevent users from editing the same piece of content, in particular it prevents multiple  edit -mode 3D viewers being active with the same scene. It is instantiated by a singleton object. Parameters      Mongo: object Singleton instance of  control.mongo.Mongo ."
},
{
"ref":"control.config",
"url":5,
"doc":""
},
{
"ref":"control.config.Config",
"url":5,
"doc":"All configuration details of the app. It is instantiated by a singleton object. Settings will be collected from the environment:  yaml files  environment variables  files and directories (for supported viewer software)  ! note \"Missing information\" If essential information is missing, the flask app will not be started, and no webserving will take place. Parameters      Messages: object Singleton instance of  control.messages.Messages . flask: boolean, optional True If False, only those settings are fetched that do not have relevance for the actual web serving by flask application. This is used for code that runs prior to web serving, e.g. data collection in  control.collect.Collect ."
},
{
"ref":"control.config.Config.checkEnv",
"url":5,
"doc":"Collect the relevant information. If essential information is missing, processing stops. This is done by setting the  good member of Config to False. Parameters      flask: boolean Whether to collect all, or a subset of variables that are not used for actually serving pages.",
"func":1
},
{
"ref":"control.config.Config.checkRepo",
"url":5,
"doc":"Get the location of the pure3dx repository on the file system.",
"func":1
},
{
"ref":"control.config.Config.checkVersion",
"url":5,
"doc":"Get the current version of the pure3d app.",
"func":1
},
{
"ref":"control.config.Config.checkSecret",
"url":5,
"doc":"Obtain a secret. This is secret information used for encrypting sessions. It resides somewhere on the file system, outside the pure3d repository.",
"func":1
},
{
"ref":"control.config.Config.checkData",
"url":5,
"doc":"Get the location of the project data on the file system.",
"func":1
},
{
"ref":"control.config.Config.checkModes",
"url":5,
"doc":"Determine whether flask is running in test/debug or production mode.",
"func":1
},
{
"ref":"control.config.Config.checkMongo",
"url":5,
"doc":"Obtain the connection details for MongDB. It is not checked whether connection with MongoDb actually works with these credentials.",
"func":1
},
{
"ref":"control.config.Config.checkSettings",
"url":5,
"doc":"Read the yaml file with application settings.",
"func":1
},
{
"ref":"control.config.Config.checkAuth",
"url":5,
"doc":"Read gthe yaml file with the authorisation rules.",
"func":1
},
{
"ref":"control.config.Config.checkViewers",
"url":5,
"doc":"Make an inventory of the supported 3D viewers.",
"func":1
},
{
"ref":"control.config.Config.Settings",
"url":5,
"doc":"The actual configuration settings are stored here."
},
{
"ref":"control.users",
"url":6,
"doc":""
},
{
"ref":"control.users.Users",
"url":6,
"doc":"All about users and the current users. This class has methods to login/authenticate a user, to logout/deauthenticate users, to retrieve users' data. It is instantiated by a singleton object. Parameters      Settings:  control.helpers.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo ."
},
{
"ref":"control.users.Users.wrapTestUsers",
"url":6,
"doc":"Generate HTML for login buttons for test users. Only produces a non-empty result if the app is in test mode. Parameters      userActive: ObjectId The id of the user that is currently logged in. The button for this users will be rendered as the active one.",
"func":1
},
{
"ref":"control.mongo",
"url":7,
"doc":""
},
{
"ref":"control.mongo.castObjectId",
"url":7,
"doc":"Try to cast the value as an ObjectId. Paramaters      value:string The value to cast, normally a string representation of a BSON ObjectId. Returns    - ObjectId | None The corresponding BSON ObjectId if the input is a valid representation of such an id, otherwise  None .",
"func":1
},
{
"ref":"control.mongo.Mongo",
"url":7,
"doc":"CRUD interface to content in the MongoDb database. This class has methods to connect to a MongoDb database, to query its data, to insert, update and delete data. It is instantiated by a singleton object. Parameters      Settings:  control.helpers.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages ."
},
{
"ref":"control.mongo.Mongo.connect",
"url":7,
"doc":"Make connection with MongoDb if there is no connection yet. The connection details come from  control.config.Config.Settings . After a successful connection attempt, the connection handle is stored in the  client and  mongo members of the Mongo object. When a connection handle exists, this method does nothing.",
"func":1
},
{
"ref":"control.mongo.Mongo.disconnect",
"url":7,
"doc":"Disconnect from the MongoDB.",
"func":1
},
{
"ref":"control.mongo.Mongo.checkCollection",
"url":7,
"doc":"Make sure that a collection exists and (optionally) that it is empty. Parameters      table: string The name of the collection. If no such collection exists, it will be created. reset: boolean, optional False If True, and the collection existed before, it will be cleared. Note that the collection will not be deleted, but all its documents will be deleted.",
"func":1
},
{
"ref":"control.mongo.Mongo.getRecord",
"url":7,
"doc":"Get a single document from a collection. Parameters      table: string The name of the collection from which we want to retrieve a single record. criteria: dict A set of criteria to narrow down the search. Usually they will be such that there will be just one document that satisfies them. But if there are more, a single one is chosen, by the mechanics of the built-in MongoDb command  findOne . Returns    -  control.helpers.generic.AttrDict The single document found, or an empty  control.helpers.generic.AttrDict if no document satisfies the criteria.",
"func":1
},
{
"ref":"control.mongo.Mongo.execute",
"url":7,
"doc":"Executes a MongoDb command and returns the result. Parameters      table: string The collection on which to perform the command. command: string The built-in MongoDb command. Note that the Python interface requires you to write camelCase commands with underscores. So the Mongo command  findOne should be passed as  find_one . args: list Any number of additional arguments that the command requires. kwargs: list Any number of additional keyword arguments that the command requires. Returns    - any Whatever the MongoDb command returns. If the command fails, an error message is issued and None is returned.",
"func":1
},
{
"ref":"control.pages",
"url":8,
"doc":""
},
{
"ref":"control.pages.Pages",
"url":8,
"doc":"Making responses that can be displayed as web pages. This class has methods that correspond to routes in the app, for which they get the data (using  control.content.Content ), which gets then wrapped in HTML. It is instantiated by a singleton object. Most methods generate a response that contains the content of a complete page. For those methods we do not document the return value. Some methods return something different. If so, it the return value will be documented. Parameters      Settings:  control.helpers.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Viewers: object Singleton instance of  control.viewers.Viewers . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo . Users: object Singleton instance of  control.users.Users . Content: object Singleton instance of  control.content.Content . Auth: object Singleton instance of  control.auth.Auth . Users: object Singleton instance of  control.users.Users ."
},
{
"ref":"control.pages.Pages.home",
"url":8,
"doc":"The site-wide home page.",
"func":1
},
{
"ref":"control.pages.Pages.about",
"url":8,
"doc":"The site-wide about page.",
"func":1
},
{
"ref":"control.pages.Pages.surprise",
"url":8,
"doc":"The \"surprise me!\" page.",
"func":1
},
{
"ref":"control.pages.Pages.projects",
"url":8,
"doc":"The page with the list of projects.",
"func":1
},
{
"ref":"control.pages.Pages.project",
"url":8,
"doc":"The landing page of a project. Parameters      projectId: ObjectId The project in question.",
"func":1
},
{
"ref":"control.pages.Pages.edition",
"url":8,
"doc":"The landing page of an edition. This page contains a list of scenes. One of these scenes will be loaded in a 3D viewer. It is dependent on defaults which scene in which viewer/version/mode. Parameters      editionId: ObjectId The edition in question. From the edition record we can find the project too.",
"func":1
},
{
"ref":"control.pages.Pages.scene",
"url":8,
"doc":"The landing page of an edition, but with a scene marked as active. This page contains a list of scenes. One of these scenes is chosen as the active scene and will be loaded in a 3D viewer. It is dependent on the parameters and/or defaults in which viewer/version/mode. Parameters      sceneId: ObjectId The active scene in question. From the scene record we can find the edition and the project too. viewer: string or None The viewer to use. version: string or None The version to use. action: string or None The mode in which the viewer is to be used ( view or  edit ).",
"func":1
},
{
"ref":"control.pages.Pages.scenes",
"url":8,
"doc":"Workhorse for  Pages.edition() and  Pages.scene() . The common part between the two functions mentioned.",
"func":1
},
{
"ref":"control.pages.Pages.viewerFrame",
"url":8,
"doc":"The page loaded in an iframe where a 3D viewer operates. Parameters      sceneId: ObjectId The scene that is shown. viewer: string or None The viewer to use. version: string or None The version to use. action: string or None The mode in which the viewer is to be used ( view or  edit ).",
"func":1
},
{
"ref":"control.pages.Pages.viewerResource",
"url":8,
"doc":"Components requested by viewers. This is the javascript code, the css, and other resources that are part of the 3D viewer software. Parameters      path: string Path on the file system under the viewers base directory where the resource resides.",
"func":1
},
{
"ref":"control.pages.Pages.dataProjects",
"url":8,
"doc":"Data content requested by viewers. This is the material belonging to the scene, the scene json itself and additional resources, that are part of the user contributed content that is under control of the viewer: annotations, media, etc. Parameters      projectName: string or None If not None, the name of a project under which the resource is to be found. editionName: string or None If not None, the name of an edition under which the resource is to be found. path: string Path on the file system under the data directory where the resource resides. If there is a project and or edition given, the path is relative to those.",
"func":1
},
{
"ref":"control.pages.Pages.page",
"url":8,
"doc":"Workhorse function to get content on the page. Parameters      url: string Initial part of the url that triggered the page function. This part is used to make one of the tabs on the web page active. projectId: ObjectId, optional None The project in question, if any. Maybe needed for back links to the project. editionId: ObjectId, optional None The edition in question, if any. Maybe needed for back links to the edition. left: string, optional  Content for the left column of the page. right: string, optional  Content for the right column of the page.",
"func":1
},
{
"ref":"control.pages.Pages.authWebdav",
"url":8,
"doc":"Authorises a webdav request. When a viewer makes a WebDAV request to the server, that request is first checked here for authorisation. See  control.webdavapp.dispatchWebdav() . Parameters      projectName: string The project in question. editionName: string The edition in question. path: string The path relative to the directory of the edition. action: string The operation that the WebDAV request wants to do on the data ( view or  edit ). Returns    - boolean Whether the action is permitted on ths data by the current user.",
"func":1
},
{
"ref":"control.pages.Pages.navigation",
"url":8,
"doc":"Generates the navigation controls. Especially the tab bar. Parameters      url: string Initial part of the url on the basis of which one of the tabs can be made active. Returns    - string The HTML of the navigation.",
"func":1
},
{
"ref":"control.pages.Pages.backLink",
"url":8,
"doc":"Makes a link to the landing page of a project. Parameters      projectId: ObjectId The project in question.",
"func":1
},
{
"ref":"control.pages.Pages.putText",
"url":8,
"doc":"Puts a piece of metadata on the web page. The meta data is retrieved and then wrapped accordingly. Parameters      nameSpace: string The namespace of the metadata, e.g.  dc (Dublin Core) fieldPath: string  . -separated list of fields into a metadata structure. level: integer 1-6 The heading level in which the text must be wrapped. projectId: ObjectId or None The project in question editionId: ObjectId or None The edition in question Returns    - string The HTML of the formatted text.",
"func":1
},
{
"ref":"control.pages.Pages.putTexts",
"url":8,
"doc":"Puts a several pieces of metadata on the web page. See  Pages.putText() for the parameter specifications. One difference: Parameters      fieldSpecs: string  , -separated list of fieldSpecs Returns    - string The join of the individual results of  Pages.putText .",
"func":1
},
{
"ref":"control.content",
"url":9,
"doc":""
},
{
"ref":"control.content.Content",
"url":9,
"doc":"Retrieving content from database and file system. This class has methods to retrieve various pieces of content from the data sources, and hand it over to the  control.pages.Pages class that will compose a response out of it. It is instantiated by a singleton object. Parameters      Settings:  control.helpers.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Viewers: object Singleton instance of  control.viewers.Viewers . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo ."
},
{
"ref":"control.content.Content.addAuth",
"url":9,
"doc":"Give this object a handle to the Auth object. Because of cyclic dependencies some objects require to be given a handle to Auth after their initialization.",
"func":1
},
{
"ref":"control.content.Content.getMeta",
"url":9,
"doc":"Retrieve a metadata string. Metadata sits in a big, potentially deeply nested dictionary of keys and values. This function retrieves the information based on a path of keys. Parameters      nameSpace: string The first selector in the metadata, e.g.  dc for Dublin Core. fieldPath: string A  . -separated list of keys. This is a selector in the nested metadata dict selected by the  nameSpace argument. projectId: ObjectId, optional None The project whose metadata we need. If it is None, we need metadata outside all of the projects. editionId: ObjectId, optional None The edition whose metadata we need. If it is None, we need metadata of a project or outer metadata. asMd: boolean, optional False If True, and the resulting metadata is a string, we assume that it is a markdown string, and we convert it to HTML. Returns    - string It is assumed that the metadata that is addressed by the  nameSpace and  fieldPath arguments exists and is a string. If not, we return the empty string.",
"func":1
},
{
"ref":"control.content.Content.getSurprise",
"url":9,
"doc":"Get the data that belongs to the surprise-me functionality.",
"func":1
},
{
"ref":"control.content.Content.getProjects",
"url":9,
"doc":"Get the list of all projects. Well, the list of all projects visible to the current user. Unpublished projects are only visible to users that belong to that project. Visible projects are each displayed by means of an icon and a title. Both link to a landing page for the project. Returns    - string A list of captions of the projects, wrapped in a HTML string.",
"func":1
},
{
"ref":"control.content.Content.getEditions",
"url":9,
"doc":"Get the list of the editions of a project. Well, only if the project is visible to the current user. See  Content.getProjects() . Editions are each displayed by means of an icon and a title. Both link to a landing page for the edition. Parameters      projectId: ObjectId The project in question. Returns    - string A list of captions of the editions of the project, wrapped in a HTML string.",
"func":1
},
{
"ref":"control.content.Content.getScenes",
"url":9,
"doc":"Get the list of the scenes of an edition of a project. Well, only if the project is visible to the current user. See  Content.getProjects() . Scenes are each displayed by means of an icon a title and a row of buttons. The title is the file name (without the  .json extension) of the scene. Both link to a landing page for the edition. One of the scenes is made  active , i.e. it is loaded in a specific version of a viewer in a specific mode ( view or  edit ). Which scene is loaded in which viewer and version in which mode, is determined by the parameters. If the parameters do not specify values, sensible defaults are chosen. Parameters      projectId: ObjectId The project in question. editionId: ObjectId The edition in question. sceneId: ObjectId, optional None The active scene. If None the default scene is chosen. A scene record specifies whether that scene is the default scene for that edition. viewer: string, optional  The viewer to be used for the 3D viewing. It should be a supported viewer. If  , the default viewer is chosen. The list of those viewers is in the  yaml/viewers.yml file, which also specifies what the default viewer is. version: string, optional  The version of the chosen viewer that will be used. If no version or a non-existing version are specified, the latest existing version for that viewer will be chosen. action: string, optional  \"view\" The mode in which the viewer should be opened. If the mode is  edit , the viewer is opened in edit mode. All other modes lead to the viewer being opened in read-only mode. Returns    - string A list of captions of the scenes of the edition, with one caption replaced by a 3D viewer showing the scene. The list is wrapped in a HTML string.",
"func":1
},
{
"ref":"control.content.Content.getCaption",
"url":9,
"doc":"Get a caption for a project, edition, or scene. A caption consists of an icon, and a textual title, both with a hyperlink to the full or active version of the item. Parameters      title: string The textual bit of the caption. candy: dict A dictionary of visual elements to chose from. If one of the elements is called  icon , that will be chosen. url: string The url to link to. iconUrlBase: string The url that almost points to the icon image file, only the selected name from  candy needs to be appended to it. active: boolean, optional False Whether the caption should be displayed as being  active . buttons: string, optional  A set of buttons that should be displayed below the captions. This applies to captions for  scenes : there we want to display buttons to open the scene in a variety of veiwers, versions and modes. frame: string, optional  An iframe to display instead of the visual element of the caption. This applies to scene captions, for the case where we want to show the scene loaded in a viewer. That will be done in an iframe, and this is the HTML for that iframe. Returns    - string The HTML representing the caption.",
"func":1
},
{
"ref":"control.content.Content.getIcon",
"url":9,
"doc":"Select an icon from a set of candidates. Parameters      candy: dict A set of candidates, given as a dict, keyed by file names (without directory information) and valued by a boolean that indicates whether the image may act as an icon. Returns    - string or None The first candidate in candy that is an icon. If there are no candidates that qualify, None is returned.",
"func":1
},
{
"ref":"control.content.Content.getViewerFile",
"url":9,
"doc":"Gets a viewer-related file from the file system. This is about files that are part of the viewer software. The viewer software is located in a specific directory on the server. This is the viewer base. Parameters      path: string The path of the viewer file within viewer base. Returns    - string The contents of the viewer file, if it exists. Otherwise, we raise an error that will lead to a 404 response.",
"func":1
},
{
"ref":"control.content.Content.getData",
"url":9,
"doc":"Gets a data file from the file system. All data files are located under a specific directory on the server. This is the data directory. Below that the files are organized by projects and editions. At least one of the parameters  projectName and  editionName should be present. And if  editionName is present,  projectName should also be present. Parameters      path: string The path of the data file within project/edition directory within the data directory. projectName: string, optional  The name of the project in question. editionName: string, optional  The name of the edition in question. Returns    - string The contents of the data file, if it exists. Otherwise, we raise an error that will lead to a 404 response.",
"func":1
},
{
"ref":"control.content.Content.getRecord",
"url":9,
"doc":"Get a record from MongoDb. This is just a trivial wrapper around a method with the same name  control.mongo.Mongo.getRecord . We have this for reasons of abstraction: the  control.pages.Pages object relies on this Content object to retrieve content, and does not want to know where the content comes from.",
"func":1
},
{
"ref":"control.messages",
"url":10,
"doc":""
},
{
"ref":"control.messages.Messages",
"url":10,
"doc":"Sending messages to the user and the server log. This class is instantiated by a singleton object. It has methods to issue messages to the screen of the webuser and to the log for the sysadmin. They distinguish themselves by the  severity :  debug ,  info ,  warning ,  error . There is also  plain , a leaner variant of  info . All those methods have two optional parameters:  logmsg and  msg . The behaviors of these methods are described in detail in the  Messages.message() function.  ! hint \"What to disclose?\" You can pass both parameters, which gives you the opportunity to make a sensible distinction between what you tell the web user (not much) and what you send to the log (the gory details). When the controllers of the flask app call methods that produce messages for the screen of the webusers, these messages are accumulated, and sent to the web client with the next response. Parameters      Settings:  control.helpers.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings . flask: boolean, optional True If False, mo messages will be sent to the screen of the webuser, instead those messages end up in the log. This is useful in the initial processing that takes place before the flask app is started."
},
{
"ref":"control.messages.Messages.debugAdd",
"url":10,
"doc":"Adds a quick debug method to a destination object. The result of this method is that nstead of saying   self.Messages.debug(logmsg=\"blabla\")   you can say   self.debug(\"blabla\")   It is recommended that in each object where you store a handle to Messages, you issue the statement   Messages.addDebug(self)  ",
"func":1
},
{
"ref":"control.messages.Messages.debug",
"url":10,
"doc":"Issue a debug message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.error",
"url":10,
"doc":"Issue an error message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.warning",
"url":10,
"doc":"Issue a warning message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.info",
"url":10,
"doc":"Issue a informational message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.plain",
"url":10,
"doc":"Issue a informational message, without bells and whistles. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.message",
"url":10,
"doc":"Workhorse to issue a message in a variety of ways. It can issue log messages and screen messages. Parameters      tp: string The severity of the message. There is a fixed number of types:   debug Messages are prepended with  DEBUG:  . Log messages go to stderr. Messages will only show up on the web page if the app runs in debug mode.   plain Messages are not prepended with anything. Log messages go to standard output.   info Messages are prepended with  INFO:  . Log messages go to standard output.   warning Messages are prepended with  WARNING:  . Log messages go to standard error.   error Messages are prepended with  ERROR:  . Log messages go to standard error. It also raises an exception, which will lead to a 404 response (if flask is running, that is). msg: string, optional None If not None, it is the contents of a screen message. logmsg: string, optional None If not None, it is the contents of a log message.",
"func":1
},
{
"ref":"control.messages.Messages.clearMessages",
"url":10,
"doc":"Clears the accumulated messages.",
"func":1
},
{
"ref":"control.messages.Messages.generateMessages",
"url":10,
"doc":"Wrap the accumulates messages into html. They are ready to be included in a response. The list of accumulated messages will be cleared afterwards.",
"func":1
},
{
"ref":"control.app",
"url":11,
"doc":""
},
{
"ref":"control.app.appFactory",
"url":11,
"doc":"Sets up the main flask app. The main task here is to configure routes, i.e. mappings from url-patterns to functions that create responses  ! note \"WebDAV enabling\" This flask app will later be combined with a webdav app, so that the combined app has the business logic of the main app but can also handle webdav requests. The routes below contain a few patterns that are used for authorising WebDAV calls: the onses starting with  /auth and  /no . See also  control.webdavapp . Parameters      objects:  control.helpers.generic.AttrDict a slew of objects that set up the toolkit with which the app works: settings, messaging and logging, MongoDb connection, 3d viewer support, higher level objects that can fetch chunks of content and distribute it over the web page. Returns    - object A WebDAV-enabled flask app, which is a wsgi app.",
"func":1
},
{
"ref":"control.viewers",
"url":12,
"doc":""
},
{
"ref":"control.viewers.Viewers",
"url":12,
"doc":"Knowledge of the installed 3D viewers. This class knows which (versions of) viewers are installed, and has the methods to invoke them. It is instantiated by a singleton object. Parameters      Settings:  control.helpers.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings ."
},
{
"ref":"control.viewers.Viewers.addAuth",
"url":12,
"doc":"Give this object a handle to the Auth object. The Viewers and Auth objects need each other, so one of them must be given the handle to the other after initialization.",
"func":1
},
{
"ref":"control.viewers.Viewers.check",
"url":12,
"doc":"Checks whether a viewer version exists. Given a viewer and a version, it is looked up whether the code is present. If not, reasonable defaults are returned instead. Parameters      viewer: string The viewer in question. version: string The version of the viewer in question. Returns    - tuple The viewer and version are returned unmodified if that viewer version is supported. If the viewer is supported, but not the version, the latest supported version of that viewer is taken. If the viewer is not supported, the default viewer is taken.",
"func":1
},
{
"ref":"control.viewers.Viewers.getButtons",
"url":12,
"doc":"Produces a set of buttons to launch 3D viewers for a scene. Parameters      sceneId: ObjectId The scene in question. actions: iterable of string The actions for which we have to create buttons. Typically  view and possibly also  edit . isSceneActive: boolean Whether this scene is active, i.e. loaded in a 3D viewer. viewerActive: string or None The viewer in which the scene is currently loaded, if any, otherwise None versionActive: string or None The version of the viewer in which the scene is currently loaded, if any, otherwise None actionActive: string or None The mode in which the scene is currently loaded in the viewer ( view or  edit ), if any, otherwise None Returns    - string The HTML that represents the buttons.",
"func":1
},
{
"ref":"control.viewers.Viewers.genHtml",
"url":12,
"doc":"Generates the HTML for the viewer page that is loaded in an iframe. When a scene is loaded in a viewer, it happens in an iframe. Here we generate the complete HTML for such an iframe. Parameters      urlBase: string The first part of the root url that is given to the viewer. The viewer code uses this to retrieve additional information. The root url will be completed with the  action and the  viewer . sceneName: string The name of the scene in the file system. The viewer will find the scene json file by this name. viewer: string The chosen viewer. version: string The chosen version of the viewer. action: string The chosen mode in which the viewer is launched ( view or  edit ). Returns    - string The HTML for the iframe.",
"func":1
},
{
"ref":"control.viewers.Viewers.getRoot",
"url":12,
"doc":"Composes the root url for a viewer. Parameters      urlBase: string The first part of the root url, depending on the project and edition. action: string The mode in which the viewer is opened. Depending on the mode, the viewer code may communicate with the server with different urls. For example, for the voyager, the  view mode (voyager-explorer) uses ordinary HTTP requests, but the  edit mode (voyager-story) uses WebDAV requests. So this app points voyager-explorer to a root url starting with  /data , and voyager-story to a root url starting with  /webdav . These prefixes of the urls can be configured per viewer in the viewer configuration in  yaml/viewers.yml .",
"func":1
},
{
"ref":"control.helpers",
"url":13,
"doc":""
},
{
"ref":"control.helpers.files",
"url":14,
"doc":""
},
{
"ref":"control.helpers.files.readPath",
"url":14,
"doc":"Reads the (textual) contents of a file.  ! note \"Not for binary files\" The file will not be opened in binary mode. Use this only for files with textual content. Parameters      filePath: string The path of the file on the file system. Returns    - string The contents of the file as unicode. If the file does not exist, the empty string is returned.",
"func":1
},
{
"ref":"control.helpers.files.readYaml",
"url":14,
"doc":"Reads a yaml file. Parameters      filePath: string The path of the file on the file system. defaultEmpty: boolean, optional False What to do if the file does not exist. If True, it returns an empty  control.helpers.generic.AttrDict otherwise False. Returns    -  control.helpers.generic.AttrDict or None The data content of the yaml file if it exists.",
"func":1
},
{
"ref":"control.helpers.files.fileExists",
"url":14,
"doc":"Whether a path exists as file on the file system.",
"func":1
},
{
"ref":"control.helpers.files.dirExists",
"url":14,
"doc":"Whether a path exists as directory on the file system.",
"func":1
},
{
"ref":"control.helpers.files.listFiles",
"url":14,
"doc":"The list of all files in a directory with a certain extension. If the directory does not exist, the empty list is returned.",
"func":1
},
{
"ref":"control.helpers.files.listImages",
"url":14,
"doc":"The list of all image files in a directory. If the directory does not exist, the empty list is returned. An image is a file with extension .png, .jpg, .jpeg or any of its case variants.",
"func":1
},
{
"ref":"control.helpers.generic",
"url":15,
"doc":""
},
{
"ref":"control.helpers.generic.htmlEsc",
"url":15,
"doc":"Escape certain HTML characters by HTML entities. To prevent them to be interpreted as HTML in cases where you need them literally.",
"func":1
},
{
"ref":"control.helpers.generic.AttrDict",
"url":15,
"doc":"Turn a dict into an object with attributes. If non-existing attributes are accessed for reading,  None is returned. See: https: stackoverflow.com/questions/4984647/accessing-dict-keys-like-an-attribute And: https: stackoverflow.com/questions/16237659/python-how-to-implement-getattr (especially the remark that >  __getattr__ is only used for missing attribute lookup )"
},
{
"ref":"control.prepare",
"url":16,
"doc":""
},
{
"ref":"control.prepare.prepare",
"url":16,
"doc":"Prepares the way for setting up the Flask webapp. Several classes are instantiated with a singleton object; each of these objects has a dedicated task in the app:   control.config.Config.Settings : all configuration aspects   control.messages.Messages : handle all messaging to user and sysadmin   control.mongo.Mongo : higher-level commands to the MongoDb   control.viewers.Viewers : support the third party 3D viewers   control.users.Users : manage the user data that the app needs   control.content.Content : retrieve all data that needs to be displayed   control.auth.Auth : compute the permission of the current user to access content   control.pages.Pages : high-level functions that distribute content over the page  ! note \"Should be run once!\" These objects are used in several web apps:  the main web app  a copy of the main app that is enriched with the webdav functionality However, these objects should be initialized once, before either app starts, and the same objects should be passed to both invocations of the factory functions that make them ( control.app.appFactory ). The invocations are done in  control.webdavapp.appFactory . Parameters      trivial: boolean, optional False If True, skips the initialization of most objects. Useful if the pure3d app container should run without doing anything. This happens when we just want to start the container and run shell commands inside it, for example after a complicated refactoring when the flask app has too many bugs. flask: boolean, optional True If False, skips several configuration steps. Useful if you need configuration details of the app before flask is running. Cases are:  when setting up the webdav app ( control.webdavapp ) you need some configuration details, and this happens before the flask app is set up  when importing data into MongoDb, we need only non-flask parts of the app. This kind of import happens manually in a running container on the command line. Returns    -  control.helpers.generic.AttrDict A dictionary keyed by the names of the singleton objects and valued by the singleton objects themselves.",
"func":1
}
]