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
"control/admin.html",
"control/messages.html",
"control/environment.html",
"control/app.html",
"control/viewers.html",
"control/wrap.html",
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
"doc":"Factory function for the master flask app.",
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
"doc":"All about authorised data access. This class knows users because it is based on the Users class. This class also knows content, and decides whether the current user is authorised to perform certain actions on content in question. It is instantiated by a singleton object. Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo . Content: object Singleton instance of  control.content.Content ."
},
{
"ref":"control.auth.Auth.authorise",
"url":2,
"doc":"Check whether an action is allowed on data. The \"create\" action is a bit special, because we do not have any record to start with. In this case  table and  record should point to the master record, and  insertTable should have the table that will contain the new record. If the action is anything else,  tabale and  record refer to the relevant record, and  insertTable should not be passed. How do the authorisation rules work? First we consider the site-wise role of the user: guest, user, admin, or root. If the action is allowed on that basis, we return True. If not, we look whether the user has an additional role with regard to the record in question, or with any of its master records. If so, we apply the rules for those cases and see whether the action is permitted. Then we have the possibility that a record is in a certain state, e.g. projects may be visible or invisible, editions may be published or unpublished. For each of these states we have separate rules, so we inspect the states of the records and master records in order to select the appropriate rules. Parameters      table: string the relevant table; for  create actions it is the master table of the table in which a record will be inserted. record: ObjectId | AttrDict The id of the record that is being accessed or the record itself; for  create actions it is the master record to which a new record will be created as a detail. action: string, optional None The action for which permission is asked. insertTable: string Only relevant for \"create\" actions. The detail table in which the new record will be inserted. Returns    - boolean | dict If an action is passed: boolean whether action is allowed. If no action is passed: dict keyed by the allowed actions, the values are true. Actions with a falsy permission (False or the empty set) are not included in the dict. So, to test whether any action is allowed, it suffices to test whether  action in result ",
"func":1
},
{
"ref":"control.auth.Auth.makeSafe",
"url":2,
"doc":"Changes an update action into a read action if needed. This function 'demotes' an \"update: to a \"read\" if the \"update\" is not allowed. If \"read\" itself is not allowed, None is returned. If any other action tahn \"update\" or \"read\" is passed, None is returned. Parameters      table: string The table in which the record exists. record: ObjectId | AttrDict The id of the record or the record itself. action: string An intended action. Returns    - string | void The resulting safe action.",
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
"doc":"Log in a user. Logging in has several main steps: 1. redirecting to a private page, for which login is required 2. obtaining the authentication results when the user visits that page 3. storing the relevant user data When we log in test users, we can skip the first step, because we already know everything about the test user on the basis of the information in the request that brought us here. So, we find out if we have to log in a test user or a user that must be authenticated through oidc. We only log in a test user if we are in test mode and the user's \"sub\" is passed in the request. Returns    - response A redirect. When logging in in test mode, the redirect is to  referrer (the url we came from). Otherwise it is to a url that triggers an oidc login procedure. To that page we pass the referrer as part of the url, so that after login the user can be redirected to the original referrer.",
"func":1
},
{
"ref":"control.auth.Auth.afterLogin",
"url":3,
"doc":"Logs in a user. When this function starts operating, the user has been through the login process provided by the authentication service. We can now find the user's \"sub\" and additional attributes in the request context. We use that information to lookup the user in the MongoDb users table. If the user does not exists, we add a new user record, with this \"sub\" and these attributes, and role  user . If the user does exists, we check whether we have to update his attributes. If the attributes found in MongoDb differ from those supplied by the authentication service, we update the MongoDb values on the basis of the provider values. Parameters      referrer: string url where we came from. Returns    - response A redirect to the referrer, with a status 302 if the log in was successful or 303 if not.",
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
"doc":"Who is the currently authenticated user? The  __User member is inspected: does it contain a field called  user ? If so, that is taken as proof that we have a valid user. Returns    - dict Otherwise a copy of the complete __User record is returned. unless there is no  user member in the current user, then the empty dictionary is returned.",
"func":1
},
{
"ref":"control.auth.Auth.getUser",
"url":3,
"doc":"Obtain the \"sub\" of the currently logged in user from the request info. It works for test users and normal users. Parameters      fromArg: boolean, optional False If True, the test user is not read from the session, but from a request argument. This is used during the login procedure of test users. Returns    - boolean, boolean, string Whether we are in test mode. Whether the user is a test user. The \"sub\" of the user",
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
"doc":"Reads a yaml file. Parameters      filePath: string The path of the file on the file system. defaultEmpty: boolean, optional False What to do if the file does not exist. If True, it returns an empty AttrDict otherwise False. Returns    - AttrDict | void The data content of the yaml file if it exists.",
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
"ref":"control.files.listFilesAccepted",
"url":4,
"doc":"The list of all files in a directory that match a certain accepted header. If the directory does not exist, the empty list is returned.",
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
"ref":"control.collect",
"url":5,
"doc":""
},
{
"ref":"control.collect.Collect",
"url":5,
"doc":"Provides initial data collection into MongoDb. Normally, this does not have to run, since the MongoDb is persistent. Only when the MongoDb of the Pure3D app is fresh, or when the MongoDb is out of sync with the data on the filesystem it must be initialized. It reads:  configuration data of the app,  project data on the file system  workflow data on the file system  3D-viewer code on file system The project-, workflow, and viewer data should be placed on the same share in the file system, by a provision step that is done on the host. The data for the supported viewers is in repo  pure3d-data , under  viewers . For testing, there is  exampledata in the same  pure3d-data repo. The provision step should copy the contents of  exampledata to the  data directory of this repo ( pure3dx ). If data collection is triggered in test mode, the user table will be wiped, and the test users present in the example data will be imported. Otherwise the user table will be left unchanged. Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo ."
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
"doc":"Collects data belonging to the editions of a project. Parameters      projectInPath: string Path on the filesystem to the input directory of this project projectOutPath: string Path on the filesystem to the destination directory of this project projectName: String Name of the project to collect.",
"func":1
},
{
"ref":"control.collect.Collect.doEdition",
"url":5,
"doc":"Collects data belonging to a specific edition. Parameters      projectName: String Name of the project to which the edition belongs. editionsInPath: string Path on the filesystem to the editions input directory within this project. editionsOutPath: string Path on the filesystem to the editions working directory within this project. editionName: string Directory name of the edition to collect.",
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
"doc":"Managing edit sessions of users. This class has methods to create and delete edit sessions for users, which guard them from overwriting each other's data. Edit sessions prevent users from editing the same piece of content, in particular it prevents multiple  edit -mode 3D viewers being active with the same scene. It is instantiated by a singleton object.  What are edit sessions? First of all, this machinery is only called upon if the user is  authorised to edit the relevant piece of content. Whether an authorised user may proceed depends on whether the content in question is not currently being edited by an other user. The idea is that content may only be modified (updated/deleted) if it is guarded by an edit session. An edit session is a MongoDb record that holds a user id and fields that specify a piece of content, and a time stamp. The timestamp counts as the start of the session. When users are done, the edit session is deleted. The idea is, that before a user is granted edit access to content, it is checked first whether there is an existing edit session for that user and that content. If so, edit access is not granted. If there is no such editsession, access is granted, and a new editsession is made. Whenever the user terminates the editing action, the editsession is deleted. A user can also save withoout terminating the edit action. In that case the timestamp is set to the current time. Editsessions will be removed after a certain amount of time. So, editsessions contain:  a user specification  a content specification  a time specification  User specification : when a session is created, the _id of the current user is stored in the userId field of the editSession record.  Content specification : we need to specify content in MongoDb records and on the file system.  ! caution \"Disclaimer\" We do not attempt to make a water-tight locking system, because the situation is a bit complex, due to the fact that most file system content is edited through a 3rd party 3D viewer (currently: Voyager-Story). Moreover, there may be multiple scenes for a single 3D model, and these scenes may refer to the same articles, although every scene contains its own metadata of the articles. In this fuzzy situation we choose a rather coarse mode of action:  at most one Voyager-Story is allowed to be fired up per edition;  file actions are guarded together with the mongo records that are also affected by those actions. That means that content specifications boil down to:   table : the name of the collection in which the meta data record sits   recordId : the id of the record in which the metadata sits We list all possible non-mongo actions and indicate the corresponding content specifications (the id values are imaginary):   viewer sessions that allow editing actions :  table=\"edition\" recordId=\"176ba\"   icon file changes   site level :  table=\"site\" recordId=\"954fe\"   project level :  table=\"project\" recordId=\"065af\"   edition level :  table=\"edition\" recordId=\"176ba\"   model file changes  table=\"edition\" recordId=\"176ba\"   scene file changes  table=\"edition\" recordId=\"176ba\"  ! note \"scene locks are edition wide\" Even if you want to change an icon of a single scene, you need a full edition-level edit session.  Expiring edit sessions Edit sessions expire if the user is done with the action for which they needed the session. But sometimes users forget to finalise their actions, and for those cases we need something that prevents edit sessions to be immortal. We let the server expire sessions that reach their expiration time. When edit sessions have expired this way, other users may claim editsessions for that content. Expiration does not delete the session, but flags it as terminated. Only when another uses asks for a new edit session with the same content specs, the terminated session is deleted, after which a new one is created for that other user. If the original user, who has not saved his material in time, tries to save content guarded by a terminated session, it will be allowed if the expired session still exists. Because in that case no other user has claimed an editsession for the content, and hence no other user has modified it. But if the terminated session has been deleted because of a new edit session by another user, the original user will be notified when he attempts to save. The user cannot proceed, the only thing he can do is to copy the content to the clipboard, try to obtain a new session, and paste the content in that session. If a user tries to save content without there being a corresponding edit session. Parameters      Mongo: object Singleton instance of  control.mongo.Mongo . Auth: object Singleton instance of  control.auth.Auth ."
},
{
"ref":"control.editsessions.EditSessions.EXPIRATION",
"url":6,
"doc":""
},
{
"ref":"control.editsessions.EditSessions.EXPIRATION_VIEWER",
"url":6,
"doc":""
},
{
"ref":"control.editsessions.EditSessions.lookup",
"url":6,
"doc":"Look up an edit session. Parameters      table: string The table of the edited material recordId: ObjectId The id of the record of the edited material Returns    - ObjectId | void If the editsession has been found, the id of that session, otherwise None",
"func":1
},
{
"ref":"control.editsessions.EditSessions.create",
"url":6,
"doc":"Create or extend an edit session of a field in a record for the current user. The system can create new editsessions or extend existing editsessions. Creation is needed when the user wants to start editing a piece of content that he was not already editing. Extending is needed when a user is editing a piece of content and performs a save, while continuing editing the content. Parameters      table: string The table of the edited material recordId: ObjectId The id of the record of the edited material session: boolean, optional False Whether the editsession is for a viewer session or for something else. This has only influence on the amount of time after which the session expires. extend: boolean, optional False If called with  extend=False a new editsession is required, otherwise an existing edit session is timestamped with the current time. Returns    - boolean Whether the operation succeeded. False means that the user should not get the opportunity to continue the edit action.",
"func":1
},
{
"ref":"control.editsessions.EditSessions.terminates",
"url":6,
"doc":"Delete an edit session. Parameters      table: string The table of the edited material recordId: ObjectId The id of the record of the edited material Returns    - void",
"func":1
},
{
"ref":"control.editsessions.EditSessions.timeout",
"url":6,
"doc":"Terminate all outdated edit sessions. An outdated editsession is one whose timestamp lies too far in the past. For sessions that correspond to a viewer session, this amount is given in the class member  EXPIRATION_VIEWER . For other sessions it is given by the much shorter  EXPIRATION . This method should be called every minute or so.",
"func":1
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
"doc":"Read the WEBDav methods from the webdav.yaml file. The methods are associated with the  read or  update keyword, depending on whether they are  GET like or  PUT like.",
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
"doc":"All about users and the current user. This class has methods to login/logout a user, to retrieve the data of the currently logged in user, and to query the users table in MongoDb. It is instantiated by a singleton object. This object has a member  __User that contains the data of the current user if there is a current user. Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo ."
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
"doc":"Log in a user. Logging in has several main steps: 1. redirecting to a private page, for which login is required 2. obtaining the authentication results when the user visits that page 3. storing the relevant user data When we log in test users, we can skip the first step, because we already know everything about the test user on the basis of the information in the request that brought us here. So, we find out if we have to log in a test user or a user that must be authenticated through oidc. We only log in a test user if we are in test mode and the user's \"sub\" is passed in the request. Returns    - response A redirect. When logging in in test mode, the redirect is to  referrer (the url we came from). Otherwise it is to a url that triggers an oidc login procedure. To that page we pass the referrer as part of the url, so that after login the user can be redirected to the original referrer.",
"func":1
},
{
"ref":"control.users.Users.afterLogin",
"url":3,
"doc":"Logs in a user. When this function starts operating, the user has been through the login process provided by the authentication service. We can now find the user's \"sub\" and additional attributes in the request context. We use that information to lookup the user in the MongoDb users table. If the user does not exists, we add a new user record, with this \"sub\" and these attributes, and role  user . If the user does exists, we check whether we have to update his attributes. If the attributes found in MongoDb differ from those supplied by the authentication service, we update the MongoDb values on the basis of the provider values. Parameters      referrer: string url where we came from. Returns    - response A redirect to the referrer, with a status 302 if the log in was successful or 303 if not.",
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
"doc":"Who is the currently authenticated user? The  __User member is inspected: does it contain a field called  user ? If so, that is taken as proof that we have a valid user. Returns    - dict Otherwise a copy of the complete __User record is returned. unless there is no  user member in the current user, then the empty dictionary is returned.",
"func":1
},
{
"ref":"control.users.Users.getUser",
"url":3,
"doc":"Obtain the \"sub\" of the currently logged in user from the request info. It works for test users and normal users. Parameters      fromArg: boolean, optional False If True, the test user is not read from the session, but from a request argument. This is used during the login procedure of test users. Returns    - boolean, boolean, string Whether we are in test mode. Whether the user is a test user. The \"sub\" of the user",
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
"doc":"CRUD interface to content in the MongoDb database. This class has methods to connect to a MongoDb database, to query its data, to create, update and delete data. It is instantiated by a singleton object.  ! note \"string versus ObjectId\" Some functions execute MongoDb statements, based on parameters whose values are MongoDb identifiers. These should be objects in the class  bson.objectid.ObjectId . However, in many cases these ids enter the app as strings. In this module, such strings will be cast to proper ObjectIds, provided they are recognizable as values in a field whose name is  _id or ends with  Id . Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages ."
},
{
"ref":"control.mongo.Mongo.cast",
"url":8,
"doc":"Try to cast the value as an ObjectId. Paramaters      value:string The value to cast, normally a string representation of a BSON ObjectId. Returns    - ObjectId | void The corresponding BSON ObjectId if the input is a valid representation of such an id, otherwise  None .",
"func":1
},
{
"ref":"control.mongo.Mongo.isId",
"url":8,
"doc":"Test whether a value is an ObjectId Parameters      value: any The value to test Returns    - boolean Whether the value is an objectId",
"func":1
},
{
"ref":"control.mongo.Mongo.connect",
"url":8,
"doc":"Make connection with MongoDb if there is no connection yet. The connection details come from  control.config.Config.Settings . After a successful connection attempt, the connection handle is stored in the  client and  db members of the Mongo object. When a connection handle exists, this method does nothing.",
"func":1
},
{
"ref":"control.mongo.Mongo.disconnect",
"url":8,
"doc":"Disconnect from the MongoDB.",
"func":1
},
{
"ref":"control.mongo.Mongo.collections",
"url":8,
"doc":"List the existent collections in the database. Returns    - list The names of the collections.",
"func":1
},
{
"ref":"control.mongo.Mongo.clearCollection",
"url":8,
"doc":"Make sure that a collection exists and that it is empty. Parameters      table: string The name of the collection. If no such collection exists, it will be created. delete: boolean, optional False If True, and the collection existed before, it will be deleted. If False, the collection will be cleared, i.e. all its documents get deleted, but the table remains.",
"func":1
},
{
"ref":"control.mongo.Mongo.get",
"url":8,
"doc":"Get the record and recordId if only one of them is specified. If the record is specified by id, the id maybe an ObjectId or a string, which will then be cast to an ObjectId. Parameters      table: string The table in which the record can be found record: string | ObjectID | AttrDict | void Either the id of the record, or the record itself. Returns    - tuple  ObjectId: the id of the record  AttrDict: the record itself If  record is None, both members of the tuple are None",
"func":1
},
{
"ref":"control.mongo.Mongo.getRecord",
"url":8,
"doc":"Get a single document from a collection. Parameters      table: string The name of the collection from which we want to retrieve a single record. warn: boolean, optional True If True, warn if there is no record satisfying the criteria. stop: boolean, optional True If the command is not successful, stop after issuing the error, do not return control. criteria: dict A set of criteria to narrow down the search. Usually they will be such that there will be just one document that satisfies them. But if there are more, a single one is chosen, by the mechanics of the built-in MongoDb command  findOne . Returns    - AttrDict The single document found, or an empty AttrDict if no document satisfies the criteria.",
"func":1
},
{
"ref":"control.mongo.Mongo.getList",
"url":8,
"doc":"Get a list of documents from a collection. Parameters      table: string The name of the collection from which we want to retrieve records. stop: boolean, optional True If the command is not successful, stop after issuing the error, do not return control. criteria: dict A set of criteria to narrow down the search. Returns    - list of AttrDict The list of documents found, empty if no documents are found. Each document is cast to an AttrDict.",
"func":1
},
{
"ref":"control.mongo.Mongo.deleteRecord",
"url":8,
"doc":"Updates a single document from a collection. Parameters      table: string The name of the collection in which we want to update a single record. stop: boolean, optional True If the command is not successful, stop after issuing the error, do not return control. criteria: dict A set of criteria to narrow down the selection. Usually they will be such that there will be just one document that satisfies them. But if there are more, a single one is chosen, by the mechanics of the built-in MongoDb command  updateOne . Returns    - boolean Whether the delete was successful",
"func":1
},
{
"ref":"control.mongo.Mongo.updateRecord",
"url":8,
"doc":"Updates a single document from a collection. Parameters      table: string The name of the collection in which we want to update a single record. updates: dict The fields that must be updated with the values they must get stop: boolean, optional True If the command is not successful, stop after issuing the error, do not return control. criteria: dict A set of criteria to narrow down the selection. Usually they will be such that there will be just one document that satisfies them. But if there are more, a single one is chosen, by the mechanics of the built-in MongoDb command  updateOne . Returns    - boolean Whether the update was successful",
"func":1
},
{
"ref":"control.mongo.Mongo.insertRecord",
"url":8,
"doc":"Inserts a new record in a table. Parameters      table: string The table in which the record will be inserted. stop: boolean, optional True If the command is not successful, stop after issuing the error, do not return control.  fields: dict The field names and their contents to populate the new record with. Returns    - ObjectId The id of the newly inserted record, or None if the record could not be inserted.",
"func":1
},
{
"ref":"control.mongo.Mongo.execute",
"url":8,
"doc":"Executes a MongoDb command and returns the result. Parameters      table: string The collection on which to perform the command. command: string The built-in MongoDb command. Note that the Python interface requires you to write camelCase commands with underscores. So the Mongo command  findOne should be passed as  find_one . args: list Any number of additional arguments that the command requires. stop: boolean, optional True If the command is not successful, stop after issuing the error, do not return control. kwargs: list Any number of additional keyword arguments that the command requires. Returns    - any Whatever the MongoDb command returns. If the command fails, an error message is issued and None is returned.",
"func":1
},
{
"ref":"control.flask",
"url":9,
"doc":""
},
{
"ref":"control.flask.appInitializing",
"url":9,
"doc":"Whether the flask web app is already running. It is False during the initialization code in the app factory before the flask app is delivered.",
"func":1
},
{
"ref":"control.flask.appMake",
"url":9,
"doc":"Create the Flask app.",
"func":1
},
{
"ref":"control.flask.renderTemplate",
"url":9,
"doc":"Renders a template. Parameters      template: string The name of the template, without extension. kwargs: dict The variables with values to fill in into the template. Returns    - object The response with as content the filled template.",
"func":1
},
{
"ref":"control.flask.flashMsg",
"url":9,
"doc":"Gives user feedback using the Flask flash mechanism.",
"func":1
},
{
"ref":"control.flask.response",
"url":9,
"doc":"Wrap data in a response. Parameters      data: any The data to be transferred in an HTTP response. Returns    - object The HTTP response",
"func":1
},
{
"ref":"control.flask.sendFile",
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
"ref":"control.flask.appStop",
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
"doc":"Gets a variable from the session. Parameters      name: string The name of the variable. Returns    - string | void The value of the variable, if it exists, else None.",
"func":1
},
{
"ref":"control.flask.sessionSet",
"url":9,
"doc":"Sets a session variable to a value. Parameters      name: string The name of the variable. value: string The value that will be assigned to the variable Returns    - void",
"func":1
},
{
"ref":"control.flask.requestMethod",
"url":9,
"doc":"Get the request method.",
"func":1
},
{
"ref":"control.flask.requestArg",
"url":9,
"doc":"Get the value of a request arg. Parameters      name: string The name of the arg. Returns    - string | void The value of the arg, if it is defined, else the None.",
"func":1
},
{
"ref":"control.flask.requestData",
"url":9,
"doc":"Get the request data. Returns    - bytes Useful for uploaded files.",
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
"ref":"control.generic.now",
"url":10,
"doc":"The current moment in time as a isolike string value. Strips everything after the decimal point, (milliseconds and timezone).",
"func":1
},
{
"ref":"control.generic.AttrDict",
"url":10,
"doc":"Turn a dict into an object with attributes. If non-existing attributes are accessed for reading,  None is returned. See: https: stackoverflow.com/questions/4984647/accessing-dict-keys-like-an-attribute And: https: stackoverflow.com/questions/16237659/python-how-to-implement-getattr (especially the remark that >  __getattr__ is only used for missing attribute lookup ) We also need to define the  __missing__ method in case we access the underlying dict by means of keys, like  xxx[\"yyy\"] rather then by attribute like  xxx.yyy . Create the data structure from incoming data."
},
{
"ref":"control.generic.deepAttrDict",
"url":10,
"doc":"Turn a dict into an AttrDict, recursively. Parameters      info: any The input dictionary. We assume that it is a data structure built by tuple, list, set, frozenset, dict and atomic types such as int, str, bool. We assume there are no user defined objects in it, and no generators and functions. Returns    - AttrDict An AttrDict containing the same info as the input dict, but where each value of type dict is turned into an AttrDict.",
"func":1
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
"doc":"Wrap specific HTML elements and patterns.  ! note Nearly all elements accept an arbitrary supply of attributes in the  atts parameter, which will not further be documented. Gives the HtmlElements access to Settings and Messages."
},
{
"ref":"control.html.HtmlElements.amp",
"url":11,
"doc":""
},
{
"ref":"control.html.HtmlElements.lt",
"url":11,
"doc":""
},
{
"ref":"control.html.HtmlElements.gt",
"url":11,
"doc":""
},
{
"ref":"control.html.HtmlElements.apos",
"url":11,
"doc":""
},
{
"ref":"control.html.HtmlElements.quot",
"url":11,
"doc":""
},
{
"ref":"control.html.HtmlElements.nbsp",
"url":11,
"doc":""
},
{
"ref":"control.html.HtmlElements.he",
"url":11,
"doc":"Escape HTML characters. The following characters will be replaced by entities:   &   .",
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
"doc":"Wraps one or more values in elements. The value is recursively joined into elements. The value at the outermost level the result is wrapped in a single outer element. All nested values are wrapped in inner elements. If the value is None, a bare empty string is returned. The structure of elements reflects the structure of the value. Parameters      value: string | iterable Every argument in  value may be None, a string, or an iterable. outerElem: string, optional \"div\" The single element at the outermost level outerArgs: list, optional [] Arguments for the outer element. outerAtts: dict, optional {} Attributes for the outer element. innerElem: string, optional \"span\" The elements at all deeper levels innerArgs: list, optional [] Arguments for the inner elements. innerAtts: dict, optional {} Attributes for the inner elements. Returns    - string(html)",
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
"ref":"control.html.HtmlElements.b",
"url":11,
"doc":"B. Bold element. Parameters      material: string | iterable Returns    - string(html)",
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
"doc":"BUTTON. A clickable button Parameters      material: string | iterable What is displayed on the button. tp: The type of the button, e.g.  submit or  button Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.code",
"url":11,
"doc":"CODE. Code element. Parameters      material: string | iterable Returns    - string(html)",
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
"doc":"detailx. Collapsible details pseudo element. Unlike the HTML  details element, this one allows separate open and close controls. There is no summary.  ! warning The  icon names must be listed in the web.yaml config file under the key  icons . The icon itself is a Unicode character.  ! hint The  atts go to the outermost  div of the result. Parameters      detailIcons: string | (string, string) Names of the icons that open and close the element. itemkey: string Identifier for reference from Javascript. openAtts: dict, optinal,  {} Attributes for the open icon. closeAtts: dict, optinal,  {} Attributes for the close icon. Returns    - string(html)",
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
"ref":"control.html.HtmlElements.i",
"url":11,
"doc":"I. Italic element. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.icon",
"url":11,
"doc":"icon. Pseudo element for an icon.  ! warning The  icon names must be listed in the settings.yml config file under the key  icons . The icon itself is a Unicode character. Parameters      icon: string Name of the icon. text: string, optional,  None Extra text that will be placed in front of the icon. asChar: boolean, optional,  False If  True , just output the icon character. Otherwise, wrap it in a    with all attributes that might have been passed. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.iconx",
"url":11,
"doc":"iconx. Pseudo element for a clickable icon. It will be wrapped in an    .  element or a  if  href is  None . If  href is the empty string, the element will still be wrapped in an    element, but without a  href attribute.  ! warning The  icon names must be listed in the settings.yml config file under the key  icons . The icon itself is a Unicode character. Parameters      icon: string Name of the icon. text: string, optional,  None Extra text that will be placed in front of the icon. href: url, optional,  None Destination of the icon when clicked. Will be left out when equal to the empty string. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.actionButton",
"url":11,
"doc":"Generates an action button to be activated by client side Javascript. It is assumed that the permission has already been checked. Parameters      H: object The  control.html.HtmlElements object name: string The name of the icon as displayed on the button kind: string, optional None The kind of the button, passed on in attribute  kind , can be used by Javascript to identify this button. If  None , the kind is set to the value of the  name parameter. Returns    - string The HTML of the button.",
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
"doc":"INPUT type=\"file\". The input element for uploading files. If the user does not have  update permission, only information about currently uploaded file(s) is presented. But if the user does have upload permission, there will be an additional control to update a new file and there will be controls to delete existing files. Parameters      content: list or tuple The widget handles to cases:  1 single file with a prescribed name.  no prescribed name, lists all files that match the  accept parameter. In the first case,  content is a tuple consisting of  file name  whether the file exists  a url to load the file as image, or None In the second case,  content is a list containing a tuple for each file:  file name  a url to load the file as image, or None And in this case, all files exist. In both cases, a delete control will be added to each file, if allowed. If an image url is present, the contents of the file will be displayed as an img element. accept: string MIME type of uploaded file mayChange: boolean Whether the user is allowed to upload new files and delete existing files. saveUrl: string The url to which the resulting file should be posted. deleteUrl: string The url to use to delete a file, with the understanding that the file name should be appended to it. caption: string basis for tooltips for the upload and delete buttons cls: string, optional  CSS class for the outer element buttonCls: string, optional  CSS class for the buttons wrapped: boolean, optional True Whether the content should be wrapped in a container element. If so, the container element carries a class attribute filled with  cls , and all attributes specified in the  atts argument. This generates a new widget on the page. If False, only the content is passed. Use this if the content of an existing widget has changed and must be inserted in that widget. The outer element of the widget is not changed. Returns    - string(html)",
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
"doc":"TABLE. The table element. Parameters      headers, rows: iterables of iterables An iterable of rows. Each row is a tuple: an iterable of cells, and a dict of atts for the row. Each cell is a tuple: material for the cell, and a dict of atts for the cell.  ! note Cells in normal rows are wrapped in    , cells in header rows go into    . Returns    - string(html)",
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
"doc":"Rows and cells. Parameters      data: iterable of iterables. Rows and cells within them, both with dicts of atts. td: function Funnction for wrapping the cells, typically boiling down to wrapping them in either    or    elements. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.asString",
"url":11,
"doc":"Join an iterable of strings or iterables into a string. And if the value is already a string, return it, and if it is  None return the empty string. The material is recursively joined into a string. Parameters      value: string | iterable | void Every argument in  value may be None, a string, or an iterable. tight: boolean, optional False If True, all material will be joined tightly, with no intervening string. Otherwise, all pieces will be joined with a newline. Returns    - string(html)",
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
"doc":"Datamodel related operations. This class has methods to manipulate various pieces of content in the data sources, and hand it over to higher level objects. It can find out dependencies between related records, and it knows a thing or two about fields. It is instantiated by a singleton object. It has a method which is a factory for  control.datamodel.Field objects, which deal with individual fields. Likewise it has a factory function for  control.datamodel.Upload objects, which deal with file uploads. Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo ."
},
{
"ref":"control.datamodel.Datamodel.relevant",
"url":12,
"doc":"Get a relevant record and the table to which it belongs. A relevant record is either a project record, or an edition record, or the one and only site record. If all optional parameters are None, we look for the site record. If the project parameter is not None, we look for the project record. This is the inverse of  context() . Paramenters      - project: string | ObjectId | AttrDict, optional None The project whose record we need. edition: string | ObjectId | AttrDict, optional None The edition whose record we need. Returns    - tuple  table: string; the table in which the record is found  record id: string; the id of the record  record: AttrDict; the record itself If both project and edition are not None",
"func":1
},
{
"ref":"control.datamodel.Datamodel.context",
"url":12,
"doc":"Get the context of a record. Get the project and edition records to which the record belongs. Parameters      table: string The table in which the record sits. record: string The record. This is the inverse of  relevant() . Returns    - tuple of tuple  (site, project, record) where the members are either None, or a full record",
"func":1
},
{
"ref":"control.datamodel.Datamodel.getDetailRecords",
"url":12,
"doc":"Retrieve the detail records of a master record. It finds all records that have a field containing an id of the given master record. Details are not retrieved recursively, only the direct details of a master are fetched. Parameters      masterTable: string The name of the table in which the master record lives. master: string | ObjectId | AttrDict The master record. Returns    - AttrDict The list of detail records, categorized by detail table in which they occur. The detail tables are the keys, the lists of records in those tables are the values. If the master record cannot be found or if there are no detail records, the empty dict is returned.",
"func":1
},
{
"ref":"control.datamodel.Datamodel.makeField",
"url":12,
"doc":"Make a field object and registers it. An instance of class  control.datamodel.Field is created, geared to this particular field.  ! note \"Idempotent\" If the Field object is already registered, nothing is done. Parameters      key: string Identifier for the field. The configuration for this field will be retrieved using this key. The new field object will be stored under this key. Returns    - object The resulting Field object. It is also added to the  fieldObjects member.",
"func":1
},
{
"ref":"control.datamodel.Datamodel.getFieldObject",
"url":12,
"doc":"Get a field object. Parameters      key: string The key of the field object Returns    - object | void The field object found under the given key, if present, otherwise None",
"func":1
},
{
"ref":"control.datamodel.Datamodel.makeUpload",
"url":12,
"doc":"Make a file upload object and registers it. An instance of class  control.datamodel.Upload is created, geared to this particular field.  ! note \"Idempotent\" If the Upload object is already registered, nothing is done. Parameters      key: string Identifier for the upload. The configuration for this upload will be retrieved using this key. The new upload object will be stored under this key. fileName: string, optional None If present, it indicates that the uploaded file will have this prescribed name. A file name for an upload object may also have been specified in the datamodel configuration. Returns    - object The resulting Upload object. It is also added to the  uploadObjects member.",
"func":1
},
{
"ref":"control.datamodel.Datamodel.getUploadConfig",
"url":12,
"doc":"Get an upload config. Parameters      key: string The key of the upload config Returns    - object | void The upload config found under the given key and file name, if present, otherwise None",
"func":1
},
{
"ref":"control.datamodel.Datamodel.getUploadObject",
"url":12,
"doc":"Get an upload object. Parameters      key: string The key of the upload object fileName: string, optional None The file name of the upload object. If not passed, the file name is derived from the config of the key. Returns    - object | void The upload object found under the given key and file name, if present, otherwise None",
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
"doc":"Give the logical value of the field in a record. Parameters      record: string | ObjectId | AttrDict The record in which the field value is stored. Returns    - any: Whatever the value is that we find for that field. No conversion/casting to other types will be performed. If the field is not present, returns None, without warning.",
"func":1
},
{
"ref":"control.datamodel.Field.bare",
"url":12,
"doc":"Give the bare string value of the field in a record. Parameters      record: string | ObjectId | AttrDict The record in which the field value is stored. Returns    - string: Whatever the value is that we find for that field, converted to string. If the field is not present, returns the empty string, without warning.",
"func":1
},
{
"ref":"control.datamodel.Field.formatted",
"url":12,
"doc":"Give the formatted value of the field in a record. Optionally also puts a caption and/or an edit control. The value retrieved is (recursively) wrapped in HTML, steered by additional argument, as in  control.html.HtmlElements.wrapValue . be applied. If the type is 'text', multiple values will simply be concatenated with newlines in between, and no extra classes will be applied. Instead, a markdown formatter is applied to the result. For other types: If the value is an iterable, each individual value is wrapped in a span to which an (other) extra CSS class may be applied. Parameters      table: string The table from which the record is taken record: string | ObjectId | AttrDict The record in which the field value is stored. level: integer, optional None The heading level in which a caption will be placed. If None, no caption will be placed. If 0, the caption will be placed in a span. editable: boolean, optional False Whether the field is editable by the current user. If so, edit controls are provided. outerCls: string optional \"fieldouter\" If given, an extra CSS class for the outer element that wraps the total value. Only relevant if the type is not 'text' innerCls: string optional \"fieldinner\" If given, an extra CSS class for the inner elements that wrap parts of the value. Only relevant if the type is not 'text' Returns    - string: Whatever the value is that we find for that field, converted to HTML. If the field is not present, returns the empty string, without warning.",
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
"doc":"Handle upload business. An upload is like a field of type 'file'. The name of the uploaded file is stored in a record in MongoDb. The contents of the file is stored on the file system. A Upload object does not correspond with an individual field in a record. It represents a  column , i.e. a set of fields with the same name in all records of a collection. First of all there is a method to retrieve the file name of an upload from a specific record. Then there are methods to deliver those values, either bare or formatted, to produce widgets to upload or delete the corresponding files. How to do this is steered by the specification of the upload by keys and values that are stored in this object. All upload access should be guarded by the authorisation rules. Parameters      kwargs: dict Upload configuration arguments. The following parts of the upload configuration should be present:  table ,  accept , while  caption ,  fileName ,  show are optional."
},
{
"ref":"control.datamodel.Upload.getDir",
"url":12,
"doc":"Give the path to the file in question. The path can be used to build the static url and the save url. It does not contain the file name. If the path is non-empty, a \"/\" will be appended. Parameters      record: string | ObjectId | AttrDict The record relevant to the upload",
"func":1
},
{
"ref":"control.datamodel.Upload.formatted",
"url":12,
"doc":"Give the formatted value of a file field in a record. Optionally also puts an upload control. Parameters      record: string | ObjectId | AttrDict The record relevant to the upload mayChange: boolean, optional False Whether the file may be changed. If so, an upload widget is supplied, wich contains a a delete button. bust: string, optional None If not None, the image url of the file whose name is passed in  bust is made unique by adding the current time to it. This is a cache buster. wrapped: boolean, optional True Whether the content should be wrapped in a container element. See  control.html.HtmlElements.finput() . Returns    - string The name of the uploaded file(s) and/or an upload control.",
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
"doc":"Indicates the directory where the actual file will be saved. Possibe values:   site : top level of the working data directory of the site   project : project directory of the project in question   edition : edition directory of the project in question"
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
"ref":"control.datamodel.Upload.multiple",
"url":12,
"doc":"Whether multiple files of this type may be uploaded."
},
{
"ref":"control.datamodel.Upload.fileName",
"url":12,
"doc":"The name of the file once it is uploaded. The file name for the upload can be passed when the file name is known in advance. In that case, a file that is uploaded in this upload widget, will get this as prescribed file name, regardless of the file name in the upload request. Without a file name, the upload widget will show all existing files conforming to the  accept setting, and will have a control to upload a new file."
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
"doc":"Reads secrets used in encryption and decryption.",
"func":1
},
{
"ref":"control.authoidc.AuthOidc.prepare",
"url":13,
"doc":"Injects the OIDC module into the main app.",
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
"doc":"Making responses that can be displayed as web pages. This class has methods that correspond to routes in the app, for which they get the data (using  control.content.Content ), which gets then wrapped in HTML. It is instantiated by a singleton object. Most methods generate a response that contains the content of a complete page. For those methods we do not document the return value. Some methods return something different. If so, it the return value will be documented. Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Viewers: object Singleton instance of  control.viewers.Viewers . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo . Collect: object Singleton instance of  control.collect.Collect . Content: object Singleton instance of  control.content.Content . Auth: object Singleton instance of  control.auth.Auth ."
},
{
"ref":"control.pages.Pages.collect",
"url":14,
"doc":"Data reset: collect the example data again.",
"func":1
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
"ref":"control.pages.Pages.admin",
"url":14,
"doc":"The page with the list of projects, editions, and users.",
"func":1
},
{
"ref":"control.pages.Pages.createProject",
"url":14,
"doc":"Creates a project and shows the new project. The current user is linked to this project as organiser.",
"func":1
},
{
"ref":"control.pages.Pages.project",
"url":14,
"doc":"The landing page of a project. Parameters      project: string | ObjectId | AttrDict The project in question.",
"func":1
},
{
"ref":"control.pages.Pages.deleteProject",
"url":14,
"doc":"Deletes a project. Parameters      project: string | ObjectId | AttrDict The project in question.",
"func":1
},
{
"ref":"control.pages.Pages.createEdition",
"url":14,
"doc":"Inserts an edition into a project and shows the new edition. The current user is linked to this edition as editor. Parameters      project: string | ObjectId | AttrDict The project to which the edition belongs.",
"func":1
},
{
"ref":"control.pages.Pages.edition",
"url":14,
"doc":"The landing page of an edition, possibly with a scene marked as active. An edition knows the scene it should display and the viewer that was used to create the scene. If action is not None, its value determines which viewer will be loaded in the 3D viewer. It is dependent on the parameters and/or defaults in which viewer/version/mode. If version is not None, this will override the default version. Parameters      edition: string | ObjectId | AttrDict The editionin quesion. From the edition record we can find the project too. version: string, optional None The viewer version to use. action: string, optional None The mode in which the viewer is to be used ( read or  update ).",
"func":1
},
{
"ref":"control.pages.Pages.deleteEdition",
"url":14,
"doc":"Deletes an edition. Parameters      edition: string | ObjectId | AttrDict The edition in question.",
"func":1
},
{
"ref":"control.pages.Pages.viewerFrame",
"url":14,
"doc":"The page loaded in an iframe where a 3D viewer operates. Parameters      edition: string | ObjectId | AttrDict The edition that is shown. version: string | None The version to use. action: string | None The mode in which the viewer is to be used ( read or  update ).",
"func":1
},
{
"ref":"control.pages.Pages.viewerResource",
"url":14,
"doc":"Components requested by viewers. This is the javascript code, the css, and other resources that are part of the 3D viewer software. Parameters      path: string Path on the file system under the viewers base directory where the resource resides. Returns    - response The response consists of the contents of the file plus headers derived from the path. If the file does not exists, a 404 is returned.",
"func":1
},
{
"ref":"control.pages.Pages.fileData",
"url":14,
"doc":"Data content requested directly from the file repository. This is  the material requested by the viewers: the scene json itself and additional resources, that are part of the user contributed content that is under control of the viewer: annotations, media, etc.  icons for the site, projects, and editions Parameters      path: string Path on the file system under the data directory where the resource resides. The path is relative to the project, and, if given, the edition. project: string | ObjectId | AttrDict The id of a project under which the resource is to be found. If None, it is site-wide material. edition: string | ObjectId | AttrDict If not None, the name of an edition under which the resource is to be found. Returns    - response The response consists of the contents of the file plus headers derived from the path. If the file does not exists, a 404 is returned.",
"func":1
},
{
"ref":"control.pages.Pages.upload",
"url":14,
"doc":"Upload a file. Parameters      record: string | ObjectId | AttrDict The context record of the upload key: string The key of the upload path: string The save location for the file givenFileName: string, optional None The name of the file as which the uploaded file will be saved; if is None, the file will be saved with the name from the request.",
"func":1
},
{
"ref":"control.pages.Pages.deleteFile",
"url":14,
"doc":"Delete a file. Parameters      record: string | ObjectId | AttrDict The context record of the upload. key: string The key of the upload. path: string The location of the file. givenFileName: string, optional None The name of the file.",
"func":1
},
{
"ref":"control.pages.Pages.authWebdav",
"url":14,
"doc":"Authorises a webdav request. When a viewer makes a WebDAV request to the server, that request is first checked here for authorisation. See  control.webdavapp.dispatchWebdav() . Parameters      edition: string | ObjectId | AttrDict The edition in question. path: string The path relative to the directory of the edition. action: string The operation that the WebDAV request wants to do on the data ( read or  update ). Returns    - boolean Whether the action is permitted on ths data by the current user.",
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
"ref":"control.pages.Pages.navigation",
"url":14,
"doc":"Generates the navigation controls. Especially the tab bar. Parameters      url: string Initial part of the url on the basis of which one of the tabs can be made active. Returns    - string The HTML of the navigation.",
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
"doc":"Retrieving content from database and file system. This class has methods to retrieve various pieces of content from the data sources, and hand it over to the  control.pages.Pages class that will compose a response out of it. It is instantiated by a singleton object. Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Viewers: object Singleton instance of  control.viewers.Viewers . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo ."
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
"ref":"control.content.Content.getEditions",
"url":15,
"doc":"Get the list of the editions of a project. Well, only if the project is visible to the current user. See  Content.getProjects() . Editions are each displayed by means of an icon and a title. Both link to a landing page for the edition. Parameters      project: string | ObjectId | AttrDict The project in question. Returns    - string A list of captions of the editions of the project, wrapped in a HTML string.",
"func":1
},
{
"ref":"control.content.Content.getScene",
"url":15,
"doc":"Get the scene of an edition of a project. Well, only if the current user is authorised. A scene is displayed by means of an icon and a row of buttons. If action is not None, the scene is loaded in a specific version of the viewer in a specific mode ( read or  read ). The edition knows which viewer to choose. Which version and which mode are used is determined by the parameters. If the parameters do not specify values, sensible defaults are chosen. Parameters      edition: string | ObjectId | AttrDict The edition in question. version: string, optional None The version of the chosen viewer that will be used. If no version or a non-existing version are specified, the latest existing version for that viewer will be chosen. action: string, optional  read The mode in which the viewer should be opened. If the mode is  update , the viewer is opened in edit mode. All other modes lead to the viewer being opened in read-only mode. Returns    - string A caption of the scene of the edition, with possibly a frame with the 3D viewer showing the scene. The result is wrapped in a HTML string.",
"func":1
},
{
"ref":"control.content.Content.getAdmin",
"url":15,
"doc":"Get the list of relevant projects, editions and users. Admin users get the list of all users. Normal users get the list of users associated with  the project of which they are organiser  the editions of which they are editor or reviewer Guests and not-logged-in users cannot see any user. If the user has rights to modify the association between users and projects/editions, he will get the controls to do so. Returns    - string",
"func":1
},
{
"ref":"control.content.Content.createProject",
"url":15,
"doc":"Creates a new project. Parameters      site: AttrDict | string record that represents the site, or its id. It acts as a master record for all projects. Returns    - ObjectId The id of the new project.",
"func":1
},
{
"ref":"control.content.Content.deleteProject",
"url":15,
"doc":"Deletes a project. Parameters      project: string | ObjectId | AttrDict The project in question.",
"func":1
},
{
"ref":"control.content.Content.createEdition",
"url":15,
"doc":"Creates a new edition. Parameters      project: AttrDict | string record that represents the maste project, or its id. Returns    - ObjectId The id of the new edition.",
"func":1
},
{
"ref":"control.content.Content.deleteEdition",
"url":15,
"doc":"Deletes an edition. Parameters      edition: string | ObjectId | AttrDict The edition in question.",
"func":1
},
{
"ref":"control.content.Content.getViewInfo",
"url":15,
"doc":"Gets viewer-related info that an edition is made with. Parameters      edition: string | ObjectId | AttrDict The edition record. Returns    - tuple of string  The name of the viewer  The name of the scene",
"func":1
},
{
"ref":"control.content.Content.saveValue",
"url":15,
"doc":"Saves a value of into a record. A record contains a document, which is a (nested) dict. A value is inserted somewhere (deep) in that dict. The value is given by the request. Where exactly is given by a path that is stored in the field information, which is accessible by the key. Parameters      table: string The relevant table. record: string | ObjectId | AttrDict | void The relevant record. key: string an identifier for the meta data field. Returns    - dict Contains the following keys:   status : whether the save action was successful   messages : messages issued during the process   readonly : the html of the updated formatted value, this will replace the currently displayed value.",
"func":1
},
{
"ref":"control.content.Content.saveRole",
"url":15,
"doc":"Saves a role into a user or cross table record. The role is given by the request. Parameters      user: string The eppn of the user. table: string | void The relevant table. If not None, it indicates whether we are updating site-wide roles, otherwise project/edition roles. recordId: string | void The id of the relevant record. If not None, it is a project/edition record Id, which can be used to locate the cross record between the user collection and the project/edition record where the user's role is stored. If None, the user's role is inside the user record. Returns    - dict Contains the following keys:   status : whether the save action was successful   messages : messages issued during the process   updated : if the action was successful, all user management info will be passed back and will replace the currently displayed material.",
"func":1
},
{
"ref":"control.content.Content.linkUser",
"url":15,
"doc":"Links a user in certain role to a project/edition record. The user and role are given by the request. Parameters      table: string The relevant table. recordId: string The id of the relevant record, which can be used to locate the cross record between the user collection and the project/edition record where the user's role is stored. Returns    - dict Contains the following keys:   status : whether the save action was successful   messages : messages issued during the process   updated : if the action was successful, all user management info will be passed back and will replace the currently displayed material.",
"func":1
},
{
"ref":"control.content.Content.getValue",
"url":15,
"doc":"Retrieve a metadata value. Metadata sits in a big, potentially deeply nested dictionary of keys and values. These locations are known to the system (based on  fields.yml ). This function retrieves the information from those known locations. If a value is in fact composed of multiple values, it will be handled accordingly. If the user may edit the value, an edit button is added. Parameters      key: string an identifier for the meta data field. table: string The relevant table. record: string | ObjectId | AttrDict | void The relevant record. level: string, optional None The heading level with which the value should be formatted.   0 : No heading level   None : no formatting at all bare: boolean, optional None Get the bare value, without HTML wrapping and without buttons. Returns    - string It is assumed that the metadata value that is addressed exists. If not, we return the empty string.",
"func":1
},
{
"ref":"control.content.Content.getValues",
"url":15,
"doc":"Puts several pieces of metadata on the web page. Parameters      fieldSpecs: string  , -separated list of fieldSpecs table: string The relevant table record: string | ObjectId | AttrDict | void The relevant record Returns    - string The join of the individual results of retrieving metadata value.",
"func":1
},
{
"ref":"control.content.Content.getUpload",
"url":15,
"doc":"Display the name and/or upload controls of an uploaded file. The user may upload model files and a scene file to an edition, and various png files as icons for projects, edtions, and scenes. Here we produce the control to do so. Only if the user has  update authorisation, an upload/delete widget will be returned. Parameters      record: string | ObjectId | AttrDict | void The relevant record. key: string an identifier for the upload field. fileName: string, optional None If present, it indicates that the uploaded file will have this prescribed name. A file name for an upload object may also have been specified in the datamodel configuration. bust: string, optional None If not None, the image url of the file whose name is passed in  bust is made unique by adding the current time to it. That will bust the cache for the image, so that uploaded images replace the existing images. This is useful when this function is called to provide udated content for an file upload widget after it has been used to successfully upload a file. The file name of the uploaded file is known, and that is the one that gets a cache buster appended. wrapped: boolean, optional True Whether the content should be wrapped in a container element. See  control.html.HtmlElements.finput() . Returns    - string The name of the file that is currently present, or the indication that no file is present. If the user has edit permission for the edition, we display widgets to upload a new file or to delete the existing file.",
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
"doc":"Gets a data file from the file system. All data files are located under a specific directory on the server. This is the data directory. Below that the files are organized by projects and editions. Projects and editions corresponds to records in tables in MongoDB. Parameters      path: string The path of the data file within site/project/edition directory within the data directory. project: string | ObjectId | AttrDict The id of the project in question. edition: string | ObjectId | AttrDict The id of the edition in question. Returns    - string The full path of the data file, if it exists. Otherwise, we raise an error that will lead to a 404 response.",
"func":1
},
{
"ref":"control.content.Content.breadCrumb",
"url":15,
"doc":"Makes a link to the landing page of a project. Parameters      project: string | ObjectId | AttrDict The project in question.",
"func":1
},
{
"ref":"control.content.Content.saveFile",
"url":15,
"doc":"Saves a file in the context given by a record. Parameters      record: string | ObjectId | AttrDict | void The relevant record. key: string The upload key path: string The path from the context directory to the file fileName: string Name of the file to be saved as mentioned in the request. givenFileName: string, optional None The name of the file as which the uploaded file will be saved; if None, the file will be saved with the name from the request. Return    response A json response with the status of the save operation:  a boolean: whether the save succeeded  a message: messages to display  content: new content for an upload control (only if successful)",
"func":1
},
{
"ref":"control.content.Content.deleteFile",
"url":15,
"doc":"Deletes a file in the context given by a record. Parameters      record: string | ObjectId | AttrDict | void The relevant record. key: string The upload key path: string The path from the context directory to the file fileName: string Name of the file to be saved as mentioned in the request. givenFileName: string, optional None The name of the file as which the uploaded file will be saved; if None, the file will be saved with the name from the request. Return    response A json response with the status of the save operation:  a boolean: whether the save succeeded  a message: messages to display  content: new content for an upload control (only if successful)",
"func":1
},
{
"ref":"control.content.Content.relevant",
"url":12,
"doc":"Get a relevant record and the table to which it belongs. A relevant record is either a project record, or an edition record, or the one and only site record. If all optional parameters are None, we look for the site record. If the project parameter is not None, we look for the project record. This is the inverse of  context() . Paramenters      - project: string | ObjectId | AttrDict, optional None The project whose record we need. edition: string | ObjectId | AttrDict, optional None The edition whose record we need. Returns    - tuple  table: string; the table in which the record is found  record id: string; the id of the record  record: AttrDict; the record itself If both project and edition are not None",
"func":1
},
{
"ref":"control.content.Content.context",
"url":12,
"doc":"Get the context of a record. Get the project and edition records to which the record belongs. Parameters      table: string The table in which the record sits. record: string The record. This is the inverse of  relevant() . Returns    - tuple of tuple  (site, project, record) where the members are either None, or a full record",
"func":1
},
{
"ref":"control.content.Content.getDetailRecords",
"url":12,
"doc":"Retrieve the detail records of a master record. It finds all records that have a field containing an id of the given master record. Details are not retrieved recursively, only the direct details of a master are fetched. Parameters      masterTable: string The name of the table in which the master record lives. master: string | ObjectId | AttrDict The master record. Returns    - AttrDict The list of detail records, categorized by detail table in which they occur. The detail tables are the keys, the lists of records in those tables are the values. If the master record cannot be found or if there are no detail records, the empty dict is returned.",
"func":1
},
{
"ref":"control.content.Content.makeField",
"url":12,
"doc":"Make a field object and registers it. An instance of class  control.datamodel.Field is created, geared to this particular field.  ! note \"Idempotent\" If the Field object is already registered, nothing is done. Parameters      key: string Identifier for the field. The configuration for this field will be retrieved using this key. The new field object will be stored under this key. Returns    - object The resulting Field object. It is also added to the  fieldObjects member.",
"func":1
},
{
"ref":"control.content.Content.getFieldObject",
"url":12,
"doc":"Get a field object. Parameters      key: string The key of the field object Returns    - object | void The field object found under the given key, if present, otherwise None",
"func":1
},
{
"ref":"control.content.Content.makeUpload",
"url":12,
"doc":"Make a file upload object and registers it. An instance of class  control.datamodel.Upload is created, geared to this particular field.  ! note \"Idempotent\" If the Upload object is already registered, nothing is done. Parameters      key: string Identifier for the upload. The configuration for this upload will be retrieved using this key. The new upload object will be stored under this key. fileName: string, optional None If present, it indicates that the uploaded file will have this prescribed name. A file name for an upload object may also have been specified in the datamodel configuration. Returns    - object The resulting Upload object. It is also added to the  uploadObjects member.",
"func":1
},
{
"ref":"control.content.Content.getUploadConfig",
"url":12,
"doc":"Get an upload config. Parameters      key: string The key of the upload config Returns    - object | void The upload config found under the given key and file name, if present, otherwise None",
"func":1
},
{
"ref":"control.content.Content.getUploadObject",
"url":12,
"doc":"Get an upload object. Parameters      key: string The key of the upload object fileName: string, optional None The file name of the upload object. If not passed, the file name is derived from the config of the key. Returns    - object | void The upload object found under the given key and file name, if present, otherwise None",
"func":1
},
{
"ref":"control.admin",
"url":16,
"doc":""
},
{
"ref":"control.admin.Admin",
"url":16,
"doc":"Get the list of relevant projects, editions and users. Admin users get the list of all users. Normal users get the list of users associated with  the project of which they are organiser  the editions of which they are editor or reviewer Guests and not-logged-in users cannot see any user. If the user has rights to modify the association between users and projects/editions, he will get the controls to do so. Upon initialization the project/edition/user data will be read and assembled in a form ready for generating html.  Overview of assembled data  projects All project records in the system, keyed by id. If a project has editions, the editions are available under key  editions as a dict of edition records keyed by id. If a project has users, the users are available under key  users as a dict keyed by user id and valued by the user records. If an edition has users, the users are available under key  users as a dict keyed by role and then by user id and valued by a tuple of the user record and his role.  users All user records in the system, keyed by id.  myIds All project and edition ids to which the current user has a relationship. It is a dict with keys  project and  edition and the values are sets of ids."
},
{
"ref":"control.admin.Admin.update",
"url":16,
"doc":"Reread the collections of users, projects, editions. Typically needed when you have used an admin function to perform a user administration action. This may change the permissions and hence the visiblity of projects and editions. It also changes the possible user management actions in the future.",
"func":1
},
{
"ref":"control.admin.Admin.authUser",
"url":16,
"doc":"Check whether a user may change the role of another user. The question are: \"which  other site-wide roles can the current user assign to the other user?\" (when no table or record are given). \"which project/edition scoped roles can the current user assign to or remove from the other user with respect to the relevant record in the given table?\". Note that the current site-wide role of the other user is never included in the set of resulting roles. There are also additional business rules. This function will return the empty set if these rules are violated.  Business rules  Users have exactly one site-wise role.  Users may demote themselves.  Users may not promote themselves unless  . see later.  Users may have zero or one project/edition-scoped role per project/edition  When assigning new site-wide or project-scoped or edition-scoped roles, these roles must be valid roles for that scope.  When assigning a new site-wide role, None is not one of the possible new roles: you cannot change the status of an authenticated user to \"not logged in\".  When assigning project/edition scoped roles, removing such a role from a user for a certain project/edition means that the other user is removed from that project or edition.  Roles are ranked in power. Users with a higher role are also authorised to all things for which lower roles give authorisation. The site-wide roles are ranked as:  root - admin - user - guest - not logged in  The project/edition roles are ranked as:  (project) organiser - (edition) editor - (edition) reviewer  Site-wide power does not automatically carry over to project/edition-scoped power.  Users cannot promote or demote people that are currently as powerful as themselves.  In normal cases there is exactly one root, but:  If a situation occurs that there is no root and no admin, any authenticated user my grab the role of admin.  If a situation occurs that there is no root, any admin may grab the role of root.  Roots may appoint admins.  Roots and admins may change site-wide roles.  Roots and admins may appoint project organisers, but may not assign edition-scoped roles.  Project organisers may appoint edition editors and reviewers.  Edition editors may appoint edition reviewers.  However, roots and admins may also be project organisers and edition editors for some projects and some editions.  Normal users and guests can not administer site-wide roles.  Guests can not be put in project/edition-scoped roles. Parameters      otherUser: string | void the other user as string (eppn) If None, the question is: what are the roles in which an other user may be put wrt to this project/edition? table: string, optional None the relevant table:  project or  edition ; this is the table in which the record sits relative to which the other user will be assigned a role. If None, the role to be assigned is a site wide role. record: ObjectId | AttrDict, optional None the relevant record; it is the record relative to which the other user will be assigned an other role. If None, the role to be assigned is a site wide role. Returns    - boolean, frozenset The boolean indicates whether the current user may modify the role of the target user. The frozenset is the set of assignable roles to the other user by the current user with respect to the given table and record or site-wide. If the boolean is false, the frozenset is empty. But if the frozenset is empty it might be the case that the current user is allowed to remove the role of the target user.",
"func":1
},
{
"ref":"control.admin.Admin.wrap",
"url":16,
"doc":"Produce a list of projects and editions and users for root/admin usage. The first overview shows all projects and editions with their associated users and roles. Only items that are relevant to the user are shown. If the user is authorised to change associations between users and items, they will be editable. The second overview is for admin/roots only. It shows a list of users and their site-wide roles, which can be changed.",
"func":1
},
{
"ref":"control.admin.Admin.wrapProject",
"url":16,
"doc":"Generate HTML for a project in admin view. Parameters      project: AttrDict A project record myOnly: boolean, optional False Whether to show only the editions in the project that are associated with the current user. Returns    - string The HTML",
"func":1
},
{
"ref":"control.admin.Admin.wrapEdition",
"url":16,
"doc":"Generate HTML for an edition in admin view. Parameters      edition: AttrDict An edition record Returns    - string The HTML",
"func":1
},
{
"ref":"control.admin.Admin.wrapUsers",
"url":16,
"doc":"Generate HTML for a list of users. It is dependent on the value of table/record whether it is about the users of a specific project/edition or the site-wide users. Parameters      itemRoles: dict Dictionary keyed by the possible roles and valued by the description of that role. table: string, optional None Either  project or  edition , indicates what users we are listing: related to a project or to an edition. record: AttrDict, optional None If  table is passed and not None, here is the specific project or edition whose users should be listed. theseUsers: dict, optional None If table/record is not specified, you can specify users here. If this parameter is also None, then all users in the system are taken. Otherwise you have to specify a dict, keyed by user eppns and valued by tuples consisting of a user record and a role. Returns    - string The HTML",
"func":1
},
{
"ref":"control.admin.Admin.wrapLinkUser",
"url":16,
"doc":"Generate HTML to add a user in a specified role. Parameters      roles: string | void The choice of roles that a new user can get. itemRoles: dict Dictionary keyed by the possible roles and valued by the description of that role. table: string Either None or  project or  edition , indicates to what we are linking users: site-wide users or users related to a project or to an edition. recordId: ObjectId or None Either None or the id of a project or edition, corresponding to the  table parameter. Returns    - string The HTML",
"func":1
},
{
"ref":"control.admin.Admin.wrapUser",
"url":16,
"doc":"Generate HTML for a single user and his role. Parameters      u: string The eppn of the user. uRecord: AttrDict The user record. role: string | void The actual role of the user, or None if the user has no role. editable: boolean Whether the current user may change the role of this user. otherRoles: frozenset The other roles that the user may get from the current user. itemRoles: dict Dictionary keyed by the possible roles and valued by the description of that role. table: string Either None or  project or  edition , indicates what users we are listing: site-wide users or users related to a project or to an edition. recordId: ObjectId or None Either None or the id of a project or edition, corresponding to the  table parameter. Returns    - string The HTML",
"func":1
},
{
"ref":"control.admin.Admin.wrapRole",
"url":16,
"doc":"Generate HTML for a role. This may or may not be an editable widget, depending on whether there are options to choose from. Site-wide users have a single site-wide role. But project/edition users can have zero or one role wrt projects/editions. Parameters      u: string The eppn of the user. itemRoles: dict Dictionary keyed by the possible roles and valued by the description of that role. role: string | void The actual role of the user, or None if the user has no role. editable: boolean Whether the current user may change the role of this user. otherRoles: frozenset The other roles that the target user may be assigned by the current user. table: string Either None or  project or  edition , indicates what users we are listing: site-wide users or users related to a project or to an edition. recordId: ObjectId or None Either None or the id of a project or edition, corresponding to the  table parameter. Returns    - string The HTML",
"func":1
},
{
"ref":"control.admin.Admin.saveRole",
"url":16,
"doc":"Saves a role into a user or cross table record. It will be checked whether the new role is valid, and whether the user has permission to perform this role assignment. Parameters      u: string The eppn of the user. newRole: string | void The new role for the target user. None means: the target user will lose his role. table: string Either None or  project or  edition , indicates what users we are listing: site-wide users or users related to a project or to an edition. recordId: ObjectId or None Either None or the id of a project or edition, corresponding to the  table parameter. Returns    - dict with keys:   stat : indicates whether the save may proceed;   messages : list of messages for the user,   updated : new content for the user managment div.",
"func":1
},
{
"ref":"control.admin.Admin.linkUser",
"url":16,
"doc":"Links a user in certain role to a project/edition record. It will be checked whether the new role is valid, and whether the user has permission to perform this role assignment. If the user is already linked to that project/edition, his role will be updated, otherwise a new link will be created. Parameters      u: string The eppn of the target user. newRole: string The new role for the target user. table: string Either  project or  edition . recordId: ObjectId The id of a project or edition, corresponding to the  table parameter. Returns    - dict with keys:   stat : indicates whether the save may proceed;   messages : list of messages for the user,   updated : new content for the user managment div.",
"func":1
},
{
"ref":"control.messages",
"url":17,
"doc":""
},
{
"ref":"control.messages.Messages",
"url":17,
"doc":"Sending messages to the user and the server log. This class is instantiated by a singleton object. It has methods to issue messages to the screen of the webuser and to the log for the sysadmin. They distinguish themselves by the  severity :  debug ,  info ,  warning ,  error . There is also  plain , a leaner variant of  info . All those methods have two optional parameters:  logmsg and  msg . The behaviors of these methods are described in detail in the  Messages.message() function.  ! hint \"What to disclose?\" You can pass both parameters, which gives you the opportunity to make a sensible distinction between what you tell the web user (not much) and what you send to the log (the gory details). Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings ."
},
{
"ref":"control.messages.Messages.setFlask",
"url":17,
"doc":"Enables messaging to the web interface.",
"func":1
},
{
"ref":"control.messages.Messages.debugAdd",
"url":17,
"doc":"Adds a quick debug method to a destination object. The result of this method is that instead of saying   self.Messages.debug (logmsg=\"blabla\")   you can say   self.debug (\"blabla\")   It is recommended that in each object where you store a handle to Messages, you issue the statement   Messages.addDebug(self)  ",
"func":1
},
{
"ref":"control.messages.Messages.debug",
"url":17,
"doc":"Issue a debug message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.error",
"url":17,
"doc":"Issue an error message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.warning",
"url":17,
"doc":"Issue a warning message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.info",
"url":17,
"doc":"Issue a informational message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.plain",
"url":17,
"doc":"Issue a informational message, without bells and whistles. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.message",
"url":17,
"doc":"Workhorse to issue a message in a variety of ways. It can issue log messages and screen messages. Messages passed in  msg go to the web interface, the ones passed in  logmsg go to the log. If there is not yet a web interface,  msg messages are suppressed if there is also a  logmsg , otherwise they will be directed to the log as well. Parameters      tp: string The severity of the message. There is a fixed number of types:   debug Messages are prepended with  DEBUG:  . Log messages go to stderr. Messages will only show up on the web page if the app runs in debug mode.   plain Messages are not prepended with anything. Log messages go to standard output.   info Messages are prepended with  INFO:  . Log messages go to standard output.   warning Messages are prepended with  WARNING:  . Log messages go to standard error.   error Messages are prepended with  ERROR:  . Log messages go to standard error. It also raises an exception, which will lead to a 404 response (if flask is running, that is). But this stopping can be prevented by passing  stop=False . msg: string | void If not None, it is the contents of a screen message. This happens by the built-in  flash method of Flask. logmsg: string | void If not None, it is the contents of a log message. stop: boolean, optional True If False, an error message will not lead to a stop.",
"func":1
},
{
"ref":"control.messages.Messages.client",
"url":17,
"doc":"Adds javascript code whose execution displays a message. Parameters      tp, msg: string, string As in  message() replace: boolean, optional False If True, clears all previous messages. Returns    - dict an onclick attribute that can be added to a link element.",
"func":1
},
{
"ref":"control.messages.Messages.onFlask",
"url":17,
"doc":"Whether the webserver is running. If False, mo messages will be sent to the screen of the webuser, instead those messages end up in the log. This is useful in the initial processing that takes place before the flask app is started."
},
{
"ref":"control.environment",
"url":18,
"doc":""
},
{
"ref":"control.environment.var",
"url":18,
"doc":"Retrieves the value of an environment variable. Parameters      name: string The name of the environment variable Returns    - string | void If the variable does not exist, None is returned.",
"func":1
},
{
"ref":"control.app",
"url":19,
"doc":""
},
{
"ref":"control.app.appFactory",
"url":19,
"doc":"Sets up the main flask app. The main task here is to configure routes, i.e. mappings from url-patterns to functions that create responses  ! note \"WebDAV enabling\" This flask app will later be combined with a webdav app, so that the combined app has the business logic of the main app but can also handle webdav requests. The routes below contain a few patterns that are used for authorising WebDAV calls: the onses starting with  /auth and  /cannot . See also  control.webdavapp . Parameters      objects a slew of objects that set up the toolkit with which the app works: settings, messaging and logging, MongoDb connection, 3d viewer support, higher level objects that can fetch chunks of content and distribute it over the web page. Returns    - object A WebDAV-enabled flask app, which is a wsgi app.",
"func":1
},
{
"ref":"control.viewers",
"url":20,
"doc":""
},
{
"ref":"control.viewers.Viewers",
"url":20,
"doc":"Knowledge of the installed 3D viewers. This class knows which (versions of) viewers are installed, and has the methods to invoke them. It is instantiated by a singleton object. Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo ."
},
{
"ref":"control.viewers.Viewers.addAuth",
"url":20,
"doc":"Give this object a handle to the Auth object. The Viewers and Auth objects need each other, so one of them must be given the handle to the other after initialization.",
"func":1
},
{
"ref":"control.viewers.Viewers.check",
"url":20,
"doc":"Checks whether a viewer version exists. Given a viewer and a version, it is looked up whether the code is present. If not, reasonable defaults returned instead by default. Parameters      viewer: string The viewer in question. version: string The version of the viewer in question. Returns    - string | void The version is returned unmodified if that viewer version is supported. If the viewer is supported, but not the version, the default version of that viewer is taken, if there is a default version, otherwise the latest supported version. If the viewer is not supported, None is returned.",
"func":1
},
{
"ref":"control.viewers.Viewers.getFrame",
"url":20,
"doc":"Produces a set of buttons to launch 3D viewers for a scene. Parameters      edition: string | ObjectId | AttrDict The edition in question. actions: iterable of string The actions for which we have to create buttons. Typically  read and possibly also  update . Actions that are not recognized as viewer actions will be filtered out, such as  create and  delete . viewer: string The viewer in which the scene is currently loaded. versionActive: string | void The version of the viewer in which the scene is currently loaded, if any, otherwise None actionActive: string | void The mode in which the scene is currently loaded in the viewer ( read or  update ), if any, otherwise None Returns    - string The HTML that represents the buttons.",
"func":1
},
{
"ref":"control.viewers.Viewers.genHtml",
"url":20,
"doc":"Generates the HTML for the viewer page that is loaded in an iframe. When a scene is loaded in a viewer, it happens in an iframe. Here we generate the complete HTML for such an iframe. Parameters      urlBase: string The first part of the root url that is given to the viewer. The viewer code uses this to retrieve additional information. The root url will be completed with the  action and the  viewer . sceneFile: string The name of the scene file in the file system. viewer: string The chosen viewer. version: string The chosen version of the viewer. action: string The chosen mode in which the viewer is launched ( read or  update ). Returns    - string The HTML for the iframe.",
"func":1
},
{
"ref":"control.viewers.Viewers.getRoot",
"url":20,
"doc":"Composes the root url for a viewer. The root url is passed to a viewer instance as the url that the viewer can use to fetch its data. It is not meant for the static data that is part of the viewer software, but for the model related data that the viewer is going to display. See  getStaticRoot() for the url meant for getting parts of the viewer software. Parameters      urlBase: string The first part of the root url, depending on the project and edition. action: string The mode in which the viewer is opened. Depending on the mode, the viewer code may communicate with the server with different urls. For example, for the voyager, the  read mode (voyager-explorer) uses ordinary HTTP requests, but the  update mode (voyager-story) uses WebDAV requests. So this app points voyager-explorer to a root url starting with  /data , and voyager-story to a root url starting with  /webdav . These prefixes of the urls can be configured per viewer in the viewer configuration in  yaml/viewers.yml .",
"func":1
},
{
"ref":"control.viewers.Viewers.getStaticRoot",
"url":20,
"doc":"Composes the static root url for a viewer. The static root url is passed to a viewer instance as the url that the viewer can use to fetch its assets. It is not meant for the model related data, but for the parts of the viewer software that it needs to get from the server. See  getRoot() for the url meant for getting model-related data. Parameters      urlBase: string The first part of the root url, depending on the project and edition. action: string The mode in which the viewer is opened. Depending on the mode, the viewer code may communicate with the server with different urls. For example, for the voyager, the  read mode (voyager-explorer) uses ordinary HTTP requests, but the  update mode (voyager-story) uses WebDAV requests. So this app points voyager-explorer to a root url starting with  /data , and voyager-story to a root url starting with  /webdav . These prefixes of the urls can be configured per viewer in the viewer configuration in  yaml/viewers.yml .",
"func":1
},
{
"ref":"control.wrap",
"url":21,
"doc":""
},
{
"ref":"control.wrap.Wrap",
"url":21,
"doc":"Wrap concepts into HTML. This class knows how to wrap several higher-level concepts into HTML, such as projects, editions and users, depending on specific purposes, such as showing widgets to manage projects and editions. It is instantiated by a singleton object. Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Viewers: object Singleton instance of  control.viewers.Viewers ."
},
{
"ref":"control.wrap.Wrap.addAuth",
"url":21,
"doc":"Give this object a handle to the Auth object. The Wrap and Auth objects need each other, so one of them must be given the handle to the other after initialization.",
"func":1
},
{
"ref":"control.wrap.Wrap.addContent",
"url":21,
"doc":"Give this object a handle to the Content object. The Wrap and Content objects need each other, so one of them must be given the handle to the other after initialization.",
"func":1
},
{
"ref":"control.wrap.Wrap.projectsMain",
"url":21,
"doc":"Wrap the list of projects for the main display. Parameters      site: AttrDict The record that corresponds to the site as a whole. It acts as a master record of the projects. projects: list of AttrDict The project records. Returns    - string The HTML of the project list",
"func":1
},
{
"ref":"control.wrap.Wrap.editionsMain",
"url":21,
"doc":"Wrap the list of editions of a project for the main display. Parameters      project: AttrDict The master project record of the editions. editions: list of AttrDict The edition records. Returns    - string The HTML of the edition list",
"func":1
},
{
"ref":"control.wrap.Wrap.sceneMain",
"url":21,
"doc":"Wrap the scene of an edition for the main display. Parameters      edition: AttrDict The edition record of the scene. viewer: string The viewer that will be used. version: string The version of the chosen viewer that will be used. action: string The mode in which the viewer should be opened. Returns    - string The HTML of the scene",
"func":1
},
{
"ref":"control.wrap.Wrap.getCaption",
"url":21,
"doc":"Produces a caption of a project or edition. Parameters      visual: string A link to an image to display in the caption. titleText: string The text on the caption. status: string The status of the project/edition: visible/hidden/published/in progress. The exact names statusCls: string The CSS class corresponding to  status button: string Control for a certain action, or empty if the user is not authorised. url: string The url to navigate to if the user clicks the caption.",
"func":1
},
{
"ref":"control.wrap.Wrap.wrapCaption",
"url":21,
"doc":"Assembles a caption from building blocks.",
"func":1
},
{
"ref":"control.wrap.Wrap.contentButton",
"url":21,
"doc":"Puts a button on the interface, if that makes sense. The button, when pressed, will lead to an action on certain content. It will be checked first if that action is allowed for the current user. If not the button will not be shown.  ! note \"Delete buttons\" Even if a user is authorised to delete a record, it is not allowed to delete master records if its detail records still exist. In that case, no delete button is displayed. Instead we display a count of detail records.  ! note \"Create buttons\" When placing a create button, the relevant record acts as the master record, to which the newly created record will be added as a detail. Parameters      table: string The relevant table. record: string | ObjectId | AttrDict The relevant record. action: string The type of action that will be performed if the button triggered. permitted: boolean, optional None If the permission for the action is already known before calling this function, it is passed here. If this parameter is None, we'll compute the permission. insertTable: string, optional None If the action is \"create\", this is the table in which a record get inserted. The  table and  record arguments are then supposed to specify the  master record of the newly inserted record. Needed to determine whether a press on the button is permitted. key: string, optional None If present, it identifies a field that is stored inside the record. href: string, optional None If present, contains the href attribute for the button.",
"func":1
},
{
"ref":"control.prepare",
"url":22,
"doc":""
},
{
"ref":"control.prepare.prepare",
"url":22,
"doc":"Prepares the way for setting up the Flask webapp. Several classes are instantiated with a singleton object; each of these objects has a dedicated task in the app:   control.config.Config.Settings : all configuration aspects   control.messages.Messages : handle all messaging to user and sysadmin   control.mongo.Mongo : higher-level commands to the MongoDb   control.viewers.Viewers : support the third party 3D viewers   control.wrap.Wrap : several lengthy functions to wrap concepts into HTML   control.datamodel.Datamodel : factory for handling fields, inherited by  Content   control.content.Content : retrieve all data that needs to be displayed   control.auth.Auth : compute the permission of the current user to access content   control.pages.Pages : high-level functions that distribute content over the page  ! note \"Should be run once!\" These objects are used in several web apps:  the main web app  a copy of the main app that is enriched with the webdav functionality However, these objects should be initialized once, before either app starts, and the same objects should be passed to both invocations of the factory functions that make them ( control.app.appFactory ). The invocations are done in  control.webdavapp.appFactory . Parameters      trivial: boolean, optional False If True, skips the initialization of most objects. Useful if the pure3d app container should run without doing anything. This happens when we just want to start the container and run shell commands inside it, for example after a complicated refactoring when the flask app has too many bugs. Returns    - AttrDict A dictionary keyed by the names of the singleton objects and valued by the singleton objects themselves.",
"func":1
}
]