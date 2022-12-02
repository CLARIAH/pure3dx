URLS=[
"control/index.html",
"control/webdavapp.html",
"control/auth.html",
"control/users.html",
"control/files.html",
"control/collect.html",
"control/editsessions.html",
"control/config.html",
"control/mongo.html",
"control/flask.html",
"control/generic.html",
"control/html.html",
"control/datamodel.html",
"control/authoidc.html",
"control/pages.html",
"control/content.html",
"control/messages.html",
"control/environment.html",
"control/app.html",
"control/viewers.html",
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
"doc":"Combines the main app with the webdavapp. A WSGI app is essentially a function that takes a request environment and a start-response function and produces a response. We combine two wsgi apps by defining a new WSGI function out of the WSGI functions of the component apps. We call this function the dispatcher. The combined function works so that requests with urls starting with a certain prefix are dispatched to the webdav app, while all other requests are handled by the main app. However, we must do proper authorisation for the calls that are sent to the webdav app. But the business-logic for authorisation is in the main app, while we want to leave the code of the webdav app untouched. We solve this by making the dispatcher so that it feeds every WebDAV request to the main app first. We mark those requests by prepending  /auth in front of the original url. The main app is programmed to react to such requests by returning a boolean to the dispatcher, instead of sending a response to the client. See  control.pages.Pages.authWebdav . The dispatcher interprets this boolean as telling whether the request is authorized. If so, it sends the original request to the webdav app. If not, it prepends  /cannot to the original url and sends the request to the main app, which is programmed to respond with a 404 to such requests. Parameters      app: object The original flask app. webdavPrefix: string Initial part of the url that is used as trigger to divert to the WEBDav app. webdavApp: A WEBDav server.",
"func":1
},
{
"ref":"control.webdavapp.appFactoryMaster",
"url":1,
"doc":"",
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
"doc":"All about authorised data access. This class knows users because it is based on the Users class. This class also knows content, and decides whether the current user is authorised to perform certain actions on content in question. It is instantiated by a singleton object. Parameters      Settings:  control.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo . Content: object Singleton instance of  control.content.Content ."
},
{
"ref":"control.auth.Auth.authorise",
"url":2,
"doc":"Gather the access conditions for the relevant record or table. Parameters      table: string, optional None the table that is being used recordId: ObjectId The id of the record that is being accessed, if any. projectId: ObjectId Only relevant if recordId is None. If passed, the new record to be created will belong to this project action: string, optional None If None, returns all permitted actions on the record in question, otherwise whether the indicated action is permitted. If recordId is None, it is assumed that the action is  create , and a boolean is returned. Returns    - set | boolean If  recordId is None: whether the user is allowed to insert a new record in  table . Otherwise: if  action is passed: whether the user is allowed to perform that action on the record in question. Otherwise: the set of actions that the user may perform on this record.",
"func":1
},
{
"ref":"control.auth.Auth.makeSafe",
"url":2,
"doc":"Changes an action into an allowed action if needed. This function 'demotes' an action to an allowed action if the action itself is not allowed. In practice, if the action is  update or  delete , but that is not allowed, it is changed into  read . If  read itself is not allowed, None is returned. Parameters      table: string The table in which the record exists. recordId: ObjectId The id of the record. action: string An intended action. Returns    - string or None The resulting safe action.",
"func":1
},
{
"ref":"control.auth.Auth.addAuthenticator",
"url":3,
"doc":"Adds the object that gives access to authentication methods. Parameters      oidc: object The object corresponding to the flask app prepared with the Flask-OIDC authenticator. Returns    - void The object is stored in the  oidc member.",
"func":1
},
{
"ref":"control.auth.Auth.login",
"url":3,
"doc":"Log in a user. Logging in has several main steps: 1. redirecting to a private page, for which login is required 2. obtaining the authentication results when the user visits that page 3. storing the relevant user data When we log in test users, we can skip the first step, because we already know everything about the test user on the basis of the information in the request that brought us here. So, we find out if we have to log in a test user or a user that must be authenticated through oidc. We only log in a test user if we are in test mode and the user's sub is passed in the request. Returns    - response A redirect. When logging in in test mode, the redirect is to  referrer (the url we came from). Otherwise it is to a url that triggers an oidc login procedure. To that page we pass the referrer as part of the url, so that after login the user can be redirected to the original referrer.",
"func":1
},
{
"ref":"control.auth.Auth.afterLogin",
"url":3,
"doc":"Logs in a user. When this function starts operating, the user has been through the login process provided by the authentication service. We can now find the user's sub and additional attributes in the request context. We use that information to lookup the user in the MongoDb users table. If the user does not exists, we add a new user record, with this sub and these attributes, and role  user . If the user does exists, we check whether we have to update his attributes. If the attributes found in MongoDb differ from those supplied by the authentication service, we update the MongoDb values on the basis of the provider values. Parameters      referrer: string url where we came from. Returns    - response A redirect to the referrer, with a status 302 if the log in was successful or 303 if not.",
"func":1
},
{
"ref":"control.auth.Auth.logout",
"url":3,
"doc":"Logs off the current user. First we find out whether we have to log out a test user or a normal user. After logging out, we redirect to the home page. Returns    - response A redirect to the home page.",
"func":1
},
{
"ref":"control.auth.Auth.identify",
"url":3,
"doc":"Make sure who is the current user. Checks whether there is a current user and whether that user is fully known, i.e. in the users collection of the mongoDb. If there is a current user that is unknown to the database, the current user will be cleared. Otherwise, we make sure that we retrieve the current user's attributes from the database.  ! note \"No login\" We do not try to perform a login of a user, we only check who is the currently logged in user. A login must be explicitly triggered by the the  /login url.",
"func":1
},
{
"ref":"control.auth.Auth.myDetails",
"url":3,
"doc":"Who is the currently authenticated user? The  __User member is inspected: does it contain an sub? If so, that is taken as proof that we have a valid user. Returns    - dict Otherwise a copy of the complete __User record is returned. unless there is no  sub member in the current user, then the empty dictionary is returned.",
"func":1
},
{
"ref":"control.auth.Auth.getUser",
"url":3,
"doc":"Obtain the sub of the currently logged in user from the request info. It works for test users and normal users. Parameters      fromArg: boolean, optional False If True, the test user is not read from the session, but from a request argument. This is used during the login procedure of test users. Returns    - boolean, boolean, string Whether we are in test mode. Whether the user is a test user. The sub of the user",
"func":1
},
{
"ref":"control.auth.Auth.wrapLogin",
"url":3,
"doc":"Generate HTML for the login widget. De task is to generate login/logout buttons. If the user is logged in, his nickname should be displayed, together with a logout button. If no user is logged in, a login button should be displayed. If in test mode, a list of buttons for each test-user should be displayed. Returns    - string HTML of the list of buttons for test users, with the button for the current user styled as active.",
"func":1
},
{
"ref":"control.auth.Auth.presentRole",
"url":3,
"doc":"Finds the interface representation of a role. Parameters      role: string The internal name of the role. Returns    - string The name of the role as it should be presented to users. If no representation can be found, the internal name is returned.",
"func":1
},
{
"ref":"control.auth.Auth.oidc",
"url":3,
"doc":"The object that gives access to authentication methods."
},
{
"ref":"control.files",
"url":4,
"doc":""
},
{
"ref":"control.files.readPath",
"url":4,
"doc":"Reads the (textual) contents of a file.  ! note \"Not for binary files\" The file will not be opened in binary mode. Use this only for files with textual content. Parameters      filePath: string The path of the file on the file system. Returns    - string The contents of the file as unicode. If the file does not exist, the empty string is returned.",
"func":1
},
{
"ref":"control.files.readYaml",
"url":4,
"doc":"Reads a yaml file. Parameters      filePath: string The path of the file on the file system. defaultEmpty: boolean, optional False What to do if the file does not exist. If True, it returns an empty  control.generic.AttrDict otherwise False. Returns    -  control.generic.AttrDict or None The data content of the yaml file if it exists.",
"func":1
},
{
"ref":"control.files.fileExists",
"url":4,
"doc":"Whether a path exists as file on the file system.",
"func":1
},
{
"ref":"control.files.fileRemove",
"url":4,
"doc":"Removes a file if it exists as file.",
"func":1
},
{
"ref":"control.files.fileCopy",
"url":4,
"doc":"Copies a file if it exists as file. Wipes the destination file, if it exists.",
"func":1
},
{
"ref":"control.files.dirExists",
"url":4,
"doc":"Whether a path exists as directory on the file system.",
"func":1
},
{
"ref":"control.files.dirRemove",
"url":4,
"doc":"Removes a directory if it exists as directory.",
"func":1
},
{
"ref":"control.files.dirCopy",
"url":4,
"doc":"Copies a directory if it exists as directory. Wipes the destination directory, if it exists.",
"func":1
},
{
"ref":"control.files.dirMake",
"url":4,
"doc":"Creates a directory if it does not already exist as directory.",
"func":1
},
{
"ref":"control.files.listDirs",
"url":4,
"doc":"The list of all subdirectories in a directory. If the directory does not exist, the empty list is returned.",
"func":1
},
{
"ref":"control.files.listFiles",
"url":4,
"doc":"The list of all files in a directory with a certain extension. If the directory does not exist, the empty list is returned.",
"func":1
},
{
"ref":"control.files.listImages",
"url":4,
"doc":"The list of all image files in a directory. If the directory does not exist, the empty list is returned. An image is a file with extension .png, .jpg, .jpeg or any of its case variants.",
"func":1
},
{
"ref":"control.files.list3d",
"url":4,
"doc":"The list of all 3D files in a directory. If the directory does not exist, the empty list is returned. An image is a file with extension .gltf, .glb or any of its case variants.",
"func":1
},
{
"ref":"control.files.get3d",
"url":4,
"doc":"Detect 3D files in a certain directory. The directory is searched for files that have an extension that signals 3D data. Optionally we restrict the search for files with a given base name. Parameters      path: string Directory in which the 3D files are looked up. name: string, optionally None If None, all files will be searched. Otherwise this is the base name of the 3D files that we look for. Returns    - dict Keyed by base name, valued by extensions of existing 3D files in that directory.",
"func":1
},
{
"ref":"control.collect",
"url":5,
"doc":""
},
{
"ref":"control.collect.Collect",
"url":5,
"doc":"Provides initial data collection into MongoDb. Normally, this does not have to run, since the MongoDb is persistent. Only when the MongoDb of the Pure3D app is fresh, or when the MongoDb is out of sync with the data on the filesystem it must be initialized. It reads:  configuration data of the app,  project data on the file system  workflow data on the file system  3D-viewer code on file system The project-, workflow, and viewer data should be placed on the same share in the file system, by a provision step that is done on the host. The data for the supported viewers is in repo  pure3d-data , under  viewers . For testing, there is  exampledata in the same  pure3d-data repo. The provision step should copy the contents of  exampledata to the  data directory of this repo ( pure3dx ). If data collection is triggered in test mode, the user table will be wiped, and the test users present in the example data will be imported. Otherwise the user table will be left unchanged. Parameters      Settings:  control.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo ."
},
{
"ref":"control.collect.Collect.trigger",
"url":5,
"doc":"Determines whether data collection should be done. We only do data collection if the environment variable  docollect is  v If so, the value of the environment variable  initdata is the name of a subdirectory of the data directory. This subdirectory contains example data that will be imported into the system. We also prevent this from happening twice, which occurs when Flask runs in debug mode, since then the code is loaded twice. We guard against this by inspecting the environment variable  WERKZEUG_RUN_MAIN . If it is set, we are already running the app, and data collection should be inhibited, because it has been done just before Flask started running.",
"func":1
},
{
"ref":"control.collect.Collect.fetch",
"url":5,
"doc":"Performs a data collection.",
"func":1
},
{
"ref":"control.collect.Collect.clearDb",
"url":5,
"doc":"Clears selected collections in the MongoDb. All collections that will be filled with data from the filesystem will be wiped.  ! \"Users collection will be wiped in test mode\" If in test mode, the  users collection will be wiped, and then filled from the example data.",
"func":1
},
{
"ref":"control.collect.Collect.doOuter",
"url":5,
"doc":"Collects data not belonging to specific projects.",
"func":1
},
{
"ref":"control.collect.Collect.doProjects",
"url":5,
"doc":"Collects data belonging to projects.",
"func":1
},
{
"ref":"control.collect.Collect.doProject",
"url":5,
"doc":"Collects data belonging to a specific project. Parameters      projectsInPath: string Path on the filesystem to the projects input directory projectsOutPath: string Path on the filesystem to the projects destination directory projectName: string Directory name of the project to collect.",
"func":1
},
{
"ref":"control.collect.Collect.doEditions",
"url":5,
"doc":"Collects data belonging to the editions of a project. Parameters      projectInPath: string Path on the filesystem to the input directory of this project projectOutPath: string Path on the filesystem to the destination directory of this project projectId: ObjectId MongoId of the project to collect.",
"func":1
},
{
"ref":"control.collect.Collect.doEdition",
"url":5,
"doc":"Collects data belonging to a specific edition. Parameters      projectId: ObjectId MongoId of the project to which the edition belongs. editionsInPath: string Path on the filesystem to the editions input directory within this project. editionsOutPath: string Path on the filesystem to the editions working directory within this project. editionName: string Directory name of the edition to collect.",
"func":1
},
{
"ref":"control.collect.Collect.doScenes",
"url":5,
"doc":"Collects data belonging to the scenes of an edition. Parameters      editionInPath: string Path on the filesystem to the input directory of this edition editionOutPath: string Path on the filesystem to the destination directory of this edition projectId: ObjectId MongoId of the project to collect. editionId: ObjectId MongoId of the edition to collect.",
"func":1
},
{
"ref":"control.collect.Collect.doWorkflow",
"url":5,
"doc":"Collects workflow information from yaml files.  ! note \"Test users\" This includes test users when in test mode.",
"func":1
},
{
"ref":"control.editsessions",
"url":6,
"doc":""
},
{
"ref":"control.editsessions.EditSessions",
"url":6,
"doc":"Managing edit sessions of users. This class has methods to create and delete edit sessions for users, which guard them from overwriting each other's data. Edit sessions prevent users from editing the same piece of content, in particular it prevents multiple  edit -mode 3D viewers being active with the same scene. It is instantiated by a singleton object. Parameters      Mongo: object Singleton instance of  control.mongo.Mongo ."
},
{
"ref":"control.config",
"url":7,
"doc":""
},
{
"ref":"control.config.Config",
"url":7,
"doc":"All configuration details of the app. It is instantiated by a singleton object. Settings will be collected from the environment:  yaml files  environment variables  files and directories (for supported viewer software)  ! note \"Missing information\" If essential information is missing, the flask app will not be started, and no webserving will take place. Parameters      Messages: object Singleton instance of  control.messages.Messages ."
},
{
"ref":"control.config.Config.checkEnv",
"url":7,
"doc":"Collect the relevant information. If essential information is missing, processing stops. This is done by setting the  good member of Config to False.",
"func":1
},
{
"ref":"control.config.Config.checkRepo",
"url":7,
"doc":"Get the location of the pure3dx repository on the file system.",
"func":1
},
{
"ref":"control.config.Config.checkWebdav",
"url":7,
"doc":"Read the WEBDav methods from the webdav.yaml file. The methods are associated with the  view or  edit keyword, depending on whether they are  GET like or  PUT like.",
"func":1
},
{
"ref":"control.config.Config.checkVersion",
"url":7,
"doc":"Get the current version of the pure3d app. We represent the version as the short hash of the current commit of the git repo that the running code is in.",
"func":1
},
{
"ref":"control.config.Config.checkSecret",
"url":7,
"doc":"Obtain a secret. This is secret information used for encrypting sessions. It resides somewhere on the file system, outside the pure3d repository.",
"func":1
},
{
"ref":"control.config.Config.checkData",
"url":7,
"doc":"Get the location of the project data on the file system.",
"func":1
},
{
"ref":"control.config.Config.checkModes",
"url":7,
"doc":"Determine whether flask is running in test/debug or production mode.",
"func":1
},
{
"ref":"control.config.Config.checkMongo",
"url":7,
"doc":"Obtain the connection details for MongDB. It is not checked whether connection with MongoDb actually works with these credentials.",
"func":1
},
{
"ref":"control.config.Config.checkSettings",
"url":7,
"doc":"Read the yaml file with application settings.",
"func":1
},
{
"ref":"control.config.Config.checkDatamodel",
"url":7,
"doc":"Read the yaml file with table and field settings. It contains model  master that contains the master tables with the information which tables are details of it. It also contains  link that contains the link tables with the information which tables are being linked. Both elements are needed when we delete records. If a user deletes a master record, its detail records become invalid. So either we must enforce that the user deletes the details first, or the system must delete those records automatically. When a user deletes a record that is linked to another record by means of a coupling record, the coupling record must be deleted automatically. Fields are bits of data that are stored in parts of documents in MongoDb collections. Fields have several properties which we summarize under a key. So if we know the key of a field, we have access to all of its properties. The properties  nameSpave and  fieldPath determine how to drill down in a document in order to find the value of that field. The property  tp is the data type of the field, default  string . The property  caption is a label that may accompany a field value on the interface.",
"func":1
},
{
"ref":"control.config.Config.checkAuth",
"url":7,
"doc":"Read the yaml file with the authorisation rules.",
"func":1
},
{
"ref":"control.config.Config.checkViewers",
"url":7,
"doc":"Make an inventory of the supported 3D viewers.",
"func":1
},
{
"ref":"control.config.Config.checkBanner",
"url":7,
"doc":"Sets a banner for all pages. This banner may include warnings that the site is still work in progress. Returns    - void The banner is stored in the  banner member of the  Settings object.",
"func":1
},
{
"ref":"control.config.Config.Settings",
"url":7,
"doc":"The actual configuration settings are stored here."
},
{
"ref":"control.users",
"url":3,
"doc":""
},
{
"ref":"control.users.Users",
"url":3,
"doc":"All about users and the current user. This class has methods to login/logout a user, to retrieve the data of the currently logged in user, and to query the users table in MongoDb. It is instantiated by a singleton object. This object has a member  __User that contains the data of the current user if there is a current user. Parameters      Settings:  control.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo ."
},
{
"ref":"control.users.Users.addAuthenticator",
"url":3,
"doc":"Adds the object that gives access to authentication methods. Parameters      oidc: object The object corresponding to the flask app prepared with the Flask-OIDC authenticator. Returns    - void The object is stored in the  oidc member.",
"func":1
},
{
"ref":"control.users.Users.login",
"url":3,
"doc":"Log in a user. Logging in has several main steps: 1. redirecting to a private page, for which login is required 2. obtaining the authentication results when the user visits that page 3. storing the relevant user data When we log in test users, we can skip the first step, because we already know everything about the test user on the basis of the information in the request that brought us here. So, we find out if we have to log in a test user or a user that must be authenticated through oidc. We only log in a test user if we are in test mode and the user's sub is passed in the request. Returns    - response A redirect. When logging in in test mode, the redirect is to  referrer (the url we came from). Otherwise it is to a url that triggers an oidc login procedure. To that page we pass the referrer as part of the url, so that after login the user can be redirected to the original referrer.",
"func":1
},
{
"ref":"control.users.Users.afterLogin",
"url":3,
"doc":"Logs in a user. When this function starts operating, the user has been through the login process provided by the authentication service. We can now find the user's sub and additional attributes in the request context. We use that information to lookup the user in the MongoDb users table. If the user does not exists, we add a new user record, with this sub and these attributes, and role  user . If the user does exists, we check whether we have to update his attributes. If the attributes found in MongoDb differ from those supplied by the authentication service, we update the MongoDb values on the basis of the provider values. Parameters      referrer: string url where we came from. Returns    - response A redirect to the referrer, with a status 302 if the log in was successful or 303 if not.",
"func":1
},
{
"ref":"control.users.Users.logout",
"url":3,
"doc":"Logs off the current user. First we find out whether we have to log out a test user or a normal user. After logging out, we redirect to the home page. Returns    - response A redirect to the home page.",
"func":1
},
{
"ref":"control.users.Users.identify",
"url":3,
"doc":"Make sure who is the current user. Checks whether there is a current user and whether that user is fully known, i.e. in the users collection of the mongoDb. If there is a current user that is unknown to the database, the current user will be cleared. Otherwise, we make sure that we retrieve the current user's attributes from the database.  ! note \"No login\" We do not try to perform a login of a user, we only check who is the currently logged in user. A login must be explicitly triggered by the the  /login url.",
"func":1
},
{
"ref":"control.users.Users.myDetails",
"url":3,
"doc":"Who is the currently authenticated user? The  __User member is inspected: does it contain an sub? If so, that is taken as proof that we have a valid user. Returns    - dict Otherwise a copy of the complete __User record is returned. unless there is no  sub member in the current user, then the empty dictionary is returned.",
"func":1
},
{
"ref":"control.users.Users.getUser",
"url":3,
"doc":"Obtain the sub of the currently logged in user from the request info. It works for test users and normal users. Parameters      fromArg: boolean, optional False If True, the test user is not read from the session, but from a request argument. This is used during the login procedure of test users. Returns    - boolean, boolean, string Whether we are in test mode. Whether the user is a test user. The sub of the user",
"func":1
},
{
"ref":"control.users.Users.wrapLogin",
"url":3,
"doc":"Generate HTML for the login widget. De task is to generate login/logout buttons. If the user is logged in, his nickname should be displayed, together with a logout button. If no user is logged in, a login button should be displayed. If in test mode, a list of buttons for each test-user should be displayed. Returns    - string HTML of the list of buttons for test users, with the button for the current user styled as active.",
"func":1
},
{
"ref":"control.users.Users.presentRole",
"url":3,
"doc":"Finds the interface representation of a role. Parameters      role: string The internal name of the role. Returns    - string The name of the role as it should be presented to users. If no representation can be found, the internal name is returned.",
"func":1
},
{
"ref":"control.users.Users.oidc",
"url":3,
"doc":"The object that gives access to authentication methods."
},
{
"ref":"control.mongo",
"url":8,
"doc":""
},
{
"ref":"control.mongo.Mongo",
"url":8,
"doc":"CRUD interface to content in the MongoDb database. This class has methods to connect to a MongoDb database, to query its data, to create, update and delete data. It is instantiated by a singleton object.  ! note \"string versus ObjectId\" Some functions execute MongoDb statements, based on parameters whose values are MongoDb identifiers. These should be objects in the class  bson.objectid.ObjectId . However, in many cases these ids enter the app as strings. In this module, such strings will be cast to proper ObjectIds, provided they are recognizable as values in a field whose name is  _id or ends with  Id . Parameters      Settings:  control.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages ."
},
{
"ref":"control.mongo.Mongo.cast",
"url":8,
"doc":"Try to cast the value as an ObjectId. Paramaters      value:string The value to cast, normally a string representation of a BSON ObjectId. Returns    - ObjectId | None The corresponding BSON ObjectId if the input is a valid representation of such an id, otherwise  None .",
"func":1
},
{
"ref":"control.mongo.Mongo.connect",
"url":8,
"doc":"Make connection with MongoDb if there is no connection yet. The connection details come from  control.config.Config.Settings . After a successful connection attempt, the connection handle is stored in the  client and  mongo members of the Mongo object. When a connection handle exists, this method does nothing.",
"func":1
},
{
"ref":"control.mongo.Mongo.disconnect",
"url":8,
"doc":"Disconnect from the MongoDB.",
"func":1
},
{
"ref":"control.mongo.Mongo.checkCollection",
"url":8,
"doc":"Make sure that a collection exists and (optionally) that it is empty. Parameters      table: string The name of the collection. If no such collection exists, it will be created. reset: boolean, optional False If True, and the collection existed before, it will be cleared. Note that the collection will not be deleted, but all its documents will be deleted.",
"func":1
},
{
"ref":"control.mongo.Mongo.getRecord",
"url":8,
"doc":"Get a single document from a collection. Parameters      table: string The name of the collection from which we want to retrieve a single record. warn: boolean, optional True If True, warn if there is no record satisfying the criteria. criteria: dict A set of criteria to narrow down the search. Usually they will be such that there will be just one document that satisfies them. But if there are more, a single one is chosen, by the mechanics of the built-in MongoDb command  findOne . Returns    -  control.generic.AttrDict The single document found, or an empty  control.generic.AttrDict if no document satisfies the criteria.",
"func":1
},
{
"ref":"control.mongo.Mongo.getList",
"url":8,
"doc":"Get a list of documents from a collection. Parameters      table: string The name of the collection from which we want to retrieve records. criteria: dict A set of criteria to narrow down the search. Returns    - list of  control.generic.AttrDict The list of documents found, empty if no documents are found. Each document is cast to an AttrDict.",
"func":1
},
{
"ref":"control.mongo.Mongo.updateRecord",
"url":8,
"doc":"Updates a single document from a collection. Parameters      table: string The name of the collection in which we want to update a single record. updates: dict The fields that must be updated with the values they must get warn: boolean, optional True If True, warn if there is no record satisfying the criteria. criteria: dict A set of criteria to narrow down the selection. Usually they will be such that there will be just one document that satisfies them. But if there are more, a single one is chosen, by the mechanics of the built-in MongoDb command  updateOne . Returns    - boolean Whether the update was successful",
"func":1
},
{
"ref":"control.mongo.Mongo.insertRecord",
"url":8,
"doc":"Inserts a new record in a table. Parameters      table: string The table in which the record will be inserted.  fields: dict The field names and their contents to populate the new record with. Returns    - ObjectId The id of the newly inserted record, or None if the record could not be inserted.",
"func":1
},
{
"ref":"control.mongo.Mongo.execute",
"url":8,
"doc":"Executes a MongoDb command and returns the result. Parameters      table: string The collection on which to perform the command. command: string The built-in MongoDb command. Note that the Python interface requires you to write camelCase commands with underscores. So the Mongo command  findOne should be passed as  find_one . args: list Any number of additional arguments that the command requires. kwargs: list Any number of additional keyword arguments that the command requires. Returns    - any Whatever the MongoDb command returns. If the command fails, an error message is issued and None is returned.",
"func":1
},
{
"ref":"control.flask",
"url":9,
"doc":""
},
{
"ref":"control.flask.initializing",
"url":9,
"doc":"Whether the flask web app is already running. It is False during the initialization code in the app factory before the flask app is delivered.",
"func":1
},
{
"ref":"control.flask.make",
"url":9,
"doc":"Create the Flask app.",
"func":1
},
{
"ref":"control.flask.template",
"url":9,
"doc":"Renders a template. Parameters      template: string The name of the template, without extension. kwargs: dict The variables with values to fill in into the template. Returns    - object The response with as content the filled template.",
"func":1
},
{
"ref":"control.flask.flashMsg",
"url":9,
"doc":"",
"func":1
},
{
"ref":"control.flask.response",
"url":9,
"doc":"Wrap data in a response. Parameters      data: any The data to be transferred in an HTTP response. Returns    - object The HTTP response",
"func":1
},
{
"ref":"control.flask.send",
"url":9,
"doc":"Send a file as a response. It is assumed that  path exists as a readable file on the file system. The function will add headers based on the file extension. Parameters      path: string The file to be transferred in an HTTP response. Returns    - object The HTTP response",
"func":1
},
{
"ref":"control.flask.redirectStatus",
"url":9,
"doc":"Redirect. Parameters      url: string The url to redirect to good: Whether the redirection corresponds to a normal scenario or is the result of an error Returns    - response A redirect response with either code 302 (good) or 303 (bad)",
"func":1
},
{
"ref":"control.flask.stop",
"url":9,
"doc":"Stop the request with a 404.",
"func":1
},
{
"ref":"control.flask.sessionPop",
"url":9,
"doc":"Pops a variable from the session. Parameters      name: string The name of the variable. Returns    - void",
"func":1
},
{
"ref":"control.flask.sessionGet",
"url":9,
"doc":"Gets a variable from the session. Parameters      name: string The name of the variable. Returns    - string or None The value of the variable, if it exists, else None.",
"func":1
},
{
"ref":"control.flask.sessionSet",
"url":9,
"doc":"Sets a session variable to a value. Parameters      name: string The name of the variable. value: string The value that will be assigned to the variable Returns    - void",
"func":1
},
{
"ref":"control.flask.method",
"url":9,
"doc":"Get the request method.",
"func":1
},
{
"ref":"control.flask.arg",
"url":9,
"doc":"Get the value of a request arg. Parameters      name: string The name of the arg. Returns    - string or None The value of the arg, if it is defined, else the None.",
"func":1
},
{
"ref":"control.flask.data",
"url":9,
"doc":"Get the request data. Returns    - bytes Useful for uploaded files.",
"func":1
},
{
"ref":"control.flask.values",
"url":9,
"doc":"",
"func":1
},
{
"ref":"control.flask.getReferrer",
"url":9,
"doc":"Get the referrer from the request. We strip the root url from the referrer. If that is not possible, the referrer is an other site, in that case we substitute the home page.  ! caution \"protocol mismatch\" It has been observed that in some cases the referrer, as taken from the request, and the root url as taken from the request, differ in their protocol part:  http: versus  https: . Therefore we first strip the protocol part from both referrer and root url before we remove the prefix. Returns    - string",
"func":1
},
{
"ref":"control.generic",
"url":10,
"doc":""
},
{
"ref":"control.generic.AttrDict",
"url":10,
"doc":"Turn a dict into an object with attributes. If non-existing attributes are accessed for reading,  None is returned. See: https: stackoverflow.com/questions/4984647/accessing-dict-keys-like-an-attribute And: https: stackoverflow.com/questions/16237659/python-how-to-implement-getattr (especially the remark that >  __getattr__ is only used for missing attribute lookup ) We also need to define the  __missing__ method in case we access the underlying dict by means of keys, like  xxx[\"yyy\"] rather then by attribute like  xxx.yyy ."
},
{
"ref":"control.html",
"url":11,
"doc":"HTML generation made easy.  for each HTML element there is a function to wrap attributes and content in it.  additional support for more involved patches of HTML ( details ,  input , icons)  escaping of HTML elements."
},
{
"ref":"control.html.HtmlElement",
"url":11,
"doc":"Wrapping of attributes and content into an HTML element.  Initialization An HtmlElement object. Parameters      name: string See below."
},
{
"ref":"control.html.HtmlElement.atNormal",
"url":11,
"doc":"Normalize the names of attributes. Substitute the  cls attribute name with  class . Substitute the  tp attribute name with  type .",
"func":1
},
{
"ref":"control.html.HtmlElement.atEscape",
"url":11,
"doc":"Escapes double quotes in attribute values.",
"func":1
},
{
"ref":"control.html.HtmlElement.attStr",
"url":11,
"doc":"Stringify attributes.  ! hint Attributes with value  True are represented as bare attributes, without value. For example:  {open=True} translates into  open . Attributes with value  False are omitted.  ! caution Use the name  cls to get a  class attribute inside an HTML element. The name  class interferes too much with Python syntax to be usable as a keyowrd argument. Parameters      atts: dict A dictionary of attributes. addClass: string An extra  class attribute. If there is already a class attribute  addClass will be appended to it. Otherwise a fresh class attribute will be created. Returns    - string The serialzed attributes.",
"func":1
},
{
"ref":"control.html.HtmlElement.wrap",
"url":11,
"doc":"Wraps attributes and content into an element.  ! caution No HTML escaping of special characters will take place. You have to use  control.html.HtmlElements.he yourself. Parameters      material: string | iterable The element content. If the material is not a string but another iterable, the items will be joined by the empty string. addClass: string An extra  class attribute. If there is already a class attribute  addClass will be appended to it. Otherwise a fresh class attribute will be created. Returns    - string The serialzed element.",
"func":1
},
{
"ref":"control.html.HtmlElement.name",
"url":11,
"doc":" string The element name."
},
{
"ref":"control.html.HtmlElements",
"url":11,
"doc":"Wrap specific HTML elements and patterns.  ! note Nearly all elements accept an arbitrary supply of attributes in the  atts parameter, which will not further be documented."
},
{
"ref":"control.html.HtmlElements.he",
"url":11,
"doc":"Escape HTML characters. The following characters will be replaced by entities:   &   .",
"func":1
},
{
"ref":"control.html.HtmlElements.amp",
"url":11,
"doc":"",
"func":1
},
{
"ref":"control.html.HtmlElements.lt",
"url":11,
"doc":"",
"func":1
},
{
"ref":"control.html.HtmlElements.gt",
"url":11,
"doc":"",
"func":1
},
{
"ref":"control.html.HtmlElements.apos",
"url":11,
"doc":"",
"func":1
},
{
"ref":"control.html.HtmlElements.quot",
"url":11,
"doc":"",
"func":1
},
{
"ref":"control.html.HtmlElements.content",
"url":11,
"doc":"fragment. This is a pseudo element. The material will be joined together, without wrapping it in an element. There are no attributes. The material is recursively joined into a string. Parameters      material: string | iterable Every argument in  material may be None, a string, or an iterable. tight: boolean, optional False If True, all material will be joined tightly, with no intervening string. Otherwise, all pieces will be joined with a newline. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.wrapValue",
"url":11,
"doc":"Wraps one or more values in elements. The value is recursively joined into elements. The at the outermost level the result is wrapped in a single outer element. All nested values are wrapped in inner elements. If the value is None, a bare empty string is returned. The structure of elements reflects the structure of the value. Parameters      value: string | iterable Every argument in  value may be None, a string, or an iterable. outerElem: string, optional \"div\" The single element at the outermost level outerArgs: list, optional [] Arguments for the outer element. outerAtts: dict, optional {} Attributes for the outer element. innerElem: string, optional \"span\" The elements at all deeper levels innerArgs: list, optional [] Arguments for the inner elements. innerAtts: dict, optional {} Attributes for the inner elements. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.elem",
"url":11,
"doc":"Wraps an element whose tag is determined at run time. You can also use this to wrap non-html elements. Parameters      thisClass: class The current class tag: string The name of the element  args,  kwargs: any The remaining arguments to be passed to the underlying wrapper.",
"func":1
},
{
"ref":"control.html.HtmlElements.a",
"url":11,
"doc":"A. Hyperlink. Parameters      material: string | iterable Text of the link. href: url Destination of the link. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.body",
"url":11,
"doc":"BODY. The  part of a document Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.br",
"url":11,
"doc":"BR. Line break. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.button",
"url":11,
"doc":"BUTTON. A clickable butto Parameters      material: string | iterable What is displayed on the button. tp: The type of the button, e.g.  submit or  button Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.checkbox",
"url":11,
"doc":"INPUT type=checkbox. The element to receive user clicks. Parameters      var: string The name of an identifier for the element. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.dd",
"url":11,
"doc":"DD. The definition part of a term. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.details",
"url":11,
"doc":"DETAILS. Collapsible details element. Parameters      summary: string | iterable The summary. material: string | iterable The expansion. itemkey: string Identifier for reference from Javascript. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.detailx",
"url":11,
"doc":"detailx. Collapsible details pseudo element. Unlike the HTML  details element, this one allows separate open and close controls. There is no summary.  ! warning The  icon names must be listed in the web.yaml config file under the key  icons . The icon itself is a Unicode character.  ! hint The  atts go to the outermost  div of the result. Parameters      icons: string | (string, string) Names of the icons that open and close the element. itemkey: string Identifier for reference from Javascript. openAtts: dict, optinal,  {} Attributes for the open icon. closeAtts: dict, optinal,  {} Attributes for the close icon. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.div",
"url":11,
"doc":"DIV. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.dl",
"url":11,
"doc":"DL. Definition list. Parameters      items: iterable of (string, string) These are the list items, which are term-definition pairs. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.dt",
"url":11,
"doc":"DT. Term of a definition. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.h",
"url":11,
"doc":"H1, H2, H3, H4, H5, H6. Parameters      level: int The heading level. material: string | iterable The heading content. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.head",
"url":11,
"doc":"HEAD. The  part of a document Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.icon",
"url":11,
"doc":"icon. Pseudo element for an icon.  ! warning The  icon names must be listed in the authorise.yaml config file under the key  icons . The icon itself is a Unicode character. Parameters      icon: string Name of the icon. asChar: boolean, optional,  False If  True , just output the icon character. Otherwise, wrap it in a    with all attributes that might have been passed. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.iconx",
"url":11,
"doc":"iconx. Pseudo element for a clickable icon. It will be wrapped in an    .  element or a  if  href is  None . If  href is the empty string, the element will still be wrapped in an    element, but without a  href attribute.  ! warning The  icon names must be listed in the web.yaml config file under the key  icons . The icon itself is a Unicode character. Parameters      icon: string Name of the icon. href: url, optional,  None Destination of the icon when clicked. Will be left out when equal to the empty string. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.iframe",
"url":11,
"doc":"IFRAME. An iframe, which is an empty element with an obligatory end tag. Parameters      src: url Source for the iframe. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.img",
"url":11,
"doc":"IMG. Image element.  ! note The  atts go to the outer element, which is either    if it is not further wrapped, or    . The  imgAtts only go to the    element. Parameters      src: url The url of the image. href: url, optional,  None The destination to navigate to if the image is clicked. The images is then wrapped in an    element. If missing, the image is not wrapped further. title: string, optional,  None Tooltip. imgAtts: dict, optional  {} Attributes that go to the    element. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.input",
"url":11,
"doc":"INPUT. The element to receive types user input.  ! caution Do not use this for checkboxes. Use  control.html.HtmlElements.checkbox instead.  ! caution Do not use this for file inputs. Use  control.html.HtmlElements.finput instead. Parameters      tp: string The type of input material: string | iterable This goes into the  value attribute of the element, after HTML escaping. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.finput",
"url":11,
"doc":"INPUT type=\"file\". The input element for uploading files. Parameters      fileName: string The name of the currently existing file. If there is not yet a file pass the empty string. accept: string MIME type of uploaded file saveUrl: string The url to which the resulting file should be posted. cls: string, optional  CSS class for the button title: string, optional  tooltip for the button Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.link",
"url":11,
"doc":"LINK. Typed hyperlink in the  element. Parameters      rel: string: The type of the link href: url Destination of the link. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.meta",
"url":11,
"doc":"META. A  element inside the  part of a document Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.p",
"url":11,
"doc":"P. Paragraph. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.script",
"url":11,
"doc":"SCRIPT. Parameters      material: string | iterable The Javascript. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.span",
"url":11,
"doc":"SPAN. Inline element. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.table",
"url":11,
"doc":"TABLE. The table element. Parameters      headers, rows: iterables of iterables An iterable of rows. Each row is a tuple: an iterable of cells, and a CSS class for the row. Each cell is a tuple: material for the cell, and a CSS class for the cell.  ! note Cells in normal rows are wrapped in    , cells in header rows go into    . Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.textarea",
"url":11,
"doc":"TEXTAREA. Input element for larger text, typically Markdown. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.wrapTable",
"url":11,
"doc":"Rows and cells. Parameters      data: iterable of iterables. Rows and cells within them, both with CSS classes. td: function Funnction for wrapping the cells, typically boiling down to wrapping them in either    or    elements. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.asString",
"url":11,
"doc":"Join an iterable of strings or iterables into a string. And if the value is already a string, return it, and if it is  None return the empty string. The material is recursively joined into a string. Parameters      material: string | iterable Every argument in  material may be None, a string, or an iterable. tight: boolean, optional False If True, all material will be joined tightly, with no intervening string. Otherwise, all pieces will be joined with a newline. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.isIterable",
"url":11,
"doc":"Whether a value is a non-string iterable.  ! note Strings are iterables. We want to know whether a value is a string or an iterable of strings.",
"func":1
},
{
"ref":"control.datamodel",
"url":12,
"doc":""
},
{
"ref":"control.datamodel.Datamodel",
"url":12,
"doc":"Datamodel related operations. This class has methods to manipulate various pieces of content in the data sources, and hand it over to higher level objects. It can find out dependencies between related records, and it knows a thing or two about fields. It is instantiated by a singleton object. It has a method which is a factory for  control.datamodel.Field objects, which deal with individual fields. Likewise it has a factory function for  control.datamodel.Upload objects, which deal with file uploads. Parameters      Settings:  control.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo ."
},
{
"ref":"control.datamodel.Datamodel.getDetailRecords",
"url":12,
"doc":"Retrieve the detail records of a master record. It finds all records that have a field containing an id of the given master record. Details are not retrieved recursively, only the direct details of a master are fetched. Parameters      masterTable: string The name of the table in which the master record lives. masterId: ObjectId The id of the master record. Returns    - AttrDict The list of detail records, categorized by detail table in which they occur. The detail tables are the keys, the lists of records in those tables are the values. If the master record cannot be found or if there are no detail records, the empty dict is returned.",
"func":1
},
{
"ref":"control.datamodel.Datamodel.makeField",
"url":12,
"doc":"Make a field object and registers it. An instance of class  control.datamodel.Field is created, geared to this particular field.  ! note \"Idempotent\" If the Field object is already registered, nothing is done. Parameters      key: string Identifier for the field. The configuration for this field will be retrieved using this key. The new field object will be stored under this key. Returns    - object The resulting Field object. It is also added to the  fieldObjects member.",
"func":1
},
{
"ref":"control.datamodel.Datamodel.makeUpload",
"url":12,
"doc":"Make a file upload object and registers it. An instance of class  control.datamodel.Upload is created, geared to this particular field.  ! note \"Idempotent\" If the Upload object is already registered, nothing is done. Parameters      key: string Identifier for the upload. The configuration for this upload will be retrieved using this key. The new upload object will be stored under this key. Returns    - object The resulting Upload object. It is also added to the  uploadObjects member.",
"func":1
},
{
"ref":"control.datamodel.Field",
"url":12,
"doc":"Handle field business. A Field object does not correspond with an individual field in a record. It represents a  column , i.e. a set of fields with the same name in all records of a collection. First of all there is a method to retrieve the value of the field from a specific record. Then there are methods to deliver those values, either bare or formatted, to produce edit widgets to modify the values, and handlers to save values. How to do this is steered by the specification of the field by keys and values that are stored in this object. All field access should be guarded by the authorisation rules. Parameters      kwargs: dict Field configuration arguments. It certain parts of the field configuration are not present, defaults will be provided."
},
{
"ref":"control.datamodel.Field.logical",
"url":12,
"doc":"Give the logical value of the field in a record. Parameters      record: AttrDict or dict The record in which the field value is stored. Returns    - any: Whatever the value is that we find for that field. No conversion/casting to other types will be performed. If the field is not present, returns None, without warning.",
"func":1
},
{
"ref":"control.datamodel.Field.bare",
"url":12,
"doc":"Give the bare string value of the field in a record. Parameters      record: AttrDict or dict The record in which the field value is stored. Returns    - string: Whatever the value is that we find for that field, converted to string. If the field is not present, returns the empty string, without warning.",
"func":1
},
{
"ref":"control.datamodel.Field.formatted",
"url":12,
"doc":"Give the formatted value of the field in a record. Optionally also puts a caption and/or an edit control. The value retrieved is (recursively) wrapped in HTML, steered by additional argument, as in  control.html.HtmlElements.wrapValue . be applied. If the type is 'text', multiple values will simply be concatenated with newlines in between, and no extra classes will be applied. Instead, a markdown formatter is applied to the result. For other types: If the value is an iterable, each individual value is wrapped in a span to which an (other) extra CSS class may be applied. Parameters      table: string The table from which the record is taken record: AttrDict or dict The record in which the field value is stored. level: integer, optional None The heading level in which a caption will be placed. If None, no caption will be placed. If 0, the caption will be placed in a span. button: string, optional  An optional edit button. outerCls: string optional \"fieldouter\" If given, an extra CSS class for the outer element that wraps the total value. Only relevant if the type is not 'text' innerCls: string optional \"fieldinner\" If given, an extra CSS class for the inner elements that wrap parts of the value. Only relevant if the type is not 'text' Returns    - string: Whatever the value is that we find for that field, converted to HTML. If the field is not present, returns the empty string, without warning.",
"func":1
},
{
"ref":"control.datamodel.Field.key",
"url":12,
"doc":"The identifier of this field within the app."
},
{
"ref":"control.datamodel.Field.nameSpace",
"url":12,
"doc":"The first key to access the field data in a record. Example  dc (Dublin Core). So if a record has Dublin Core metadata, we expect that metadata to exist under key  dc in that record. If the namespace is    , it is assumed that we can dig up the values without going into a namespace subdocument first."
},
{
"ref":"control.datamodel.Field.fieldPath",
"url":12,
"doc":"Compound selector in a nested dict. A string of keys, separated by  . , which will be used to drill down into a nested dict. At the end of the path we find the selected value. This field selection is applied after the name space selection (if  nameSpace is not the empty string)."
},
{
"ref":"control.datamodel.Field.tp",
"url":12,
"doc":"The value type of the field. Value types can be string, integer, but also date times, and values from an other collection (value lists)."
},
{
"ref":"control.datamodel.Field.caption",
"url":12,
"doc":"A caption that may be displayed with the field value. The caption may be a literal string with or without a placeholder  {} . If there is no place holder, the caption will precede the content of the field. If there is a placeholder, the content will replace the place holder in the caption."
},
{
"ref":"control.datamodel.Upload",
"url":12,
"doc":"Handle upload business. An upload is like a field of type 'file'. The name of the uploaded file is stored in a record in MongoDb. The contents of the file is stored on the file system. A Upload object does not correspond with an individual field in a record. It represents a  column , i.e. a set of fields with the same name in all records of a collection. First of all there is a method to retrieve the file name of an upload from a specific record. Then there are methods to deliver those values, either bare or formatted, to produce widgets to upload or delete the corresponding files. How to do this is steered by the specification of the upload by keys and values that are stored in this object. All upload access should be guarded by the authorisation rules. Parameters      kwargs: dict Field configuration arguments. The following parts of the field configuration should be present:  table ,  field and  relative ."
},
{
"ref":"control.datamodel.Upload.bare",
"url":12,
"doc":"Give the bare file name as stored in a record in MongoDb. Parameters      record: AttrDict The record in which the file name is stored. Returns    - string: Whatever the value is that we find. If the field is not present, returns None, without warning.",
"func":1
},
{
"ref":"control.datamodel.Upload.getPath",
"url":12,
"doc":"Give the path to the file in question. The path can be used to build the static url and the save url. It does not contain the file name. If the path is non-empty, a \"/\" will be appended.",
"func":1
},
{
"ref":"control.datamodel.Upload.formatted",
"url":12,
"doc":"Give the formatted value of a file field in a record. Optionally also puts an upload control. Parameters      record: AttrDict or dict The record in which the field value is stored. mayChange: boolean, optional False Whether the file may be changed. If so, an upload widget is supplied, wich contains a a delete button. Returns    - string: Whatever the value is that we find for that field, converted to HTML. If the field is not present, returns the empty string, without warning.",
"func":1
},
{
"ref":"control.datamodel.Upload.key",
"url":12,
"doc":"The identifier of this upload within the app."
},
{
"ref":"control.datamodel.Upload.table",
"url":12,
"doc":"The table in which the file name should be placed."
},
{
"ref":"control.datamodel.Upload.field",
"url":12,
"doc":"The field in which the file name should be placed."
},
{
"ref":"control.datamodel.Upload.relative",
"url":12,
"doc":"Indicates the directory where the actual file will be saved. Possibe values:   site : top level of the working data directory of the site   project : project directory of the project in question   edition : edition directory of the project in question If left out, the value will be derived from  table ."
},
{
"ref":"control.datamodel.Upload.accept",
"url":12,
"doc":"The file types that the field accepts."
},
{
"ref":"control.datamodel.Upload.caption",
"url":12,
"doc":"The text to display on the upload button."
},
{
"ref":"control.datamodel.Upload.show",
"url":12,
"doc":"Whether to show the contents of the file. This is typically the case when the file is an image to be presented as a logo."
},
{
"ref":"control.authoidc",
"url":13,
"doc":""
},
{
"ref":"control.authoidc.AuthOidc",
"url":13,
"doc":""
},
{
"ref":"control.authoidc.AuthOidc.OIDC_CLIENT_SECRETS",
"url":13,
"doc":""
},
{
"ref":"control.authoidc.AuthOidc.load_secrets",
"url":13,
"doc":"",
"func":1
},
{
"ref":"control.authoidc.AuthOidc.prepare",
"url":13,
"doc":"",
"func":1
},
{
"ref":"control.pages",
"url":14,
"doc":""
},
{
"ref":"control.pages.Pages",
"url":14,
"doc":"Making responses that can be displayed as web pages. This class has methods that correspond to routes in the app, for which they get the data (using  control.content.Content ), which gets then wrapped in HTML. It is instantiated by a singleton object. Most methods generate a response that contains the content of a complete page. For those methods we do not document the return value. Some methods return something different. If so, it the return value will be documented. Parameters      Settings:  control.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Viewers: object Singleton instance of  control.viewers.Viewers . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo . Content: object Singleton instance of  control.content.Content . Auth: object Singleton instance of  control.auth.Auth ."
},
{
"ref":"control.pages.Pages.home",
"url":14,
"doc":"The site-wide home page.",
"func":1
},
{
"ref":"control.pages.Pages.about",
"url":14,
"doc":"The site-wide about page.",
"func":1
},
{
"ref":"control.pages.Pages.surprise",
"url":14,
"doc":"The \"surprise me!\" page.",
"func":1
},
{
"ref":"control.pages.Pages.projects",
"url":14,
"doc":"The page with the list of projects.",
"func":1
},
{
"ref":"control.pages.Pages.projectInsert",
"url":14,
"doc":"Inserts a project and shows the new project.",
"func":1
},
{
"ref":"control.pages.Pages.project",
"url":14,
"doc":"The landing page of a project. Parameters      projectId: ObjectId The project in question.",
"func":1
},
{
"ref":"control.pages.Pages.editionInsert",
"url":14,
"doc":"Inserts an edition into a project and shows the new edition. Parameters      projectId: ObjectId The project to which the edition belongs.",
"func":1
},
{
"ref":"control.pages.Pages.edition",
"url":14,
"doc":"The landing page of an edition. This page contains a list of scenes. One of these scenes will be loaded in a 3D viewer. It is dependent on defaults which scene in which viewer/version/mode. Parameters      editionId: ObjectId The edition in question. From the edition record we can find the project too.",
"func":1
},
{
"ref":"control.pages.Pages.scene",
"url":14,
"doc":"The landing page of an edition, but with a scene marked as active. This page contains a list of scenes. One of these scenes is chosen as the active scene and will be loaded in a 3D viewer. It is dependent on the parameters and/or defaults in which viewer/version/mode. Parameters      sceneId: ObjectId The active scene in question. From the scene record we can find the edition and the project too. viewer: string or None The viewer to use. version: string or None The version to use. action: string or None The mode in which the viewer is to be used ( view or  edit ).",
"func":1
},
{
"ref":"control.pages.Pages.sceneInsert",
"url":14,
"doc":"Inserts a scene into an edition and shows the new scene. Parameters      projectId: ObjectId The project to which the scene belongs. editionId: ObjectId The edition to which the scene belongs.",
"func":1
},
{
"ref":"control.pages.Pages.viewerFrame",
"url":14,
"doc":"The page loaded in an iframe where a 3D viewer operates. Parameters      sceneId: ObjectId The scene that is shown. viewer: string or None The viewer to use. version: string or None The version to use. action: string or None The mode in which the viewer is to be used ( view or  edit ).",
"func":1
},
{
"ref":"control.pages.Pages.viewerResource",
"url":14,
"doc":"Components requested by viewers. This is the javascript code, the css, and other resources that are part of the 3D viewer software. Parameters      path: string Path on the file system under the viewers base directory where the resource resides. Returns    - response The response consists of the contents of the file plus headers derived from the path. If the file does not exists, a 404 is returned.",
"func":1
},
{
"ref":"control.pages.Pages.dataProjects",
"url":14,
"doc":"Data content requested directly from the file repository. This is  the material requested by the viewers: the scene json itself and additional resources, that are part of the user contributed content that is under control of the viewer: annotations, media, etc.  icons for the site, projects, and editions Parameters      path: string Path on the file system under the data directory where the resource resides. The path is relative to the project, and, if given, the edition. projectId: ObjectId, optional None The id of a project under which the resource is to be found. If None, it is site-wide material. editionId: ObjectId, optional None If not None, the name of an edition under which the resource is to be found. Returns    - response The response consists of the contents of the file plus headers derived from the path. If the file does not exists, a 404 is returned.",
"func":1
},
{
"ref":"control.pages.Pages.upload",
"url":14,
"doc":"",
"func":1
},
{
"ref":"control.pages.Pages.authWebdav",
"url":14,
"doc":"Authorises a webdav request. When a viewer makes a WebDAV request to the server, that request is first checked here for authorisation. See  control.webdavapp.dispatchWebdav() . Parameters      projectId: ObjectId The project in question. editionId: ObjectId The edition in question. path: string The path relative to the directory of the edition. action: string The operation that the WebDAV request wants to do on the data ( view or  edit ). Returns    - boolean Whether the action is permitted on ths data by the current user.",
"func":1
},
{
"ref":"control.pages.Pages.remaining",
"url":14,
"doc":"When the url of the request is not recognized. Parameters      path: string The url (without leading /) that is not recognized. Returns    - response Either a redirect to the referred, for some recognized urls that correspond to not-yet implemented one. Or a 404 abort for all other cases.",
"func":1
},
{
"ref":"control.pages.Pages.page",
"url":14,
"doc":"Workhorse function to get content on the page. Parameters      url: string Initial part of the url that triggered the page function. This part is used to make one of the tabs on the web page active. left: string, optional None Content for the left column of the page. right: string, optional None Content for the right column of the page.",
"func":1
},
{
"ref":"control.pages.Pages.scenes",
"url":14,
"doc":"Workhorse for  Pages.edition() and  Pages.scene() . The common part between the two functions mentioned.",
"func":1
},
{
"ref":"control.pages.Pages.navigation",
"url":14,
"doc":"Generates the navigation controls. Especially the tab bar. Parameters      url: string Initial part of the url on the basis of which one of the tabs can be made active. Returns    - string The HTML of the navigation.",
"func":1
},
{
"ref":"control.pages.Pages.breadCrumb",
"url":14,
"doc":"Makes a link to the landing page of a project. Parameters      projectId: ObjectId The project in question.",
"func":1
},
{
"ref":"control.pages.Pages.putValues",
"url":14,
"doc":"Puts several pieces of metadata on the web page. Parameters      fieldSpecs: string  , -separated list of fieldSpecs projectId: ObjectId, optional None The project in question. editionId: ObjectId, optional None The edition in question. Returns    - string The join of the individual results of retrieving metadata value.",
"func":1
},
{
"ref":"control.pages.Pages.putUpload",
"url":14,
"doc":"Puts a file upload control on a page. Parameters      key: string the key that identifies the kind of upload projectId: ObjectId, optional None The project in question. editionId: ObjectId, optional None The edition in question. cls: string, optional None An extra CSS class for the control Returns    - string A control that shows the file and possibly provides an upload/delete control for it.",
"func":1
},
{
"ref":"control.content",
"url":15,
"doc":""
},
{
"ref":"control.content.Content",
"url":15,
"doc":"Retrieving content from database and file system. This class has methods to retrieve various pieces of content from the data sources, and hand it over to the  control.pages.Pages class that will compose a response out of it. It is instantiated by a singleton object. Parameters      Settings:  control.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Viewers: object Singleton instance of  control.viewers.Viewers . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo ."
},
{
"ref":"control.content.Content.addAuth",
"url":15,
"doc":"Give this object a handle to the Auth object. Because of cyclic dependencies some objects require to be given a handle to Auth after their initialization.",
"func":1
},
{
"ref":"control.content.Content.getSurprise",
"url":15,
"doc":"Get the data that belongs to the surprise-me functionality.",
"func":1
},
{
"ref":"control.content.Content.getProjects",
"url":15,
"doc":"Get the list of all projects. Well, the list of all projects visible to the current user. Unpublished projects are only visible to users that belong to that project. Visible projects are each displayed by means of an icon and a title. Both link to a landing page for the project. Returns    - string A list of captions of the projects, wrapped in a HTML string.",
"func":1
},
{
"ref":"control.content.Content.insertProject",
"url":15,
"doc":"",
"func":1
},
{
"ref":"control.content.Content.getEditions",
"url":15,
"doc":"Get the list of the editions of a project. Well, only if the project is visible to the current user. See  Content.getProjects() . Editions are each displayed by means of an icon and a title. Both link to a landing page for the edition. Parameters      projectId: ObjectId The project in question. Returns    - string A list of captions of the editions of the project, wrapped in a HTML string.",
"func":1
},
{
"ref":"control.content.Content.insertEdition",
"url":15,
"doc":"",
"func":1
},
{
"ref":"control.content.Content.getScenes",
"url":15,
"doc":"Get the list of the scenes of an edition of a project. Well, only if the project is visible to the current user. See  Content.getProjects() . Scenes are each displayed by means of an icon a title and a row of buttons. The title is the file name (without the  .json extension) of the scene. Both link to a landing page for the edition. One of the scenes is made  active , i.e. it is loaded in a specific version of a viewer in a specific mode ( view or  edit ). Which scene is loaded in which viewer and version in which mode, is determined by the parameters. If the parameters do not specify values, sensible defaults are chosen. Parameters      projectId: ObjectId The project in question. editionId: ObjectId The edition in question. sceneId: ObjectId, optional None The active scene. If None the default scene is chosen. A scene record specifies whether that scene is the default scene for that edition. viewer: string, optional None The viewer to be used for the 3D viewing. It should be a supported viewer. If None, the default viewer is chosen. The list of those viewers is in the  yaml/viewers.yml file, which also specifies what the default viewer is. version: string, optional None The version of the chosen viewer that will be used. If no version or a non-existing version are specified, the latest existing version for that viewer will be chosen. action: string, optional  view The mode in which the viewer should be opened. If the mode is  edit , the viewer is opened in edit mode. All other modes lead to the viewer being opened in read-only mode. Returns    - string A list of captions of the scenes of the edition, with one caption replaced by a 3D viewer showing the scene. The list is wrapped in a HTML string.",
"func":1
},
{
"ref":"control.content.Content.insertScene",
"url":15,
"doc":"",
"func":1
},
{
"ref":"control.content.Content.wrapCaption",
"url":15,
"doc":"",
"func":1
},
{
"ref":"control.content.Content.getCaption",
"url":15,
"doc":"",
"func":1
},
{
"ref":"control.content.Content.getValue",
"url":15,
"doc":"Retrieve a metadata value. Metadata sits in a big, potentially deeply nested dictionary of keys and values. These locations are known to the system (based on  fields.yml ). This function retrieves the information from those known locations. If a value is in fact composed of multiple values, it will be handled accordingly. Parameters      key: an identifier for the meta data field. projectId: ObjectId, optional None The project whose metadata we need. If it is None, we are at the site level. editionId: ObjectId, optional None The edition whose metadata we need. If it is None, we need metadata of a project or outer metadata. bare: boolean, optional None Get the bare value, without HTML wrapping and without buttons. Returns    - string It is assumed that the metadata value that is addressed exists. If not, we return the empty string.",
"func":1
},
{
"ref":"control.content.Content.getUpload",
"url":15,
"doc":"Display the name and/or upload controls of an uploaded file. The user may to upload model files and scene files to an edition, and various png files as icons for projects, edtions, and scenes. Here we produce the control to do so. Only if the user has  update authorisation, an upload/delete widget will be returned. Parameters      key: an identifier for the upload field. projectId: ObjectId, optional None The project in question. If it is None, we are at the site level. editionId: ObjectId, optional None The edition in question. If it is None, we are at the project level or site level. sceneId: ObjectId, optional None The scene in question. If it is None, we are at the edition, project, or site level. Returns    - string The name of the file that is currently present, or the indication that no file is present. If the user has edit permission for the edition, we display widgets to upload a new file or to delete the existing file.",
"func":1
},
{
"ref":"control.content.Content.getViewerFile",
"url":15,
"doc":"Gets a viewer-related file from the file system. This is about files that are part of the viewer software. The viewer software is located in a specific directory on the server. This is the viewer base. Parameters      path: string The path of the viewer file within viewer base. Returns    - string The full path to the viewer file, if it exists. Otherwise, we raise an error that will lead to a 404 response.",
"func":1
},
{
"ref":"control.content.Content.getData",
"url":15,
"doc":"Gets a data file from the file system. All data files are located under a specific directory on the server. This is the data directory. Below that the files are organized by projects and editions. Parameters      path: string The path of the data file within project/edition directory within the data directory. projectId: ObjectId, optional None The id of the project in question. editionId: ObjectId, optional None The id of the edition in question. Returns    - string The full path of the data file, if it exists. Otherwise, we raise an error that will lead to a 404 response.",
"func":1
},
{
"ref":"control.content.Content.getItem",
"url":15,
"doc":"Get a all information about an item. The item can be a project, edition, or scene. The information about that item is a record in MongoDb. possibly additional files on the file system. Parameters      table: string The name of the table from which to fetch an item  args,  kwargs: any Additional arguments to select the item's record from MongoDB Returns    - AttrDict the contents of the item's record in MongoDB",
"func":1
},
{
"ref":"control.content.Content.actionButton",
"url":15,
"doc":"Puts a button on the interface, if that makes sense. The button, when pressed, will lead to an action on certain content. It will be checked first if that action is allowed for the current user. If not the button will not be shown.  ! note \"Delete buttons\" Even if a user is authorised to delete a record, it is not allowed to delete master records if its detail records still exist. In that case, no delete button is displayed. Instead we display a count of detail records. Parameters      action: string, optional None The type of action that will be performed if the button triggered. table: string the table to which the action applies; recordId: ObjectId, optional None the record in question projectId: ObjectId, optional None The project in question, if any. Needed to determine whether a press on the button is permitted. editionId: ObjectId, optional None The edition in question, if any. Needed to determine whether a press on the button is permitted. key: string, optional None If present, it identifies a metadata field that is stored inside the record. From the key, the value can be found.",
"func":1
},
{
"ref":"control.content.Content.save",
"url":15,
"doc":"",
"func":1
},
{
"ref":"control.content.Content.getDetailRecords",
"url":12,
"doc":"Retrieve the detail records of a master record. It finds all records that have a field containing an id of the given master record. Details are not retrieved recursively, only the direct details of a master are fetched. Parameters      masterTable: string The name of the table in which the master record lives. masterId: ObjectId The id of the master record. Returns    - AttrDict The list of detail records, categorized by detail table in which they occur. The detail tables are the keys, the lists of records in those tables are the values. If the master record cannot be found or if there are no detail records, the empty dict is returned.",
"func":1
},
{
"ref":"control.content.Content.makeField",
"url":12,
"doc":"Make a field object and registers it. An instance of class  control.datamodel.Field is created, geared to this particular field.  ! note \"Idempotent\" If the Field object is already registered, nothing is done. Parameters      key: string Identifier for the field. The configuration for this field will be retrieved using this key. The new field object will be stored under this key. Returns    - object The resulting Field object. It is also added to the  fieldObjects member.",
"func":1
},
{
"ref":"control.content.Content.makeUpload",
"url":12,
"doc":"Make a file upload object and registers it. An instance of class  control.datamodel.Upload is created, geared to this particular field.  ! note \"Idempotent\" If the Upload object is already registered, nothing is done. Parameters      key: string Identifier for the upload. The configuration for this upload will be retrieved using this key. The new upload object will be stored under this key. Returns    - object The resulting Upload object. It is also added to the  uploadObjects member.",
"func":1
},
{
"ref":"control.messages",
"url":16,
"doc":""
},
{
"ref":"control.messages.Messages",
"url":16,
"doc":"Sending messages to the user and the server log. This class is instantiated by a singleton object. It has methods to issue messages to the screen of the webuser and to the log for the sysadmin. They distinguish themselves by the  severity :  debug ,  info ,  warning ,  error . There is also  plain , a leaner variant of  info . All those methods have two optional parameters:  logmsg and  msg . The behaviors of these methods are described in detail in the  Messages.message() function.  ! hint \"What to disclose?\" You can pass both parameters, which gives you the opportunity to make a sensible distinction between what you tell the web user (not much) and what you send to the log (the gory details). Parameters      Settings:  control.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings . onFlask: boolean, optional True If False, mo messages will be sent to the screen of the webuser, instead those messages end up in the log. This is useful in the initial processing that takes place before the flask app is started."
},
{
"ref":"control.messages.Messages.debugAdd",
"url":16,
"doc":"Adds a quick debug method to a destination object. The result of this method is that instead of saying   self.Messages.debug (logmsg=\"blabla\")   you can say   self.debug (\"blabla\")   It is recommended that in each object where you store a handle to Messages, you issue the statement   Messages.addDebug(self)  ",
"func":1
},
{
"ref":"control.messages.Messages.debug",
"url":16,
"doc":"Issue a debug message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.error",
"url":16,
"doc":"Issue an error message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.warning",
"url":16,
"doc":"Issue a warning message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.info",
"url":16,
"doc":"Issue a informational message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.plain",
"url":16,
"doc":"Issue a informational message, without bells and whistles. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.message",
"url":16,
"doc":"Workhorse to issue a message in a variety of ways. It can issue log messages and screen messages. Parameters      tp: string The severity of the message. There is a fixed number of types:   debug Messages are prepended with  DEBUG:  . Log messages go to stderr. Messages will only show up on the web page if the app runs in debug mode.   plain Messages are not prepended with anything. Log messages go to standard output.   info Messages are prepended with  INFO:  . Log messages go to standard output.   warning Messages are prepended with  WARNING:  . Log messages go to standard error.   error Messages are prepended with  ERROR:  . Log messages go to standard error. It also raises an exception, which will lead to a 404 response (if flask is running, that is). msg: string, optional None If not None, it is the contents of a screen message. Ths happens by the built-in  flash method of Flask. logmsg: string, optional None If not None, it is the contents of a log message.",
"func":1
},
{
"ref":"control.environment",
"url":17,
"doc":""
},
{
"ref":"control.environment.var",
"url":17,
"doc":"Retrieves the value of an environment variable. Parameters      name: string The name of the environment variable Returns    - string or None If the variable does not exist, None is returned.",
"func":1
},
{
"ref":"control.app",
"url":18,
"doc":""
},
{
"ref":"control.app.appFactory",
"url":18,
"doc":"Sets up the main flask app. The main task here is to configure routes, i.e. mappings from url-patterns to functions that create responses  ! note \"WebDAV enabling\" This flask app will later be combined with a webdav app, so that the combined app has the business logic of the main app but can also handle webdav requests. The routes below contain a few patterns that are used for authorising WebDAV calls: the onses starting with  /auth and  /cannot . See also  control.webdavapp . Parameters      objects:  control.generic.AttrDict a slew of objects that set up the toolkit with which the app works: settings, messaging and logging, MongoDb connection, 3d viewer support, higher level objects that can fetch chunks of content and distribute it over the web page. Returns    - object A WebDAV-enabled flask app, which is a wsgi app.",
"func":1
},
{
"ref":"control.viewers",
"url":19,
"doc":""
},
{
"ref":"control.viewers.Viewers",
"url":19,
"doc":"Knowledge of the installed 3D viewers. This class knows which (versions of) viewers are installed, and has the methods to invoke them. It is instantiated by a singleton object. Parameters      Settings:  control.generic.AttrDict App-wide configuration data obtained from  control.config.Config.Settings ."
},
{
"ref":"control.viewers.Viewers.addAuth",
"url":19,
"doc":"Give this object a handle to the Auth object. The Viewers and Auth objects need each other, so one of them must be given the handle to the other after initialization.",
"func":1
},
{
"ref":"control.viewers.Viewers.check",
"url":19,
"doc":"Checks whether a viewer version exists. Given a viewer and a version, it is looked up whether the code is present. If not, reasonable defaults returned instead by default. Parameters      viewer: string The viewer in question. version: string The version of the viewer in question. fail: boolean, optional False If true, returns True or False, depending on whther the given viewer-version combination is supported. Returns    - tuple or boolean The viewer and version are returned unmodified if that viewer version is supported. If the viewer is supported, but not the version, the default version of that viewer is taken, if there is a default version, otherwise the latest supported version. If the viewer is not supported, the default viewer is taken. See the  fail parameter above.",
"func":1
},
{
"ref":"control.viewers.Viewers.getFrame",
"url":19,
"doc":"Produces a set of buttons to launch 3D viewers for a scene. Parameters      sceneId: ObjectId The scene in question. actions: iterable of string The actions for which we have to create buttons. Typically  read and possibly also  update . viewerActive: string or None The viewer in which the scene is currently loaded, if any, otherwise None versionActive: string or None The version of the viewer in which the scene is currently loaded, if any, otherwise None actionActive: string or None The mode in which the scene is currently loaded in the viewer ( read or  update ), if any, otherwise None Returns    - string The HTML that represents the buttons.",
"func":1
},
{
"ref":"control.viewers.Viewers.genHtml",
"url":19,
"doc":"Generates the HTML for the viewer page that is loaded in an iframe. When a scene is loaded in a viewer, it happens in an iframe. Here we generate the complete HTML for such an iframe. Parameters      urlBase: string The first part of the root url that is given to the viewer. The viewer code uses this to retrieve additional information. The root url will be completed with the  action and the  viewer . sceneName: string The name of the scene in the file system. The viewer will find the scene json file by this name. viewer: string The chosen viewer. version: string The chosen version of the viewer. action: string The chosen mode in which the viewer is launched ( read or  update ). Returns    - string The HTML for the iframe.",
"func":1
},
{
"ref":"control.viewers.Viewers.getRoot",
"url":19,
"doc":"Composes the root url for a viewer. The root url is passed to a viewer instance as the url that the viewer can use to fetch its data. It is not meant for the static data that is part of the viewer software, but for the model related data that the viewer is going to display. See  getStaticRoot() for the url meant for getting parts of the viewer software. Parameters      urlBase: string The first part of the root url, depending on the project and edition. action: string The mode in which the viewer is opened. Depending on the mode, the viewer code may communicate with the server with different urls. For example, for the voyager, the  read mode (voyager-explorer) uses ordinary HTTP requests, but the  update mode (voyager-story) uses WebDAV requests. So this app points voyager-explorer to a root url starting with  /data , and voyager-story to a root url starting with  /webdav . These prefixes of the urls can be configured per viewer in the viewer configuration in  yaml/viewers.yml .",
"func":1
},
{
"ref":"control.viewers.Viewers.getStaticRoot",
"url":19,
"doc":"Composes the static root url for a viewer. The static root url is passed to a viewer instance as the url that the viewer can use to fetch its assets. It is not meant for the model related data, but for the parts of the viewer software that it needs to get from the server. See  getRoot() for the url meant for getting model-related data. Parameters      urlBase: string The first part of the root url, depending on the project and edition. action: string The mode in which the viewer is opened. Depending on the mode, the viewer code may communicate with the server with different urls. For example, for the voyager, the  read mode (voyager-explorer) uses ordinary HTTP requests, but the  update mode (voyager-story) uses WebDAV requests. So this app points voyager-explorer to a root url starting with  /data , and voyager-story to a root url starting with  /webdav . These prefixes of the urls can be configured per viewer in the viewer configuration in  yaml/viewers.yml .",
"func":1
},
{
"ref":"control.prepare",
"url":20,
"doc":""
},
{
"ref":"control.prepare.prepare",
"url":20,
"doc":"Prepares the way for setting up the Flask webapp. Several classes are instantiated with a singleton object; each of these objects has a dedicated task in the app:   control.config.Config.Settings : all configuration aspects   control.messages.Messages : handle all messaging to user and sysadmin   control.mongo.Mongo : higher-level commands to the MongoDb   control.viewers.Viewers : support the third party 3D viewers   control.datamodel.Datamodel : factory for handling fields   control.content.Content : retrieve all data that needs to be displayed   control.auth.Auth : compute the permission of the current user to access content   control.pages.Pages : high-level functions that distribute content over the page  ! note \"Should be run once!\" These objects are used in several web apps:  the main web app  a copy of the main app that is enriched with the webdav functionality However, these objects should be initialized once, before either app starts, and the same objects should be passed to both invocations of the factory functions that make them ( control.app.appFactory ). The invocations are done in  control.webdavapp.appFactory . Parameters      trivial: boolean, optional False If True, skips the initialization of most objects. Useful if the pure3d app container should run without doing anything. This happens when we just want to start the container and run shell commands inside it, for example after a complicated refactoring when the flask app has too many bugs. Returns    -  control.generic.AttrDict A dictionary keyed by the names of the singleton objects and valued by the singleton objects themselves.",
"func":1
}
]