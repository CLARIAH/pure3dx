URLS=[
"control/index.html",
"control/webdavapp.html",
"control/auth.html",
"control/users.html",
"control/files.html",
"control/config.html",
"control/mongo.html",
"control/checkgltf.html",
"control/flask.html",
"control/generic.html",
"control/html.html",
"control/datamodel.html",
"control/tailwind.html",
"control/authoidc.html",
"control/precheck.html",
"control/pages.html",
"control/content.html",
"control/admin.html",
"control/messages.html",
"control/static.html",
"control/environment.html",
"control/app.html",
"control/viewers.html",
"control/wrap.html",
"control/helpers.html",
"control/prepare.html",
"control/publish.html"
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
"doc":"Make a WebDAV enabled app.  Combine the main app with an other wsgi app that can handle WebDAV requests. There is a Python module that offers a wsgi app out of the box that can talk WebDAV, we configure it in  getWebdavApp() . The  dispatchWebdav() function combines the current app with this WebDAV app at a deep level, before requests are fed to either app.  ! note \"Authorisation\" Authorisation of WebDAV requests happens in the main app. See  dispatchWebdav() .  ! caution \"Requirements for the server\" When this Flask app runs and the Voyager software is run in edit mode, the client will fire a sequence of webdav requests to the server. When the app is served by the default Flask development server, these requests will almost surely block the whole application. The solution is to run the app through a task runner like Gunicorn. However, the app does not run in debug mode then, so tracing errors becomes more difficult then.",
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
"doc":"Check whether an action is allowed on data. The \"create\" action is a bit special, because we do not have any record to start with. In this case  table and  record should point to the master record, and  insertTable should have the table that will contain the new record. If the action is anything else,  table and  record refer to the relevant record, and  insertTable should not be passed. How do the authorisation rules work? First we consider the site-wise role of the user: guest, user, admin, or root. If the action is allowed on that basis, we return True. If not, we look whether the user has an additional role with regard to the record in question, or with any of its master records. If so, we apply the rules for those cases and see whether the action is permitted. Then we have the possibility that a record is in a certain state, e.g. projects may be visible or invisible, editions may be published or unpublished. For each of these states we have separate rules, so we inspect the states of the records and master records in order to select the appropriate rules. Parameters      table: string the relevant table; for  create actions it is the master table of the table in which a record will be inserted. record: ObjectId | AttrDict The id of the record that is being accessed or the record itself; for  create actions it is the master record to which a new record will be created as a detail. action: string, optional None The action for which permission is asked. insertTable: string Only relevant for \"create\" actions. The detail table in which the new record will be inserted. Returns    - boolean | dict If an action is passed: boolean whether action is allowed. If no action is passed: dict keyed by the allowed actions, the values are true. Actions with a falsy permission (False or the empty set) are not included in the dict. So, to test whether any action is allowed, it suffices to test whether  action in result ",
"func":1
},
{
"ref":"control.auth.Auth.mayBackup",
"url":2,
"doc":"Whether the current user is allowed to make backups.  Backups are only allowed in all modes.  Site-wide backups are only allowed for power users.  Project backups are only allowed for project organisers and (power users). Parameters      project: AttrDict | ObjectId | string, optional None If None, we deal with site-wide backup. Otherwise we get the backups of this project. Returns    - boolean whether the relevant backup/restore actions are allowed.",
"func":1
},
{
"ref":"control.auth.Auth.makeSafe",
"url":2,
"doc":"Changes an update action into a read action if needed. This function 'demotes' an \"update: to a \"read\" if the \"update\" is not allowed. If \"read\" itself is not allowed, None is returned. If any other action tahn \"update\" or \"read\" is passed, None is returned. Parameters      table: string The table in which the record exists. record: ObjectId | AttrDict The id of the record or the record itself. action: string An intended action. Returns    - string | void The resulting safe action.",
"func":1
},
{
"ref":"control.auth.Auth.initUser",
"url":3,
"doc":"Initialize the storage that keeps the details of the currently logged-in user. It will put an empty AttrDict as  global in the current application context. As long as there is no current user, this AttrDict will remain empty. If there is a current user, or a user logs in, it will get a member  user , which is the  sub as it comes from the OIDC authenticator or from a special login procedure. It may then also have additional members, such as  name and  role .",
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
"doc":"Log in a user. Logging in has several main steps: 1. redirecting to a private page, for which login is required 2. obtaining the authentication results when the user visits that page 3. storing the relevant user data When we log in test/pilot users, we can skip the first step, because we already know everything about the test/pilot user on the basis of the information in the request that brought us here. So, we find out if we have to log in a test/pilot user or a user that must be authenticated through oidc. We only log in a test/pilot user if we are in test/pilot mode and the user's \"sub\" is passed in the request. Returns    - response A redirect. When logging in in test/pilot mode, the redirect is to  referrer (the url we came from). Otherwise it is to a url that triggers an oidc login procedure. To that page we pass the referrer as part of the url, so that after login the user can be redirected to the original referrer.",
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
"doc":"Logs off the current user. First we find out whether we have to log out a test/pilot user or a normal user. After logging out, we redirect to the home page. Returns    - response A redirect to the home page.",
"func":1
},
{
"ref":"control.auth.Auth.identify",
"url":3,
"doc":"Make sure who is the current user. Checks whether there is a current user and whether that user is fully known, i.e. in the users table of the mongoDb. If there is a current user that is unknown to the database, the current user will be cleared. Otherwise, we make sure that we retrieve the current user's attributes from the database.  ! note \"No login\" We do not try to perform a login of a user, we only check who is the currently logged in user. A login must be explicitly triggered by the the  /login url.",
"func":1
},
{
"ref":"control.auth.Auth.myDetails",
"url":3,
"doc":"Who is the currently authenticated user? The appplication-context-global  User is inspected: does it contain a member called  user ? If so, that is taken as proof that we have a valid user. Returns    - dict Otherwise a copy of the complete  User record is returned. unless there is no  user member in the current user, then the empty dictionary is returned.",
"func":1
},
{
"ref":"control.auth.Auth.getUser",
"url":3,
"doc":"Obtain the \"sub\" of the currently logged in user from the request info. It works for test/pilot users and normal users. Parameters      fromArg: boolean, optional False If True, the test/pilot user is not read from the session, but from a request argument. This is used during the login procedure of test/pilot users. Returns    - boolean, string  Whether the user is a test/pilot user or a normally authenticated user. None if there is no authenticated user.  The \"sub\" of the user.",
"func":1
},
{
"ref":"control.auth.Auth.wrapLogin",
"url":3,
"doc":"Generate HTML for the login widget. De task is to generate login/logout buttons. If the user is logged in, his nickname should be displayed, together with a logout button. If no user is logged in, a login button should be displayed. If in test/pilot mode, a list of buttons for each test/pilot user should be displayed. Returns    - string HTML of the list of buttons for test/pilot users, with the button for the current user styled as active.",
"func":1
},
{
"ref":"control.auth.Auth.presentRole",
"url":3,
"doc":"Finds the interface representation of a role. Parameters      role: string The internal name of the role. Returns    - string The name of the role as it should be presented to users. If no representation can be found, the internal name is returned.",
"func":1
},
{
"ref":"control.auth.Auth.getInvolvedUsers",
"url":3,
"doc":"Finds the users involved in a specific role with respect to something. By this method you can find the organisers of a project, the editors of an edition, the admins of the site, etc. Parameters      table: string Either  site ,  project or  edition . This indicates the kind of thing that the users are related to. tableRecordRoles: tuple The tuple consists of tuples  (table, record, role) The users connected to that record in that table in that role should be added to the list. All roles are specified in the  yaml/authorise.yml file. Returns    - tuple or string If  asString is False, the result is a datastructure:  whether the information can be disclosed to the current users  the representation of that role on the interface.  a tuple: Each item is a tuple, corresponding to a user. For each user there are the follwoing fields:  user field in the user table  full name  table of the record to which the user is linked  role in which the user is linked to that record If  asString is True, this data structure will be wrapped in HTML.",
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
"ref":"control.files.str_presenter",
"url":4,
"doc":"configures yaml for dumping multiline strings Ref: https: stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data",
"func":1
},
{
"ref":"control.files.normpath",
"url":4,
"doc":"",
"func":1
},
{
"ref":"control.files.abspath",
"url":4,
"doc":"",
"func":1
},
{
"ref":"control.files.expanduser",
"url":4,
"doc":"",
"func":1
},
{
"ref":"control.files.unexpanduser",
"url":4,
"doc":"",
"func":1
},
{
"ref":"control.files.prefixSlash",
"url":4,
"doc":"Prefix a / before a path if it is non-empty and not already starts with it.",
"func":1
},
{
"ref":"control.files.dirEmpty",
"url":4,
"doc":"",
"func":1
},
{
"ref":"control.files.clearTree",
"url":4,
"doc":"Remove all files from a directory, recursively, but leave subdirectories. Reason: we want to inspect output in an editor. But if we remove the directories, the editor looses its current directory all the time. Parameters      path: The directory in question. A leading  ~ will be expanded to the user's home directory.",
"func":1
},
{
"ref":"control.files.initTree",
"url":4,
"doc":"Make sure a directory exists, optionally clean it. Parameters      path: The directory in question. A leading  ~ will be expanded to the user's home directory. If the directory does not exist, it will be created. fresh: boolean, optional False If True, existing contents will be removed, more or less gently. gentle: boolean, optional False When existing content is removed, only files are recursively removed, not subdirectories.",
"func":1
},
{
"ref":"control.files.dirNm",
"url":4,
"doc":"Get the directory part of a file name. Parameters      up: int, optional 1 The number of levels to go up. Should be 1 or higher. If not passed, the parent directory is returned. If it is 0 or lower, the  path itself is returned.",
"func":1
},
{
"ref":"control.files.fileNm",
"url":4,
"doc":"Get the file part of a file name.",
"func":1
},
{
"ref":"control.files.stripExt",
"url":4,
"doc":"Strip the extension of a file name, if there is one.",
"func":1
},
{
"ref":"control.files.splitPath",
"url":4,
"doc":"Split a file name in a directory part and a file part.",
"func":1
},
{
"ref":"control.files.isFile",
"url":4,
"doc":"Whether path exists and is a file.",
"func":1
},
{
"ref":"control.files.isDir",
"url":4,
"doc":"Whether path exists and is a directory.",
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
"ref":"control.files.fileMove",
"url":4,
"doc":"Moves a file if it exists as file. Wipes the destination file, if it exists.",
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
"ref":"control.files.dirMove",
"url":4,
"doc":"Moves a directory if it exists as directory. Refuses the operation in the target exists.",
"func":1
},
{
"ref":"control.files.dirCopy",
"url":4,
"doc":"Copies a directory if it exists as directory. Wipes the destination directory, if it exists.",
"func":1
},
{
"ref":"control.files.dirUpdate",
"url":4,
"doc":"Makes a destination dir equal to a source dir by copying newer files only. Files of the source dir that are missing or older in the destination dir are copied from the source to the destination. Files and directories in the destination dir that do not exist in the source dir are deleted, but this can be prevented. Parameters      pathSrc: string The source directory. It does not matter whether the directory ends with a slash or not, unless the directory is the root. pathDst: string The destination directory. It does not matter whether the directory ends with a slash or not, unless the directory is the root. force: boolean, optional False If True, files that are older in the source than in the destination will also be copied. delete: boolean, optional False Whether to delete items from the destination that do not exist in the source. level: integer, optional -1 Whether to merge recursively and to what level. At level 0 we do not merge, but copy each item from source to destination. If we start with a negative level, we never reach level 0, so we apply merging always. If we start with level 0, we merge the files, but we copy the subdirectories. If we start with a positive level, we merge that many levels deep, after which we switch to copying. Returns    - tuple  boolean: whether the action was successful;  integer: the amount of copy actions to destination directory  integer: the amount of delete actions in the destination directory",
"func":1
},
{
"ref":"control.files.dirMake",
"url":4,
"doc":"Creates a directory if it does not already exist as directory.",
"func":1
},
{
"ref":"control.files.dirContents",
"url":4,
"doc":"Gets the contents of a directory. Only the direct entries in the directory (not recursively), and only real files and folders. The list of files and folders will be returned separately. There is no attempt to sort the files. Parameters      path: string The path to the directory on the file system. asSet: boolean, optional False If True, the files and directories will be delivered as sets, otherwise as tuples. Returns    - tuple of tuple The files and the subdirectories. These are given as names relative to the directory  path , so  path is not prepended to these names.",
"func":1
},
{
"ref":"control.files.dirAllFiles",
"url":4,
"doc":"Gets all the files found by  path . The result is just  [path] if  path is a file, otherwise the list of files under  path , recursively. The files are sorted alphabetically by path name. Parameters      path: string The path to the file or directory on the file system. ignore: set Names of directories that must be skipped Returns    - tuple of string The names of the files under  path , starting with  path , followed by the bit relative to  path .",
"func":1
},
{
"ref":"control.files.getCwd",
"url":4,
"doc":"Get current directory. Returns    - string The current directory.",
"func":1
},
{
"ref":"control.files.chDir",
"url":4,
"doc":"Change to other directory. Parameters      directory: string The directory to change to.",
"func":1
},
{
"ref":"control.files.readPath",
"url":4,
"doc":"Reads the (textual) contents of a file.  ! note \"Not for binary files\" The file will not be opened in binary mode. Use this only for files with textual content. Parameters      filePath: string The path of the file on the file system. Returns    - string The contents of the file as unicode. If the file does not exist, the empty string is returned.",
"func":1
},
{
"ref":"control.files.readJson",
"url":4,
"doc":"",
"func":1
},
{
"ref":"control.files.writeJson",
"url":4,
"doc":"",
"func":1
},
{
"ref":"control.files.readYaml",
"url":4,
"doc":"Reads a yaml file. Parameters      text: string, optional None The input text, should be valid YAML, but see  ignore . If not given, the text is read from the file whose path is given in  asFile asFile: string, optional None The path of the file on the file system from which the YAML is read. If not given,  text is used. See also  ignore . plain: boolean, optional False If True, the result is (recursively) converted to an AttrDict preferTuples: optional True When converting to an AttrDict, values of type lists are replaced by tuples. Has only effect if  plain is False. defaultEmpty: boolean, False If True, when the yaml text is None or the file named by  asFile does not exist, it returns an empty dict or AttrDict. If False,  None is returned in such cases. ignore: boolean, False If the text is not valid YAML, do not raise an exception, but return the text itself. Returns    - AttrDict | void | string The data content of the yaml file if it exists.",
"func":1
},
{
"ref":"control.files.writeYaml",
"url":4,
"doc":"",
"func":1
},
{
"ref":"control.files.extNm",
"url":4,
"doc":"Get the extension part of a file name. The dot is not included. If there is no extension, the empty string is returned.",
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
"ref":"control.config",
"url":5,
"doc":""
},
{
"ref":"control.config.Config",
"url":5,
"doc":"All configuration details of the app. It is instantiated by a singleton object. Settings will be collected from the environment:  yaml files  environment variables  files and directories (for supported viewer software)  ! note \"Missing information\" If essential information is missing, the flask app will not be started, and no webserving will take place. Parameters      Messages: object Singleton instance of  control.messages.Messages . design: boolean, optional False If True only settings are collected that are needed for static page generation in the  Published directory, assuming that the project/edition files have already been exported. migrate: boolean, optional False If True only settings are collected that are needed for migration of data."
},
{
"ref":"control.config.Config.checkEnv",
"url":5,
"doc":"Collect the relevant information. If essential information is missing, processing stops. This is done by setting the  good member of Config to False.",
"func":1
},
{
"ref":"control.config.Config.checkRepo",
"url":5,
"doc":"Get the location of the pure3dx repository on the file system.",
"func":1
},
{
"ref":"control.config.Config.checkWebdav",
"url":5,
"doc":"Read the WEBDav methods from the webdav.yaml file. The methods are associated with the  read or  update keyword, depending on whether they are  GET like or  PUT like.",
"func":1
},
{
"ref":"control.config.Config.checkVersion",
"url":5,
"doc":"Get the current version of the pure3d app. We represent the version as the short hash of the current commit of the git repo that the running code is in.",
"func":1
},
{
"ref":"control.config.Config.checkSecret",
"url":5,
"doc":"Obtain a secret. This is secret information used for encrypting sessions. It resides somewhere on the file system, outside the pure3d repository.",
"func":1
},
{
"ref":"control.config.Config.checkModes",
"url":5,
"doc":"Determine whether flask is running in test/pilot/custom/prod mode.",
"func":1
},
{
"ref":"control.config.Config.checkData",
"url":5,
"doc":"Get the location of the project data on the file system.",
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
"ref":"control.config.Config.checkDatamodel",
"url":5,
"doc":"Read the yaml file with table and field settings. It contains model  master that contains the master tables with the information which tables are details of it. It also contains  link that contains the link tables with the information which tables are being linked. Both elements are needed when we delete records. If a user deletes a master record, its detail records become invalid. So either we must enforce that the user deletes the details first, or the system must delete those records automatically. When a user deletes a record that is linked to another record by means of a coupling record, the coupling record must be deleted automatically. Fields are bits of data that are stored in parts of records in MongoDb tables. Fields have several properties which we summarize under a key. So if we know the key of a field, we have access to all of its properties. The properties  nameSpave and  fieldPath determine how to drill down in a record in order to find the value of that field. The property  tp is the data type of the field, default  string . The property  caption is a label that may accompany a field value on the interface.",
"func":1
},
{
"ref":"control.config.Config.checkAuth",
"url":5,
"doc":"Read the yaml file with the authorisation rules.",
"func":1
},
{
"ref":"control.config.Config.checkViewers",
"url":5,
"doc":"Make an inventory of the supported 3D viewers.",
"func":1
},
{
"ref":"control.config.Config.checkBanner",
"url":5,
"doc":"Sets a banner for all pages. This banner may include warnings that the site is still work in progress. Returns    - void The banner is stored in the  banner member of the  Settings object.",
"func":1
},
{
"ref":"control.config.Config.checkDesign",
"url":5,
"doc":"Checks the design resources. Returns    - void Some values are stored in the  Settings object.",
"func":1
},
{
"ref":"control.config.Config.Settings",
"url":5,
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
"doc":"All about users and the current user. This class has methods to login/logout a user, to retrieve the data of the currently logged in user, and to query the users table in MongoDb. It is instantiated by a singleton object.  ! note \"User details are not stored here\" The user details are not stored as members of this object, since this object has been made before the flask app was initialized, hence the object is global in the sefver process, meaning that all workers can see its data. Instead, the user details are stored in a so-called  global in an [Application Context](https: flask.palletsprojects.com/en/2.2.x/appcontext/), where it is visible and modifiable by the current request only. Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo ."
},
{
"ref":"control.users.Users.initUser",
"url":3,
"doc":"Initialize the storage that keeps the details of the currently logged-in user. It will put an empty AttrDict as  global in the current application context. As long as there is no current user, this AttrDict will remain empty. If there is a current user, or a user logs in, it will get a member  user , which is the  sub as it comes from the OIDC authenticator or from a special login procedure. It may then also have additional members, such as  name and  role .",
"func":1
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
"doc":"Log in a user. Logging in has several main steps: 1. redirecting to a private page, for which login is required 2. obtaining the authentication results when the user visits that page 3. storing the relevant user data When we log in test/pilot users, we can skip the first step, because we already know everything about the test/pilot user on the basis of the information in the request that brought us here. So, we find out if we have to log in a test/pilot user or a user that must be authenticated through oidc. We only log in a test/pilot user if we are in test/pilot mode and the user's \"sub\" is passed in the request. Returns    - response A redirect. When logging in in test/pilot mode, the redirect is to  referrer (the url we came from). Otherwise it is to a url that triggers an oidc login procedure. To that page we pass the referrer as part of the url, so that after login the user can be redirected to the original referrer.",
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
"doc":"Logs off the current user. First we find out whether we have to log out a test/pilot user or a normal user. After logging out, we redirect to the home page. Returns    - response A redirect to the home page.",
"func":1
},
{
"ref":"control.users.Users.identify",
"url":3,
"doc":"Make sure who is the current user. Checks whether there is a current user and whether that user is fully known, i.e. in the users table of the mongoDb. If there is a current user that is unknown to the database, the current user will be cleared. Otherwise, we make sure that we retrieve the current user's attributes from the database.  ! note \"No login\" We do not try to perform a login of a user, we only check who is the currently logged in user. A login must be explicitly triggered by the the  /login url.",
"func":1
},
{
"ref":"control.users.Users.myDetails",
"url":3,
"doc":"Who is the currently authenticated user? The appplication-context-global  User is inspected: does it contain a member called  user ? If so, that is taken as proof that we have a valid user. Returns    - dict Otherwise a copy of the complete  User record is returned. unless there is no  user member in the current user, then the empty dictionary is returned.",
"func":1
},
{
"ref":"control.users.Users.getUser",
"url":3,
"doc":"Obtain the \"sub\" of the currently logged in user from the request info. It works for test/pilot users and normal users. Parameters      fromArg: boolean, optional False If True, the test/pilot user is not read from the session, but from a request argument. This is used during the login procedure of test/pilot users. Returns    - boolean, string  Whether the user is a test/pilot user or a normally authenticated user. None if there is no authenticated user.  The \"sub\" of the user.",
"func":1
},
{
"ref":"control.users.Users.wrapLogin",
"url":3,
"doc":"Generate HTML for the login widget. De task is to generate login/logout buttons. If the user is logged in, his nickname should be displayed, together with a logout button. If no user is logged in, a login button should be displayed. If in test/pilot mode, a list of buttons for each test/pilot user should be displayed. Returns    - string HTML of the list of buttons for test/pilot users, with the button for the current user styled as active.",
"func":1
},
{
"ref":"control.users.Users.presentRole",
"url":3,
"doc":"Finds the interface representation of a role. Parameters      role: string The internal name of the role. Returns    - string The name of the role as it should be presented to users. If no representation can be found, the internal name is returned.",
"func":1
},
{
"ref":"control.users.Users.getInvolvedUsers",
"url":3,
"doc":"Finds the users involved in a specific role with respect to something. By this method you can find the organisers of a project, the editors of an edition, the admins of the site, etc. Parameters      table: string Either  site ,  project or  edition . This indicates the kind of thing that the users are related to. tableRecordRoles: tuple The tuple consists of tuples  (table, record, role) The users connected to that record in that table in that role should be added to the list. All roles are specified in the  yaml/authorise.yml file. Returns    - tuple or string If  asString is False, the result is a datastructure:  whether the information can be disclosed to the current users  the representation of that role on the interface.  a tuple: Each item is a tuple, corresponding to a user. For each user there are the follwoing fields:  user field in the user table  full name  table of the record to which the user is linked  role in which the user is linked to that record If  asString is True, this data structure will be wrapped in HTML.",
"func":1
},
{
"ref":"control.users.Users.oidc",
"url":3,
"doc":"The object that gives access to authentication methods."
},
{
"ref":"control.mongo",
"url":6,
"doc":""
},
{
"ref":"control.mongo.Mongo",
"url":6,
"doc":"CRUD interface to content in the MongoDb database. This class has methods to connect to a MongoDb database, to query its data, to create, update and delete data. It is instantiated by a singleton object.  ! note \"string versus ObjectId\" Some functions execute MongoDb statements, based on parameters whose values are MongoDb identifiers. These should be objects in the class  bson.objectid.ObjectId . However, in many cases these ids enter the app as strings. In this module, such strings will be cast to proper ObjectIds, provided they are recognizable as values in a field whose name is  _id or ends with  Id . Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages ."
},
{
"ref":"control.mongo.Mongo.cast",
"url":6,
"doc":"Try to cast the value as an ObjectId. Paramaters      value:string The value to cast, normally a string representation of a BSON ObjectId. Returns    - ObjectId | void The corresponding BSON ObjectId if the input is a valid representation of such an id, otherwise  None .",
"func":1
},
{
"ref":"control.mongo.Mongo.isId",
"url":6,
"doc":"Test whether a value is an ObjectId Parameters      value: any The value to test Returns    - boolean Whether the value is an objectId",
"func":1
},
{
"ref":"control.mongo.Mongo.connect",
"url":6,
"doc":"Make connection with MongoDb if there is no connection yet. The connection details come from  control.config.Config.Settings . After a successful connection attempt, the connection handle is stored in the  client and  db members of the Mongo object. When a connection handle exists, this method does nothing.",
"func":1
},
{
"ref":"control.mongo.Mongo.disconnect",
"url":6,
"doc":"Disconnect from the MongoDB.",
"func":1
},
{
"ref":"control.mongo.Mongo.tables",
"url":6,
"doc":"List the existent tables in the database. Returns    - list The names of the tables.",
"func":1
},
{
"ref":"control.mongo.Mongo.clearTable",
"url":6,
"doc":"Make sure that a table exists and that it is empty. Parameters      table: string The name of the table. If no such table exists, it will be created. delete: boolean, optional False If True, and the table existed before, it will be deleted. If False, the table will be cleared, i.e. all its records get deleted, but the table remains.",
"func":1
},
{
"ref":"control.mongo.Mongo.get",
"url":6,
"doc":"Get the record and recordId if only one of them is specified. If the record is specified by id, the id maybe an ObjectId or a string, which will then be cast to an ObjectId. Parameters      table: string The table in which the record can be found record: string | ObjectID | AttrDict | void Either the id of the record, or the record itself. Returns    - tuple  ObjectId: the id of the record  AttrDict: the record itself If  record is None, both members of the tuple are None",
"func":1
},
{
"ref":"control.mongo.Mongo.getRecord",
"url":6,
"doc":"Get a single record from a table. Parameters      table: string The name of the table from which we want to retrieve a single record. warn: boolean, optional True If True, warn if there is no record satisfying the criteria. stop: boolean, optional True If the command is not successful, stop after issuing the error, do not return control. criteria: dict A set of criteria to narrow down the search. Usually they will be such that there will be just one record that satisfies them. But if there are more, a single one is chosen, by the mechanics of the built-in MongoDb command  findOne . Returns    - AttrDict The single record found, or an empty AttrDict if no record satisfies the criteria.",
"func":1
},
{
"ref":"control.mongo.Mongo.getList",
"url":6,
"doc":"Get a list of records from a table. Parameters      table: string The name of the table from which we want to retrieve records. stop: boolean, optional True If the command is not successful, stop after issuing the error, do not return control. sort: string | function, optional None Sort key. If  None , the results will not be sorted. If a string, it is the name of a field by which the results will be sorted in ascending order. If a function, the function should take a record as input and return a value. The records will be sorted by this value. asDict: boolean or string, optional False If False, returns a list of records as result. If True or a string, returns the same records, but now as dict, keyed by the  _id field if asDict is True, else keyed by the field in dicated by asDict. criteria: dict A set of criteria to narrow down the search. Returns    - list of AttrDict The list of records found, empty if no records are found. Each record is cast to an AttrDict.",
"func":1
},
{
"ref":"control.mongo.Mongo.deleteRecord",
"url":6,
"doc":"Deletes a single record from a table. Parameters      table: string The name of the table from which we want to delete a single record. stop: boolean, optional True If the command is not successful, stop after issuing the error, do not return control. criteria: dict A set of criteria to narrow down the selection. Usually they will be such that there will be just one record that satisfies them. But if there are more, a single one is chosen, by the mechanics of the built-in MongoDb command  updateOne . Returns    - boolean Whether the delete was successful",
"func":1
},
{
"ref":"control.mongo.Mongo.deleteRecords",
"url":6,
"doc":"Delete multiple records from a table. Parameters      table: string The name of the table from which we want to delete a records. stop: boolean, optional True If the command is not successful, stop after issuing the error, do not return control. criteria: dict A set of criteria to narrow down the selection. Returns    - boolean, integer Whether the command completed successfully and how many records have been deleted",
"func":1
},
{
"ref":"control.mongo.Mongo.updateRecord",
"url":6,
"doc":"Updates a single record from a table. Parameters      table: string The name of the table in which we want to update a single record. updates: dict The fields that must be updated with the values they must get. If the value  None is specified for a field, that field will be set to null. stop: boolean, optional True If the command is not successful, stop after issuing the error, do not return control. criteria: dict A set of criteria to narrow down the selection. Usually they will be such that there will be just one record that satisfies them. But if there are more, a single one is chosen, by the mechanics of the built-in MongoDb command  updateOne . Returns    - boolean Whether the update was successful",
"func":1
},
{
"ref":"control.mongo.Mongo.insertRecord",
"url":6,
"doc":"Inserts a new record in a table. Parameters      table: string The table in which the record will be inserted. stop: boolean, optional True If the command is not successful, stop after issuing the error, do not return control.  fields: dict The field names and their contents to populate the new record with. Returns    - ObjectId The id of the newly inserted record, or None if the record could not be inserted.",
"func":1
},
{
"ref":"control.mongo.Mongo.execute",
"url":6,
"doc":"Executes a MongoDb command and returns the result. Parameters      table: string The table on which to perform the command. command: string The built-in MongoDb command. Note that the Python interface requires you to write camelCase commands with underscores. So the Mongo command  findOne should be passed as  find_one . args: list Any number of additional arguments that the command requires. warn: boolean, optional True If True, warn if there is an error. stop: boolean, optional True If the command is not successful, stop after issuing the error, do not return control. kwargs: list Any number of additional keyword arguments that the command requires. Returns    - boolean, any The  boolean is whether an error occurred. The  any is whatever the MongoDb command returns. If the command fails, an error message is issued and  any=None is returned.",
"func":1
},
{
"ref":"control.mongo.Mongo.consolidate",
"url":6,
"doc":"Resolves all links in a record to title values of linked records. The  _id field of the record will be removed. Values of fields with names like  xxxId will be looked up in table  xxx , and will be replaced by the value of the  title field of the found record. Parameters      record: dict or AttrDict The record data to consolidate. Returns    - dict All AttrDict values will be recursively transformed in ordinary dict values.",
"func":1
},
{
"ref":"control.mongo.Mongo.mkBackup",
"url":6,
"doc":"Backs up data as record files in table folders. We do site-wide backups and project-specific backups. See also  control.content.Content.mkBackup This function backs up database data in [ bson ](https: www.mongodb.com/basics/bson) and/or  json format. Inspired by this [gist](https: gist.github.com/Lh4cKg/939ce683e2876b314a205b3f8c6e8e9d). Parameters      dstBase: string Destination folder. This folder will get subfolders  bson and/or  json in which the backups are stored. project: string, optional None If given, only backs up the given project. asJson: boolean, optional False Whether to create a backup in  json format asBson: boolean, optional True Whether to create a backup in  bson format Returns    - boolean Whether the operation was successful.",
"func":1
},
{
"ref":"control.mongo.Mongo.writeRecords",
"url":6,
"doc":"Writes records to bson and possibly json file. If the destination file already exists, it will be wiped. Parameters      table: string Table that contains the record. Will be used as file name for the record to be written to. record: dict The record as it is retrieved from MongoDb dstb: string Destination folder for the bson file. dstj: string, optional None Destination folder for the json file. If  None , no json file will be written. jOpts: dict, optional {} Format options for writing the json file. first Returns    - integer The number of records written",
"func":1
},
{
"ref":"control.mongo.Mongo.restore",
"url":6,
"doc":"Restores the database from record files in table folders. We do site-wide restores or project-specific restores. See also  control.content.Content.restore This function restores database data given in [ bson ](https: www.mongodb.com/basics/bson). Inspired by this [gist](https: gist.github.com/Lh4cKg/939ce683e2876b314a205b3f8c6e8e9d). Parameters      src: string Source folder. project: string, optional None If given, only restores the given project. clean: boolean, optional True Whether to delete records from a table before restoring records to it. If  clean=True then, in case of site-wide restores, all records will be cleaned. In case of project restores, only the relevant project/edition records will be cleaned. Returns    - boolean Whether the operation was successful.",
"func":1
},
{
"ref":"control.checkgltf",
"url":7,
"doc":""
},
{
"ref":"control.checkgltf.check",
"url":7,
"doc":"",
"func":1
},
{
"ref":"control.checkgltf.main",
"url":7,
"doc":"",
"func":1
},
{
"ref":"control.flask",
"url":8,
"doc":""
},
{
"ref":"control.flask.appInitializing",
"url":8,
"doc":"Whether the flask web app is already running. If there is no  current_app , we are surely initializing. But if flask runs in debug mode, two instances of the server will be started. When the second one is started, there is a second time that there is no  current_app . In that case we alse inspect the environment variable  WERKZEUG_RUN_MAIN . If it is set, we have already had the init stage of the first instance.",
"func":1
},
{
"ref":"control.flask.appMake",
"url":8,
"doc":"Create the Flask app.",
"func":1
},
{
"ref":"control.flask.renderTemplate",
"url":8,
"doc":"Renders a template. Parameters      template: string The name of the template, without extension. kwargs: dict The variables with values to fill in into the template. Returns    - object The response with as content the filled template.",
"func":1
},
{
"ref":"control.flask.flashMsg",
"url":8,
"doc":"Gives user feedback using the Flask flash mechanism.",
"func":1
},
{
"ref":"control.flask.response",
"url":8,
"doc":"Wrap data in a response. Parameters      data: any The data to be transferred in an HTTP response. headers: dict Returns    - object The HTTP response",
"func":1
},
{
"ref":"control.flask.sendFile",
"url":8,
"doc":"Send a file as a response. It is assumed that  path exists as a readable file on the file system. The function will add headers based on the file extension. Parameters      path: string The file to be transferred in an HTTP response. Returns    - object The HTTP response",
"func":1
},
{
"ref":"control.flask.redirectStatus",
"url":8,
"doc":"Redirect. Parameters      url: string The url to redirect to good: Whether the redirection corresponds to a normal scenario or is the result of an error Returns    - response A redirect response with either code 302 (good) or 303 (bad)",
"func":1
},
{
"ref":"control.flask.appStop",
"url":8,
"doc":"Stop the request with a 404.",
"func":1
},
{
"ref":"control.flask.sessionPop",
"url":8,
"doc":"Pops a variable from the session. Parameters      name: string The name of the variable. Returns    - void",
"func":1
},
{
"ref":"control.flask.sessionGet",
"url":8,
"doc":"Gets a variable from the session. Parameters      name: string The name of the variable. Returns    - string | void The value of the variable, if it exists, else None.",
"func":1
},
{
"ref":"control.flask.sessionSet",
"url":8,
"doc":"Sets a session variable to a value. Parameters      name: string The name of the variable. value: string The value that will be assigned to the variable Returns    - void",
"func":1
},
{
"ref":"control.flask.requestMethod",
"url":8,
"doc":"Get the request method.",
"func":1
},
{
"ref":"control.flask.requestArg",
"url":8,
"doc":"Get the value of a request arg. Parameters      name: string The name of the arg. Returns    - string | void The value of the arg, if it is defined, else the None.",
"func":1
},
{
"ref":"control.flask.requestData",
"url":8,
"doc":"Get the request data. Returns    - bytes Useful for uploaded files.",
"func":1
},
{
"ref":"control.flask.getReferrer",
"url":8,
"doc":"Get the referrer from the request. We strip the root url from the referrer. If that is not possible, the referrer is an other site, in that case we substitute the home page.  ! caution \"protocol mismatch\" It has been observed that in some cases the referrer, as taken from the request, and the root url as taken from the request, differ in their protocol part:  http: versus  https: . Therefore we first strip the protocol part from both referrer and root url before we remove the prefix. Returns    - string",
"func":1
},
{
"ref":"control.generic",
"url":9,
"doc":""
},
{
"ref":"control.generic.now",
"url":9,
"doc":"The current moment in time as a isolike string value. Strips everything after the decimal point, (milliseconds and timezone).",
"func":1
},
{
"ref":"control.generic.splitComp",
"url":9,
"doc":"",
"func":1
},
{
"ref":"control.generic.makeComps",
"url":9,
"doc":"",
"func":1
},
{
"ref":"control.generic.versionCompare",
"url":9,
"doc":"",
"func":1
},
{
"ref":"control.generic.getVersionKeyFunc",
"url":9,
"doc":"",
"func":1
},
{
"ref":"control.generic.attResolve",
"url":9,
"doc":"",
"func":1
},
{
"ref":"control.generic.AttrDict",
"url":9,
"doc":"Turn a dict into an object with attributes. If non-existing attributes are accessed for reading,  None is returned. See these links on stackoverflow:  [1](https: stackoverflow.com/questions/4984647/accessing-dict-keys-like-an-attribute)  [2](https: stackoverflow.com/questions/16237659/python-how-to-implement-getattr) especially the remark that >  __getattr__ is only used for missing attribute lookup We also need to define the  __missing__ method in case we access the underlying dict by means of keys, like  xxx[\"yyy\"] rather then by attribute like  xxx.yyy . Create the data structure from incoming data."
},
{
"ref":"control.generic.AttrDict.deepdict",
"url":9,
"doc":"",
"func":1
},
{
"ref":"control.generic.deepdict",
"url":9,
"doc":"Turns an  AttrDict into a  dict , recursively. Parameters      info: any The input dictionary. We assume that it is a data structure built by  tuple ,  list ,  set ,  frozenset ,  dict and atomic types such as  int ,  str ,  bool . We assume there are no user defined objects in it, and no generators and functions. Returns    - dict A dictionary containing the same info as the input dictionary, but where each value of type  AttrDict is turned into a  dict .",
"func":1
},
{
"ref":"control.generic.deepAttrDict",
"url":9,
"doc":"Turn a  dict into an  AttrDict , recursively. Parameters      info: any The input dictionary. We assume that it is a data structure built by  tuple ,  list ,  set ,  frozenset ,  dict and atomic types such as  int ,  str ,  bool . We assume there are no user defined objects in it, and no generators and functions. preferTuples: boolean, optional False Lists are converted to tuples. Returns    - AttrDict An  AttrDict containing the same info as the input dictionary, but where each value of type  dict is turned into an  AttrDict .",
"func":1
},
{
"ref":"control.html",
"url":10,
"doc":"HTML generation made easy.  for each HTML element there is a function to wrap attributes and content in it.  additional support for more involved patches of HTML ( details ,  input , icons)  escaping of HTML elements."
},
{
"ref":"control.html.HtmlElement",
"url":10,
"doc":"Wrapping of attributes and content into an HTML element.  Initialization An HtmlElement object. Parameters      name: string See below."
},
{
"ref":"control.html.HtmlElement.atNormal",
"url":10,
"doc":"Normalize the names of attributes. Substitute the  cls attribute name with  class . Substitute the  tp attribute name with  type .",
"func":1
},
{
"ref":"control.html.HtmlElement.atEscape",
"url":10,
"doc":"Escapes double quotes in attribute values.",
"func":1
},
{
"ref":"control.html.HtmlElement.attStr",
"url":10,
"doc":"Stringify attributes.  ! hint Attributes with value  True are represented as bare attributes, without value. For example:  {open=True} translates into  open . Attributes with value  False are omitted.  ! caution Use the name  cls to get a  class attribute inside an HTML element. The name  class interferes too much with Python syntax to be usable as a keyowrd argument. Parameters      atts: dict A dictionary of attributes. addCls: string An extra  class attribute. If there is already a class attribute  addCls will be appended to it. Otherwise a fresh class attribute will be created. Returns    - string The serialzed attributes.",
"func":1
},
{
"ref":"control.html.HtmlElement.wrap",
"url":10,
"doc":"Wraps attributes and content into an element.  ! caution No HTML escaping of special characters will take place. You have to use  control.html.HtmlElements.he yourself. Parameters      material: string | iterable The element content. If the material is not a string but another iterable, the items will be joined by the empty string. addCls: string An extra  class attribute. If there is already a class attribute  addCls will be appended to it. Otherwise a fresh class attribute will be created. Returns    - string The serialized element.",
"func":1
},
{
"ref":"control.html.HtmlElement.name",
"url":10,
"doc":" string The element name."
},
{
"ref":"control.html.HtmlElements",
"url":10,
"doc":"Wrap specific HTML elements and patterns.  ! note Nearly all elements accept an arbitrary supply of attributes in the  atts parameter, which will not further be documented. Gives the HtmlElements access to Settings and Messages."
},
{
"ref":"control.html.HtmlElements.amp",
"url":10,
"doc":""
},
{
"ref":"control.html.HtmlElements.lt",
"url":10,
"doc":""
},
{
"ref":"control.html.HtmlElements.gt",
"url":10,
"doc":""
},
{
"ref":"control.html.HtmlElements.apos",
"url":10,
"doc":""
},
{
"ref":"control.html.HtmlElements.quot",
"url":10,
"doc":""
},
{
"ref":"control.html.HtmlElements.nbsp",
"url":10,
"doc":""
},
{
"ref":"control.html.HtmlElements.he",
"url":10,
"doc":"Escape HTML characters. The following characters will be replaced by entities:   &   .",
"func":1
},
{
"ref":"control.html.HtmlElements.content",
"url":10,
"doc":"fragment. This is a pseudo element. The material will be joined together, without wrapping it in an element. There are no attributes. The material is recursively joined into a string. Parameters      material: string | iterable Every argument in  material may be None, a string, or an iterable. tight: boolean, optional False If True, all material will be joined tightly, with no intervening string. Otherwise, all pieces will be joined with a newline. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.wrapValue",
"url":10,
"doc":"Wraps one or more values in elements. The value is recursively joined into elements. The value at the outermost level the result is wrapped in a single outer element. All nested values are wrapped in inner elements. If the value is None, a bare empty string is returned. The structure of elements reflects the structure of the value. Parameters      value: string | iterable Every argument in  value may be None, a string, or an iterable. outerElem: string, optional \"div\" The single element at the outermost level outerArgs: list, optional [] Arguments for the outer element. outerAtts: dict, optional {} Attributes for the outer element. innerElem: string, optional \"span\" The elements at all deeper levels innerArgs: list, optional [] Arguments for the inner elements. innerAtts: dict, optional {} Attributes for the inner elements. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.elem",
"url":10,
"doc":"Wraps an element whose tag is determined at run time. You can also use this to wrap non-html elements. Parameters      thisClass: class The current class tag: string The name of the element  args,  kwargs: any The remaining arguments to be passed to the underlying wrapper.",
"func":1
},
{
"ref":"control.html.HtmlElements.a",
"url":10,
"doc":"A. Hyperlink. Parameters      material: string | iterable Text of the link. href: url Destination of the link. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.b",
"url":10,
"doc":"B. Bold element. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.body",
"url":10,
"doc":"BODY. The  part of a document Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.br",
"url":10,
"doc":"BR. Line break. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.button",
"url":10,
"doc":"BUTTON. A clickable button Parameters      material: string | iterable What is displayed on the button. tp: The type of the button, e.g.  submit or  button Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.code",
"url":10,
"doc":"CODE. Code element. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.checkbox",
"url":10,
"doc":"INPUT type=checkbox. The element to receive user clicks. Parameters      var: string The name of an identifier for the element. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.dd",
"url":10,
"doc":"DD. The definition part of a term. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.details",
"url":10,
"doc":"DETAILS. Collapsible details element. Parameters      summary: string | iterable The summary. material: string | iterable The expansion. itemkey: string Identifier for reference from Javascript. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.detailx",
"url":10,
"doc":"detailx. Collapsible details pseudo element. Unlike the HTML  details element, this one allows separate open and close controls. There is no summary.  ! warning The  icon names must be listed in the web.yaml config file under the key  icons . The icon itself is a Unicode character.  ! hint The  atts go to the outermost  div of the result. Parameters      detailIcons: string | (string, string) Names of the icons that open and close the element. itemkey: string Identifier for reference from Javascript. openAtts: dict, optinal,  {} Attributes for the open icon. closeAtts: dict, optinal,  {} Attributes for the close icon. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.dialog",
"url":10,
"doc":"DIALOG. A  element. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.div",
"url":10,
"doc":"DIV. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.dl",
"url":10,
"doc":"DL. Definition list. Parameters      items: iterable of (string, string) These are the list items, which are term-definition pairs. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.dt",
"url":10,
"doc":"DT. Term of a definition. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.h",
"url":10,
"doc":"H1, H2, H3, H4, H5, H6. Parameters      level: int The heading level. material: string | iterable The heading content. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.head",
"url":10,
"doc":"HEAD. The  part of a document Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.i",
"url":10,
"doc":"I. Italic element. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.icon",
"url":10,
"doc":"icon. Pseudo element for an icon.  ! warning The  icon names must be listed in the settings.yml config file under the key  icons . The icon itself is a Unicode character. Parameters      icon: string Name of the icon. text: string, optional,  None Extra text that will be placed in front of the icon. asChar: boolean, optional,  False If  True , just output the icon character. Otherwise, wrap it in a    with all attributes that might have been passed. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.iconx",
"url":10,
"doc":"iconx. Pseudo element for a clickable icon. It will be wrapped in an    .  element or a  if  href is  None . If  href is the empty string, the element will still be wrapped in an    element, but without a  href attribute.  ! warning The  icon names must be listed in the settings.yml config file under the key  icons . The icon itself is a Unicode character. Parameters      icon: string Name of the icon. text: string, optional,  None Extra text that will be placed in front of the icon. href: url, optional,  None Destination of the icon when clicked. Will be left out when equal to the empty string. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.actionButton",
"url":10,
"doc":"Generates an action button to be activated by client side Javascript. It is assumed that the permission has already been checked. Parameters      H: object The  control.html.HtmlElements object name: string The name of the icon as displayed on the button kind: string, optional None The kind of the button, passed on in attribute  kind , can be used by Javascript to identify this button. If  None , the kind is set to the value of the  name parameter. Returns    - string The HTML of the button.",
"func":1
},
{
"ref":"control.html.HtmlElements.iframe",
"url":10,
"doc":"IFRAME. An iframe, which is an empty element with an obligatory end tag. Parameters      src: url Source for the iframe. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.img",
"url":10,
"doc":"IMG. Image element.  ! note The  atts go to the outer element, which is either    if it is not further wrapped, or    . The  imgAtts only go to the    element. Parameters      src: url The url of the image. href: url, optional,  None The destination to navigate to if the image is clicked. The images is then wrapped in an    element. If missing, the image is not wrapped further. title: string, optional,  None Tooltip. imgAtts: dict, optional {} Attributes that go to the    element. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.input",
"url":10,
"doc":"INPUT. The element to receive types user input.  ! caution Do not use this for checkboxes. Use  control.html.HtmlElements.checkbox instead.  ! caution Do not use this for file inputs. Use  control.html.HtmlElements.finput instead. Parameters      tp: string The type of input material: string | iterable This goes into the  value attribute of the element, after HTML escaping. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.finput",
"url":10,
"doc":"INPUT type=\"file\". The input element for uploading files. If the user does not have  update permission, only information about currently uploaded file(s) is presented. But if the user does have upload permission, there will be an additional control to update a new file and there will be controls to delete existing files. Parameters      content: list or tuple The widget handles to cases:  1 single file with a prescribed name.  no prescribed name, lists all files that match the  accept parameter. In the first case,  content is a tuple consisting of  file name  whether the file exists  a url to load the file as image, or None In the second case,  content is a list containing a tuple for each file:  file name  a url to load the file as image, or None And in this case, all files exist. In both cases, a delete control will be added to each file, if allowed. If an image url is present, the contents of the file will be displayed as an img element. accept: string MIME type of uploaded file mayChange: boolean Whether the user is allowed to upload new files and delete existing files. saveUrl: string The url to which the resulting file should be posted. deleteUrl: string The url to use to delete a file, with the understanding that the file name should be appended to it. caption: string basis for tooltips for the upload and delete buttons cls: string, optional  CSS class for the outer element buttonCls: string, optional  CSS class for the buttons wrapped: boolean, optional True Whether the content should be wrapped in a container element. If so, the container element carries a class attribute filled with  cls , and all attributes specified in the  atts argument. This generates a new widget on the page. If False, only the content is passed. Use this if the content of an existing widget has changed and must be inserted in that widget. The outer element of the widget is not changed. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.li",
"url":10,
"doc":"LI. List item. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.link",
"url":10,
"doc":"LINK. Typed hyperlink in the  element. Parameters      rel: string: The type of the link href: url Destination of the link. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.meta",
"url":10,
"doc":"META. A  element inside the  part of a document Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.ol",
"url":10,
"doc":"OL. Ordered list. Parameters      tp: string, optional \"1\" The type of ordered list, see the [HTML spec](https: developer.mozilla.org/en-US/docs/Web/HTML/Element/ol) items: iterable of string These are the list items. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.p",
"url":10,
"doc":"P. Paragraph. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.script",
"url":10,
"doc":"SCRIPT. Parameters      material: string | iterable The Javascript. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.small",
"url":10,
"doc":"SMALL. Small element. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.span",
"url":10,
"doc":"SPAN. Inline element. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.table",
"url":10,
"doc":"TABLE. The table element. Parameters      headers, rows: iterables of iterables An iterable of rows. Each row is a tuple: an iterable of cells, and a dict of atts for the row. Each cell is a tuple: material for the cell, and a dict of atts for the cell.  ! note Cells in normal rows are wrapped in    , cells in header rows go into    . Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.textarea",
"url":10,
"doc":"TEXTAREA. Input element for larger text, typically Markdown. Parameters      material: string | iterable Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.ul",
"url":10,
"doc":"UL. Unordered list. Parameters      items: iterable of string These are the list items. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.HtmlElements.wrapTable",
"url":10,
"doc":"Rows and cells. Parameters      data: iterable of iterables. Rows and cells within them, both with dicts of atts. td: function Funnction for wrapping the cells, typically boiling down to wrapping them in either    or    elements. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.asString",
"url":10,
"doc":"Join an iterable of strings or iterables into a string. And if the value is already a string, return it, and if it is  None return the empty string. The material is recursively joined into a string. Parameters      value: string | iterable | void Every argument in  value may be None, a string, or an iterable. tight: boolean, optional False If True, all material will be joined tightly, with no intervening string. Otherwise, all pieces will be joined with a newline. Returns    - string(html)",
"func":1
},
{
"ref":"control.html.isIterable",
"url":10,
"doc":"Whether a value is a non-string iterable.  ! note Strings are iterables. We want to know whether a value is a string or an iterable of strings.",
"func":1
},
{
"ref":"control.datamodel",
"url":11,
"doc":""
},
{
"ref":"control.datamodel.Datamodel",
"url":11,
"doc":"Datamodel related operations. This class has methods to manipulate various pieces of content in the data sources, and hand it over to higher level objects. It can find out dependencies between related records, and it knows a thing or two about fields. It is instantiated by a singleton object. It has a method which is a factory for  control.datamodel.Field objects, which deal with individual fields. Likewise it has a factory function for  control.datamodel.Upload objects, which deal with file uploads. Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo ."
},
{
"ref":"control.datamodel.Datamodel.relevant",
"url":11,
"doc":"Get a relevant record and the table to which it belongs. A relevant record is either a project record, or an edition record, or the one and only site record. If all optional parameters are None, we look for the site record. If the project parameter is not None, we look for the project record. This is the inverse of  context() . Paramenters      - project: string | ObjectId | AttrDict, optional None The project whose record we need. edition: string | ObjectId | AttrDict, optional None The edition whose record we need. Returns    - tuple  table: string; the table in which the record is found  record id: string; the id of the record  record: AttrDict; the record itself If both project and edition are not None",
"func":1
},
{
"ref":"control.datamodel.Datamodel.context",
"url":11,
"doc":"Get the context of a record. Get the project and edition records to which the record belongs. Parameters      table: string The table in which the record sits. record: string The record. This is the inverse of  relevant() . Returns    - tuple of tuple (siteId, site, projectId, project, editionId, edition)",
"func":1
},
{
"ref":"control.datamodel.Datamodel.getDetailRecords",
"url":11,
"doc":"Retrieve the detail records of a master record. It finds all records that have a field containing an id of the given master record. But not those in cross-link records. Details are not retrieved recursively, only the direct details of a master are fetched. Parameters      masterTable: string The name of the table in which the master record lives. master: string | ObjectId | AttrDict The master record. Returns    - AttrDict The list of detail records, categorized by detail table in which they occur. The detail tables are the keys, the lists of records in those tables are the values. If the master record cannot be found or if there are no detail records, the empty dict is returned.",
"func":1
},
{
"ref":"control.datamodel.Datamodel.getUserWork",
"url":11,
"doc":"Gets the number of project and edition records of a user. We will not delete users if the user is linked to a project or edition. This function counts how many projects and editions a user is linked to. Parameters      user: string The name of the user (field  user in the record) Returns    - integer The number of projects integer The number of editions",
"func":1
},
{
"ref":"control.datamodel.Datamodel.getLinkedCrit",
"url":11,
"doc":"Produce criteria to retrieve the linked records of a record. It finds all cross-linked records containing an id of the given record. So no detail records. Parameters      table: string The name of the table in which the record lives. record: string | ObjectId | AttrDict The record. Returns    - AttrDict Keys: tables in which linked records exist. Values: the criteria to find those linked records in that table.",
"func":1
},
{
"ref":"control.datamodel.Datamodel.makeField",
"url":11,
"doc":"Make a field object and registers it. An instance of class  control.datamodel.Field is created, geared to this particular field.  ! note \"Idempotent\" If the Field object is already registered, nothing is done. Parameters      key: string Identifier for the field. The configuration for this field will be retrieved using this key. The new field object will be stored under this key. Returns    - object The resulting Field object. It is also added to the  fieldObjects member.",
"func":1
},
{
"ref":"control.datamodel.Datamodel.getFieldObject",
"url":11,
"doc":"Get a field object. Parameters      key: string The key of the field object Returns    - object | void The field object found under the given key, if present, otherwise None",
"func":1
},
{
"ref":"control.datamodel.Datamodel.makeUpload",
"url":11,
"doc":"Make a file upload object and registers it. An instance of class  control.datamodel.Upload is created, geared to this particular field.  ! note \"Idempotent\" If the Upload object is already registered, nothing is done. Parameters      key: string Identifier for the upload. The configuration for this upload will be retrieved using this key. The new upload object will be stored under this key. fileName: string, optional None If present, it indicates that the uploaded file will have this prescribed name. A file name for an upload object may also have been specified in the datamodel configuration. Returns    - object The resulting Upload object. It is also added to the  uploadObjects member.",
"func":1
},
{
"ref":"control.datamodel.Datamodel.getUploadConfig",
"url":11,
"doc":"Get an upload config. Parameters      key: string The key of the upload config Returns    - object | void The upload config found under the given key and file name, if present, otherwise None",
"func":1
},
{
"ref":"control.datamodel.Datamodel.getUploadObject",
"url":11,
"doc":"Get an upload object. Parameters      key: string The key of the upload object fileName: string, optional None The file name of the upload object. If not passed, the file name is derived from the config of the key. Returns    - object | void The upload object found under the given key and file name, if present, otherwise None",
"func":1
},
{
"ref":"control.datamodel.Field",
"url":11,
"doc":"Handle field business. A Field object does not correspond with an individual field in a record. It represents a  column , i.e. a set of fields with the same name in all records of a table. First of all there is a method to retrieve the value of the field from a specific record. Then there are methods to deliver those values, either bare or formatted, to produce edit widgets to modify the values, and handlers to save values. How to do this is steered by the specification of the field by keys and values that are stored in this object. All field access should be guarded by the authorisation rules. Parameters      kwargs: dict Field configuration arguments. It certain parts of the field configuration are not present, defaults will be provided."
},
{
"ref":"control.datamodel.Field.logical",
"url":11,
"doc":"Give the logical value of the field in a record. Parameters      record: string | ObjectId | AttrDict The record in which the field value is stored. Returns    - any: Whatever the value is that we find for that field. No conversion/casting to other types will be performed. If the field is not present, returns None, without warning.",
"func":1
},
{
"ref":"control.datamodel.Field.bare",
"url":11,
"doc":"Give the bare string value of the field in a record. Parameters      record: string | ObjectId | AttrDict The record in which the field value is stored. Returns    - string: Whatever the value is that we find for that field, converted to string. If the field is not present, returns the empty string, without warning.",
"func":1
},
{
"ref":"control.datamodel.Field.formatted",
"url":11,
"doc":"Give the formatted value of the field in a record. Optionally also puts a caption and/or an edit control. The value retrieved is (recursively) wrapped in HTML, steered by additional argument, as in  control.html.HtmlElements.wrapValue . be applied. If the type is 'text', multiple values will simply be concatenated with newlines in between, and no extra classes will be applied. Instead, a markdown formatter is applied to the result. For other types: If the value is an iterable, each individual value is wrapped in a span to which an (other) extra CSS class may be applied. Parameters      table: string The table from which the record is taken record: string | ObjectId | AttrDict The record in which the field value is stored. level: integer, optional None The heading level in which a caption will be placed. If None, no caption will be placed. If 0, the caption will be placed in a span. editable: boolean, optional False Whether the field is editable by the current user. If so, edit controls are provided. outerCls: string optional \"fieldouter\" If given, an extra CSS class for the outer element that wraps the total value. Only relevant if the type is not 'text' innerCls: string optional \"fieldinner\" If given, an extra CSS class for the inner elements that wrap parts of the value. Only relevant if the type is not 'text' Returns    - string: Whatever the value is that we find for that field, converted to HTML. If the field is not present, returns the empty string, without warning.",
"func":1
},
{
"ref":"control.datamodel.Field.key",
"url":11,
"doc":"The identifier of this field within the app."
},
{
"ref":"control.datamodel.Field.nameSpace",
"url":11,
"doc":"The first key to access the field data in a record. Example  dc (Dublin Core). So if a record has Dublin Core metadata, we expect that metadata to exist under key  dc in that record. If the namespace is    , it is assumed that we can dig up the values without going into a namespace sub-record first."
},
{
"ref":"control.datamodel.Field.fieldPath",
"url":11,
"doc":"Compound selector in a nested dict. A string of keys, separated by  . , which will be used to drill down into a nested dict. At the end of the path we find the selected value. This field selection is applied after the name space selection (if  nameSpace is not the empty string)."
},
{
"ref":"control.datamodel.Field.tp",
"url":11,
"doc":"The value type of the field. Value types can be string, integer, but also date times, and values from an other table (value lists), or structured values."
},
{
"ref":"control.datamodel.Field.caption",
"url":11,
"doc":"A caption that may be displayed with the field value. The caption may be a literal string with or without a placeholder  {} . If there is no place holder, the caption will precede the content of the field. If there is a placeholder, the content will replace the place holder in the caption."
},
{
"ref":"control.datamodel.Upload",
"url":11,
"doc":"Handle upload business. An upload is like a field of type 'file'. The name of the uploaded file is stored in a record in MongoDb. The contents of the file is stored on the file system. A Upload object does not correspond with an individual field in a record. It represents a  column , i.e. a set of fields with the same name in all records of a table. First of all there is a method to retrieve the file name of an upload from a specific record. Then there are methods to deliver those values, either bare or formatted, to produce widgets to upload or delete the corresponding files. How to do this is steered by the specification of the upload by keys and values that are stored in this object. All upload access should be guarded by the authorisation rules. Parameters      kwargs: dict Upload configuration arguments. The following parts of the upload configuration should be present:  table ,  accept , while  caption ,  fileName ,  show are optional."
},
{
"ref":"control.datamodel.Upload.getDir",
"url":11,
"doc":"Give the path to the file in question. The path can be used to build the static url and the save url. It does not contain the file name. If the path is non-empty, a \"/\" will be appended. Parameters      record: string | ObjectId | AttrDict The record relevant to the upload",
"func":1
},
{
"ref":"control.datamodel.Upload.formatted",
"url":11,
"doc":"Give the formatted value of a file field in a record. Optionally also puts an upload control. Parameters      record: string | ObjectId | AttrDict The record relevant to the upload mayChange: boolean, optional False Whether the file may be changed. If so, an upload widget is supplied, wich contains a a delete button. bust: string, optional None If not None, the image url of the file whose name is passed in  bust is made unique by adding the current time to it. This is a cache buster. wrapped: boolean, optional True Whether the content should be wrapped in a container element. See  control.html.HtmlElements.finput() . Returns    - string The name of the uploaded file(s) and/or an upload control.",
"func":1
},
{
"ref":"control.datamodel.Upload.key",
"url":11,
"doc":"The identifier of this upload within the app."
},
{
"ref":"control.datamodel.Upload.table",
"url":11,
"doc":"Indicates the directory where the actual file will be saved. Possibe values:   site : top level of the working data directory of the site   project : project directory of the project in question   edition : edition directory of the project in question"
},
{
"ref":"control.datamodel.Upload.accept",
"url":11,
"doc":"The file types that the field accepts."
},
{
"ref":"control.datamodel.Upload.caption",
"url":11,
"doc":"The text to display on the upload button."
},
{
"ref":"control.datamodel.Upload.multiple",
"url":11,
"doc":"Whether multiple files of this type may be uploaded."
},
{
"ref":"control.datamodel.Upload.fileName",
"url":11,
"doc":"The name of the file once it is uploaded. The file name for the upload can be passed when the file name is known in advance. In that case, a file that is uploaded in this upload widget, will get this as prescribed file name, regardless of the file name in the upload request. Without a file name, the upload widget will show all existing files conforming to the  accept setting, and will have a control to upload a new file."
},
{
"ref":"control.datamodel.Upload.show",
"url":11,
"doc":"Whether to show the contents of the file. This is typically the case when the file is an image to be presented as a logo."
},
{
"ref":"control.tailwind",
"url":12,
"doc":""
},
{
"ref":"control.tailwind.Tailwind",
"url":12,
"doc":""
},
{
"ref":"control.tailwind.Tailwind.install",
"url":12,
"doc":"",
"func":1
},
{
"ref":"control.tailwind.Tailwind.generate",
"url":12,
"doc":"Generate the css file. Issues: The following CSS definitions are found in the content of  _dist , but not in the content of  components ,  js , and  templates . We investigate these cases and explain what we do about it.   .container  @media The  container class is triggered by the occurrence of the word  container in the HTML content in one of the article files. This is a false positive, it was better if tailwind had not found this. Luckily, we loose these false positives if we generate on the basis of the templates. The  @media definitions accompany the  container definition.   .visible ,  fixed ,  table ,  ring Each of these are analogous to  container : if the word  visible occurrs in HTML content, its CSS class definition is inserted in the generated CSS.   order-2,3,4,5,6,7 This is a case of a generated class, one of the templates contains  order- @index  where index varies. We solve this by putting [all possible  order- classes](https: tailwindcss.com/docs/order) in the [safelist](https: tailwindcss.com/docs/content-configuration safelisting-classes).   .h-4  .w-4  .fill-blue-700 This is also a case of generated classes, in many of the icon templates:  class=\" w-  if twSize  twSize  else 6 /if h-  if twSize  twSize  else 6 /if   if twColor fill- twColor  /if  \"  The  p3d-project and  p3d-edition templates define the variables  twSize and  twColor as follows:    >icons/iconChevronLeft isFill=true twSize=\"4\" twColor=\"blue-700\" All projects   So far, only these values ( 4 resp  blue-700 are specified, to we add  w-4 and  h-4 and  fill-blue-700 to the safelist.",
"func":1
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
"ref":"control.precheck",
"url":14,
"doc":""
},
{
"ref":"control.precheck.Precheck",
"url":14,
"doc":"All about checking the files of an edition prior to publishing."
},
{
"ref":"control.precheck.Precheck.checkEdition",
"url":14,
"doc":"Checks the article and media files in an editon and produces a toc. Articles and media are files and directories that the user creates through the Voyager interface. Before publishing we want to make sure that these files pass some basic sanity checks:  All links in the articles are either external links, or they point at an existing file within the edition.  All non-html files are referred to by a link in an html file. Not meeting this requirement does not block publishing, but unreferenced files will not be published. We also create a table of contents of all html files in the edition, so they can be inspected outside the Voyager. To that, we add a table of the media files, together with the information which html files refer to them. The table of contents in the Pure3d author app is slightly different from that in the Pure3d pub app, because the internal links work differently. You can trigger the generation of a toc that works for the published edition as well. Parameters      project: string | ObjectId | AttrDict | int The id of the project in question. edition: string | ObjectId | AttrDict | int The id of the edition in question. asPublished: boolean, optional False If False, the project and edition refer to the edition in the Pure3D author app, and the toc file will be created there. If True, the project and edition are numbers that refer to the published edition; it is assumed that all checks pass and the only task is to create a toc that is valid in the published edition. Returns    - boolean | string If  asPublished is True, it returns the toc as a string, otherwise it returns whether the edition passed all checks.",
"func":1
},
{
"ref":"control.pages",
"url":15,
"doc":""
},
{
"ref":"control.pages.Pages",
"url":15,
"doc":"Making responses that can be displayed as web pages. This class has methods that correspond to routes in the app, for which they get the data (using  control.content.Content ), which gets then wrapped in HTML. It is instantiated by a singleton object. Most methods generate a response that contains the content of a complete page. For those methods we do not document the return value. Some methods return something different. If so, it the return value will be documented. Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Viewers: object Singleton instance of  control.viewers.Viewers . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo . Content: object Singleton instance of  control.content.Content . Auth: object Singleton instance of  control.auth.Auth ."
},
{
"ref":"control.pages.Pages.precheck",
"url":15,
"doc":"Check the articles of an edition prior to publishing. Parameters      edition: string the edition After the operation: Goes back to the referrer url. The check operation will have generated a table of contents for the articles and media files, and these will be shown on the edition page. Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.publish",
"url":15,
"doc":"Publish an edition as static pages. Parameters      edition: string the edition force: boolean If True, ignore when some checks fail After the operation:   success : goes back to referrer url, good status   failure : goes back to referrer url, error status Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.republish",
"url":15,
"doc":"Re-publish an edition as static pages. Parameters      edition: string the edition force: boolean If True, ignore when some checks fail After the operation:   success : goes back to referrer url, good status   failure : goes back to referrer url, error status Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.unpublish",
"url":15,
"doc":"Unpublish an edition from the static pages. Parameters      edition: string the edition After the operation:   success : goes back to referrer url, good status   failure : goes back to referrer url, error status Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.generate",
"url":15,
"doc":"Regenerate the static HTML pages for the whole published site. After the operation:   success : goes back to referrer url, good status   failure : goes back to referrer url, error status Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.mkBackup",
"url":15,
"doc":"Backup: Save file and database data in a backup directory. Parameters      project: string, optional None If given, only backs up the given project. After the operation:   success : goes back to referrer url, good status   failure : goes back to referrer url, error status Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.restore",
"url":15,
"doc":"Restore from a backup. Make a new backup first. After the operation:   success :  site-wide restore: goes to logout url, good status  project-specific restore: goes to project url, good status   failure : goes back to referrer url, error status Parameters      backup: string The name of the backup as stored in the backups directory on the server. project: string, optional None If given, restores the given project. Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.delBackup",
"url":15,
"doc":"Deletes a backup. After the operation:   success : goes back to referrer url, good status   failure : goes back to referrer url, error status Parameters      backup: string The name of the backup as stored in the backups directory on the server. project: string, optional None If given, deletes a backup of the given project. Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.home",
"url":15,
"doc":"The site-wide home page. Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.about",
"url":15,
"doc":"The site-wide about page. Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.surprise",
"url":15,
"doc":"The \"surprise me!\" page. Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.projects",
"url":15,
"doc":"The page with the list of projects. Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.admin",
"url":15,
"doc":"The page with the list of projects, editions, and users. Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.createUser",
"url":15,
"doc":"Creates a new test user. After the operation:   success : goes to admin url, good status   failure : goes to admin url, error status Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.deleteUser",
"url":15,
"doc":"Deletes a test user. After the operation:   success : goes to admin url, good status   failure : goes to admin url, error status Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.createProject",
"url":15,
"doc":"Creates a project and shows the new project. The current user is linked to this project as organiser. After the operation:   success : goes to new project url, good status   failure : goes to all projects url, error status Returns    - response Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.project",
"url":15,
"doc":"The landing page of a project. Parameters      project: string | ObjectId | AttrDict The project in question. Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.createEdition",
"url":15,
"doc":"Inserts an edition into a project and shows the new edition. The current user is linked to this edition as editor. After the operation:   success : goes to new edition url, good status   failure : goes to project url, error status Returns    - response Parameters      project: string | ObjectId | AttrDict The project to which the edition belongs. Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.edition",
"url":15,
"doc":"The landing page of an edition, possibly with a scene marked as active. An edition knows the scene it should display and the viewer that was used to create the scene. If action is not None, its value determines which viewer will be loaded in the 3D viewer. It is dependent on the parameters and/or defaults in which viewer/version/mode. If version is not None, this will override the default version. Parameters      edition: string | ObjectId | AttrDict The editionin quesion. From the edition record we can find the project too. version: string, optional None The viewer version to use. action: string, optional None The mode in which the viewer is to be used ( read or  update ). Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.fromPub",
"url":15,
"doc":"Redirect to a project or edition or the home page. If the edition or project does not exist, show a friendly message.",
"func":1
},
{
"ref":"control.pages.Pages.deleteItem",
"url":15,
"doc":"Deletes an item, project or edition. After the operation:   success : goes to all-projects url or master project url, good status   failure : goes to back referrer url, error status Parameters      table: string The kind of item:  project or  edition . record: string | ObjectId | AttrDict The item in question. Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.viewerFrame",
"url":15,
"doc":"The page loaded in an iframe where a 3D viewer operates. Parameters      edition: string | ObjectId | AttrDict The edition that is shown. version: string | None The version to use. action: string | None The mode in which the viewer is to be used ( read or  update ). subMode: string | None The sub mode in which the viewer is to be used ( update or  create ). Returns    - response",
"func":1
},
{
"ref":"control.pages.Pages.viewerResource",
"url":15,
"doc":"Components requested by viewers. This is the javascript code, the css, and other resources that are part of the 3D viewer software. Parameters      path: string Path on the file system under the viewers base directory where the resource resides. Returns    - response The response consists of the contents of the file plus headers derived from the path. If the file does not exist, a 404 is returned.",
"func":1
},
{
"ref":"control.pages.Pages.fileData",
"url":15,
"doc":"Data content requested directly from the file repository. This is  the material requested by the viewers: the scene json itself and additional resources, that are part of the user contributed content that is under control of the viewer: annotations, media, etc.  icons for the site, projects, and editions Parameters      path: string Path on the file system under the data directory where the resource resides. The path is relative to the project, and, if given, the edition. project: string | ObjectId | AttrDict The id of a project under which the resource is to be found. If None, it is site-wide material. edition: string | ObjectId | AttrDict If not None, the name of an edition under which the resource is to be found. Returns    - response The response consists of the contents of the file plus headers derived from the path. If the file does not exist, a 404 is returned.",
"func":1
},
{
"ref":"control.pages.Pages.upload",
"url":15,
"doc":"Upload a file. Parameters      record: string | ObjectId | AttrDict The context record of the upload key: string The key of the upload path: string The save location for the file targetFileName: string, optional None The name of the file as which the uploaded file will be saved; if is None, the file will be saved with the name from the request. Returns    - response With json data containing a status and a content member. The content is new content to display the upload widget with.",
"func":1
},
{
"ref":"control.pages.Pages.deleteFile",
"url":15,
"doc":"Delete a file. Parameters      record: string | ObjectId | AttrDict The context record of the upload. key: string The key of the upload. path: string The location of the file. targetFileName: string, optional None The name of the file. Returns    - response With json data containing a status, msg, and content members. The content is new content to display the upload widget with.",
"func":1
},
{
"ref":"control.pages.Pages.authWebdav",
"url":15,
"doc":"Authorises a webdav request. When a viewer makes a WebDAV request to the server, that request is first checked here for authorisation. See  control.webdavapp.dispatchWebdav() . Parameters      edition: string | ObjectId | AttrDict The edition in question. path: string The path relative to the directory of the edition. action: string The operation that the WebDAV request wants to do on the data ( read or  update ). Returns    - boolean Whether the action is permitted on ths data by the current user.",
"func":1
},
{
"ref":"control.pages.Pages.remaining",
"url":15,
"doc":"When the url of the request is not recognized. Parameters      path: string The url (without leading /) that is not recognized. Returns    - response Either a redirect to the referred, for some recognized urls that correspond to not-yet implemented one. Or a 404 abort for all other cases.",
"func":1
},
{
"ref":"control.pages.Pages.page",
"url":15,
"doc":"Workhorse function to get content on the page. Parameters      url: string Initial part of the url that triggered the page function. This part is used to make one of the tabs on the web page active. left: string, optional None Content for the left column of the page. right: string, optional None Content for the right column of the page.",
"func":1
},
{
"ref":"control.pages.Pages.navigation",
"url":15,
"doc":"Generates the navigation controls. Especially the tab bar. Parameters      url: string Initial part of the url on the basis of which one of the tabs can be made active. Returns    - string The HTML of the navigation.",
"func":1
},
{
"ref":"control.content",
"url":16,
"doc":""
},
{
"ref":"control.content.Content",
"url":16,
"doc":"Retrieving content from database and file system. This class has methods to retrieve various pieces of content from the data sources, and hand it over to the  control.pages.Pages class that will compose a response out of it. It is instantiated by a singleton object. Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Viewers: object Singleton instance of  control.viewers.Viewers . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo . Wrap: object Singleton instance of  control.wrap.Wrap ."
},
{
"ref":"control.content.Content.addAuth",
"url":16,
"doc":"Give this object a handle to the Auth object. Because of cyclic dependencies some objects require to be given a handle to Auth after their initialization.",
"func":1
},
{
"ref":"control.content.Content.addPublish",
"url":16,
"doc":"Give this object a handle to the Publish object. Because of cyclic dependencies some objects require to be given a handle to Publish after their initialization.",
"func":1
},
{
"ref":"control.content.Content.getSurprise",
"url":16,
"doc":"Get the data that belongs to the surprise-me functionality.",
"func":1
},
{
"ref":"control.content.Content.getProjects",
"url":16,
"doc":"Get the list of all projects. Well, the list of all projects visible to the current user. Unpublished projects are only visible to users that belong to that project. Visible projects are each displayed by means of an icon and a title. Both link to a landing page for the project. Returns    - string A list of captions of the projects, wrapped in a HTML string.",
"func":1
},
{
"ref":"control.content.Content.getEditions",
"url":16,
"doc":"Get the list of the editions of a project. Well, only if the project is visible to the current user. See  Content.getProjects() . Editions are each displayed by means of an icon and a title. Both link to a landing page for the edition. Parameters      project: string | ObjectId | AttrDict The project in question. Returns    - string A list of captions of the editions of the project, wrapped in a HTML string.",
"func":1
},
{
"ref":"control.content.Content.getScene",
"url":16,
"doc":"Get the scene of an edition of a project. Well, only if the current user is authorised. A scene is displayed by means of an icon and a row of buttons. There are also buttons to upload model files and the scene file. If action is not None, the scene is loaded in a specific version of the viewer in a specific mode ( read or  edit ). The edition knows which viewer to choose. Which version and which mode are used is determined by the parameters. If the parameters do not specify values, sensible defaults are chosen. Parameters      projectId: ObjectId The id of the project to which the edition belongs. edition: string | ObjectId | AttrDict The edition in question. version: string, optional None The version of the chosen viewer that will be used. If no version or a non-existing version are specified, the latest existing version for that viewer will be chosen. action: string, optional read The mode in which the viewer should be opened. If the mode is  update , the viewer is opened in edit mode, if the scene file exists, otherwise in create mode, which, in case of the Voyager viewer, means  dragdrop mode, in older versions  standalone . All other modes lead to the viewer being opened in read-only mode. If the mode is read-only, but the scene file is missing, no viewer will be opened. Returns    - string A caption of the scene of the edition, with possibly a frame with the 3D viewer showing the scene. The result is wrapped in a HTML string.",
"func":1
},
{
"ref":"control.content.Content.getAdmin",
"url":16,
"doc":"Get the list of relevant projects, editions and users. Admin users get the list of all users. Normal users get the list of users associated with  the project of which they are organiser  the editions of which they are editor or reviewer Guests and not-logged-in users cannot see any user. If the user has rights to modify the association between users and projects/editions, he will get the controls to do so. Returns    - string",
"func":1
},
{
"ref":"control.content.Content.createProject",
"url":16,
"doc":"Creates a new project. Parameters      site: AttrDict | string record that represents the site, or its id. It acts as a master record for all projects. Returns    - ObjectId The id of the new project.",
"func":1
},
{
"ref":"control.content.Content.deleteItem",
"url":16,
"doc":"Deletes an item, project or edition. Parameters      table: string The kind of item:  project or  edition . record: string | ObjectId | AttrDict The item in question. Returns    - boolean Whether the deletion was successful.",
"func":1
},
{
"ref":"control.content.Content.createEdition",
"url":16,
"doc":"Creates a new edition. Parameters      project: AttrDict | string record that represents the maste project, or its id. Returns    - ObjectId The id of the new edition.",
"func":1
},
{
"ref":"control.content.Content.saveValue",
"url":16,
"doc":"Saves a value of into a record. A record is a document, which is a (nested) dict. A value is inserted somewhere (deep) in that dict. The value is given by the request. Where exactly is given by a path that is stored in the field information, which is accessible by the key. Parameters      table: string The relevant table. record: string | ObjectId | AttrDict | void The relevant record. key: string an identifier for the meta data field. Returns    - dict Contains the following keys:   status : whether the save action was successful   messages : messages issued during the process   readonly : the html of the updated formatted value, this will replace the currently displayed value.",
"func":1
},
{
"ref":"control.content.Content.saveRole",
"url":16,
"doc":"Saves a role into a user or cross table record. The role is given by the request. Parameters      user: string The eppn of the user. table: string | void The relevant table. If not None, it indicates whether we are updating site-wide roles, otherwise project/edition roles. recordId: string | void The id of the relevant record. If not None, it is a project/edition record Id, which can be used to locate the cross record between the user table and the project/edition record where the user's role is stored. If None, the user's role is inside the user record. Returns    - dict Contains the following keys:   status : whether the save action was successful   messages : messages issued during the process   updated : if the action was successful, all user management info will be passed back and will replace the currently displayed material.",
"func":1
},
{
"ref":"control.content.Content.createUser",
"url":16,
"doc":"Creates a new user with a given user name. Parameters      user: string The user name of the user. This should be different from the user names of existing users. Returns    - dict Contains the following keys:   status : whether the create action was successful   messages : messages issued during the process   name : the name under which the new user has been saved",
"func":1
},
{
"ref":"control.content.Content.deleteUser",
"url":16,
"doc":"Deletes a test user with a given user name. Parameters      user: string The user name of the user. This should be a test user, not linked to any project or edition. Returns    - dict Contains the following keys:   status : whether the create action was successful   messages : messages issued during the process",
"func":1
},
{
"ref":"control.content.Content.linkUser",
"url":16,
"doc":"Links a user in certain role to a project/edition record. The user and role are given by the request. Parameters      table: string The relevant table. recordId: string The id of the relevant record, which can be used to locate the cross record between the user table and the project/edition record where the user's role is stored. Returns    - dict Contains the following keys:   status : whether the save action was successful   messages : messages issued during the process   updated : if the action was successful, all user management info will be passed back and will replace the currently displayed material.",
"func":1
},
{
"ref":"control.content.Content.getValue",
"url":16,
"doc":"Retrieve a metadata value. Metadata sits in a big, potentially deeply nested dictionary of keys and values. These locations are known to the system (based on  fields.yml ). This function retrieves the information from those known locations. If a value is in fact composed of multiple values, it will be handled accordingly. If the user may edit the value, an edit button is added. Parameters      key: string an identifier for the meta data field. table: string The relevant table. record: string | ObjectId | AttrDict | void The relevant record. level: string, optional None The heading level with which the value should be formatted.   0 : No heading level   None : no formatting at all manner: string, optional wrapped If it is \"formatted\", the value is represented fully wrapped in HTML, possibly with edit/save controls. If it is \"bare\", the value is represented as a simple string. If it is \"logical\", the logical value is returned. Returns    - string It is assumed that the metadata value that is addressed exists. If not, we return the empty string.",
"func":1
},
{
"ref":"control.content.Content.getValues",
"url":16,
"doc":"Puts several pieces of metadata on the web page. Parameters      fieldSpecs: string  , -separated list of fieldSpecs table: string The relevant table record: string | ObjectId | AttrDict | void The relevant record Returns    - string The join of the individual results of retrieving metadata value.",
"func":1
},
{
"ref":"control.content.Content.getUpload",
"url":16,
"doc":"Display the name and/or upload controls of an uploaded file. The user may upload model files and a scene file to an edition, and various png files as icons for projects, edtions, and scenes. Here we produce the control to do so. Only if the user has  update authorisation, an upload/delete widget will be returned. Parameters      record: string | ObjectId | AttrDict | void The relevant record. key: string an identifier for the upload field. fileName: string, optional None If present, it indicates that the uploaded file will have this prescribed name. A file name for an upload object may also have been specified in the datamodel configuration. bust: string, optional None If not None, the image url of the file whose name is passed in  bust is made unique by adding the current time to it. That will bust the cache for the image, so that uploaded images replace the existing images. This is useful when this function is called to provide udated content for an file upload widget after it has been used to successfully upload a file. The file name of the uploaded file is known, and that is the one that gets a cache buster appended. wrapped: boolean, optional True Whether the content should be wrapped in a container element. See  control.html.HtmlElements.finput() . Returns    - string The name of the file that is currently present, or the indication that no file is present. If the user has edit permission for the edition, we display widgets to upload a new file or to delete the existing file.",
"func":1
},
{
"ref":"control.content.Content.getBackups",
"url":16,
"doc":"Produce a backup button and an overview of existing backups. Only if it is relevant to the current user in the current run mode. The existing backups will be presented as link: a click will trigger a restore from that backup. There will also be delete buttons for each backup. Parameters      project: AttrDict | ObjectId | string, optional None If None, we deal with site-wide backup. Otherwise we get the backups of this project.",
"func":1
},
{
"ref":"control.content.Content.getDownload",
"url":16,
"doc":"Display the name and/or upload controls of an uploaded file. The user may upload model files and a scene file to an edition, and various png files as icons for projects, edtions, and scenes. Here we produce the control to do so. Only if the user has  update authorisation, an upload/delete widget will be returned. Parameters      table: string The table in which the relevant record sits record: string | ObjectId | AttrDict The relevant record. Returns    - string The name of the file that is currently present, or the indication that no file is present. If the user has edit permission for the edition, we display widgets to upload a new file or to delete the existing file.",
"func":1
},
{
"ref":"control.content.Content.getPublishInfo",
"url":16,
"doc":"Display the number under which a project/edition is published. Editions of a project may have been published. If that is the case, the project has been assigned a sequence number, under which it can be found on the static site with published material. Here we collect that number, and, for editions, we may put a publish button here. Parameters      table: string The table in which the relevant record sits record: string | ObjectId | AttrDict The relevant record. Returns    - string In case of a project: the number of the project on the static site. In case of an edition: the number of the project and the number of the edition on the static site. If the edition is not yet published, and the user is allowed to publish the edition, then a publish button is also added.",
"func":1
},
{
"ref":"control.content.Content.getViewerFile",
"url":16,
"doc":"Gets a viewer-related file from the file system. This is about files that are part of the viewer software. The viewer software is located in a specific directory on the server. This is the viewer base. Parameters      path: string The path of the viewer file within viewer base. Returns    - string The full path to the viewer file, if it exists. Otherwise, we raise an error that will lead to a 404 response.",
"func":1
},
{
"ref":"control.content.Content.getDataFile",
"url":16,
"doc":"Gets a data file from the file system. All data files are located under a specific directory on the server. This is the data directory. Below that the files are organized by projects and editions. Projects and editions corresponds to records in tables in MongoDB. Parameters      path: string The path of the data file within site/project/edition directory within the data directory. project: string | ObjectId | AttrDict The id of the project in question. edition: string | ObjectId | AttrDict The id of the edition in question. content: boolean, optional False If True, delivers the content of the file, instead of the path lenient: boolean, optional False If True, do not complain if the file does not exist. Returns    - string The full path of the data file, if it exists. But if the  content parameter is True, we deliver the content of the file. Otherwise, we raise an error that will lead to a 404 response, except when  lenient is True.",
"func":1
},
{
"ref":"control.content.Content.breadCrumb",
"url":16,
"doc":"Makes a link to the landing page of a project. Parameters      project: string | ObjectId | AttrDict The project in question.",
"func":1
},
{
"ref":"control.content.Content.mkBackup",
"url":16,
"doc":"Makes a backup of data as found in files and db. We do site-wide backups and project-specific backups. Site-wide backups take the complete working directory on the file system, and the complete relevant database in MongoDb. Project-specific backups take only the project directory on the file system, and the relevant project record plus the relevant edition records in MongoDb.  ! caution \"Site-wide backups affect user data\" The set of users and their permissions may be different across backups. After restoring a snaphot, the user that restored it may no longer exist, or have different rights.  ! caution \"Project backups do not affect user data\" No user data nor any coupling between users and the project and its editions are modified. A consequence is that a backup may contain editions that do not exist anymore and to which no users are coupled. It may be needed to assign current users to editions after a restore. Backups are stored in the data directory of the server under  backups and then the run mode ( pilot ,  test ,  prod ). The site-wide backups are stores under  site , the project backups under  project/ projectId . The directory name of the backup is the current date-time up to the second in iso format, but with the  : replaced by  - . Below that we have directories:   files : contains the complete contents of the working directory of the current run mode.   db : a backup of the complete contents of the MongoDb database of the current run mode. In there again a subdivision:  [ bson ](https: www.mongodb.com/basics/bson)   json The name indicates the file format of the backup. In both cases, the data ends up in folders per table, and within those folders we have files per record. Parameters      project: string, optional None If given, only backs up the given project.",
"func":1
},
{
"ref":"control.content.Content.restore",
"url":16,
"doc":"Restores data to files and db, from a backup. See also  mkBackup() . First a new backup of the current situation will be made. Parameters      backup: string Name of a backup. The backup must exist. project: string, optional None If given, only restores the given project.",
"func":1
},
{
"ref":"control.content.Content.delBackup",
"url":16,
"doc":"Deletes a backup. See also  mkBackup() . Parameters      backup: string Name of a backup. The backup must exist. project: string, optional None If given, only deletes the backup of this project.",
"func":1
},
{
"ref":"control.content.Content.precheck",
"url":16,
"doc":"Check the articles of an edition prior to publishing. Parameters      record: string The record of the edition to be checked. Return    response A status response. It will also generate a a bunch of toc files in the edition.",
"func":1
},
{
"ref":"control.content.Content.publish",
"url":16,
"doc":"Publish an edition. Parameters      record: string The record of the item to be published. force: boolean If True, ignore when some checks fail Return    response A publish status response.",
"func":1
},
{
"ref":"control.content.Content.republish",
"url":16,
"doc":"Re-ublish an edition. Parameters      record: string The record of the item to be re-published. force: boolean If True, ignore when some checks fail Return    response A re-publish status response.",
"func":1
},
{
"ref":"control.content.Content.unpublish",
"url":16,
"doc":"Unpublish an edition. Parameters      record: string The record of the item to be unpublished. Return    response An unpublish status response.",
"func":1
},
{
"ref":"control.content.Content.generate",
"url":16,
"doc":"Regenerate the HTML for the published site. Return    response A publish status response.",
"func":1
},
{
"ref":"control.content.Content.download",
"url":16,
"doc":"Responds with a download of a project or edition. Parameters      table: string The table where the item to be downloaded sits. record: string The record of the item to be downloaded. Return    response A download response.",
"func":1
},
{
"ref":"control.content.Content.saveFile",
"url":16,
"doc":"Saves a file in the context given by a record. The parameter  key refers to a configuration section in the datamodel. This determines what file type to expect. We only accept files whose name has an extension that matches the expected file type. The key  modelz expects a zip file with the files of an edition, in particular a scene file and model files. We make sure that these files have the proper type, and we also perform checks on the other parts of the zip file, namely whether they have decent paths. Parameters      record: string | ObjectId | AttrDict | void The relevant record. key: string The upload key path: string The path from the context directory to the file fileName: string Name of the file to be saved as mentioned in the request. targetFileName: string, optional None The name of the file as which the uploaded file will be saved; if None, the file will be saved with the name from the request. Return    response A json response with the status of the save operation:  a boolean: whether the save succeeded  a list of messages to display  content: new content for an upload control (only if successful)",
"func":1
},
{
"ref":"control.content.Content.checkFileContent",
"url":16,
"doc":"Performs checks on the name and content of an uploaded file before saving it. Parameters      key: string The key of the upload. This key determines what kind of file we expect. If None, we do not expect a particular mime type targetFileName: string The prescribed name to save the file under, if None, it will be saved under the name mentioned in the request. fileName: string The name of the file as mentioned in the request. fileContent: bytes The content of the file as bytes Returns    - tuple A boolean that tells whether the file content looks OK plus a sequences of messages indicating what is wrong with the content.",
"func":1
},
{
"ref":"control.content.Content.processModelZip",
"url":16,
"doc":"Processes zip data with a scene and model files. All files in the zip file will be examined, and those with extension svx.json will be saved as scene.svx.json at top level and those with extensions glb of gltf will be saved under their own names, also at top level. All other files will be saved as is, unless they have extension .svx.json, or .gltf or .glb. These files can end up in subdirectories. We do not check the file types of the member files other than the svx.json files and the model files (glb, gltf). If the file type for these files does not match their extensions, they will be ignored. The user is held responsible to submit a suitable file. Parameters      zf: bytes The raw zip data",
"func":1
},
{
"ref":"control.content.Content.deleteFile",
"url":16,
"doc":"Deletes a file in the context given by a record. Parameters      record: string | ObjectId | AttrDict | void The relevant record. key: string The upload key path: string The path from the context directory to the file fileName: string Name of the file to be saved as mentioned in the request. targetFileName: string, optional None The name of the file as which the uploaded file will be saved; if None, the file will be saved with the name from the request. Return    response A json response with the status of the save operation:  a boolean: whether the save succeeded  a message: messages to display  content: new content for an upload control (only if successful)",
"func":1
},
{
"ref":"control.content.Content.relevant",
"url":11,
"doc":"Get a relevant record and the table to which it belongs. A relevant record is either a project record, or an edition record, or the one and only site record. If all optional parameters are None, we look for the site record. If the project parameter is not None, we look for the project record. This is the inverse of  context() . Paramenters      - project: string | ObjectId | AttrDict, optional None The project whose record we need. edition: string | ObjectId | AttrDict, optional None The edition whose record we need. Returns    - tuple  table: string; the table in which the record is found  record id: string; the id of the record  record: AttrDict; the record itself If both project and edition are not None",
"func":1
},
{
"ref":"control.content.Content.context",
"url":11,
"doc":"Get the context of a record. Get the project and edition records to which the record belongs. Parameters      table: string The table in which the record sits. record: string The record. This is the inverse of  relevant() . Returns    - tuple of tuple (siteId, site, projectId, project, editionId, edition)",
"func":1
},
{
"ref":"control.content.Content.getDetailRecords",
"url":11,
"doc":"Retrieve the detail records of a master record. It finds all records that have a field containing an id of the given master record. But not those in cross-link records. Details are not retrieved recursively, only the direct details of a master are fetched. Parameters      masterTable: string The name of the table in which the master record lives. master: string | ObjectId | AttrDict The master record. Returns    - AttrDict The list of detail records, categorized by detail table in which they occur. The detail tables are the keys, the lists of records in those tables are the values. If the master record cannot be found or if there are no detail records, the empty dict is returned.",
"func":1
},
{
"ref":"control.content.Content.getUserWork",
"url":11,
"doc":"Gets the number of project and edition records of a user. We will not delete users if the user is linked to a project or edition. This function counts how many projects and editions a user is linked to. Parameters      user: string The name of the user (field  user in the record) Returns    - integer The number of projects integer The number of editions",
"func":1
},
{
"ref":"control.content.Content.getLinkedCrit",
"url":11,
"doc":"Produce criteria to retrieve the linked records of a record. It finds all cross-linked records containing an id of the given record. So no detail records. Parameters      table: string The name of the table in which the record lives. record: string | ObjectId | AttrDict The record. Returns    - AttrDict Keys: tables in which linked records exist. Values: the criteria to find those linked records in that table.",
"func":1
},
{
"ref":"control.content.Content.makeField",
"url":11,
"doc":"Make a field object and registers it. An instance of class  control.datamodel.Field is created, geared to this particular field.  ! note \"Idempotent\" If the Field object is already registered, nothing is done. Parameters      key: string Identifier for the field. The configuration for this field will be retrieved using this key. The new field object will be stored under this key. Returns    - object The resulting Field object. It is also added to the  fieldObjects member.",
"func":1
},
{
"ref":"control.content.Content.getFieldObject",
"url":11,
"doc":"Get a field object. Parameters      key: string The key of the field object Returns    - object | void The field object found under the given key, if present, otherwise None",
"func":1
},
{
"ref":"control.content.Content.makeUpload",
"url":11,
"doc":"Make a file upload object and registers it. An instance of class  control.datamodel.Upload is created, geared to this particular field.  ! note \"Idempotent\" If the Upload object is already registered, nothing is done. Parameters      key: string Identifier for the upload. The configuration for this upload will be retrieved using this key. The new upload object will be stored under this key. fileName: string, optional None If present, it indicates that the uploaded file will have this prescribed name. A file name for an upload object may also have been specified in the datamodel configuration. Returns    - object The resulting Upload object. It is also added to the  uploadObjects member.",
"func":1
},
{
"ref":"control.content.Content.getUploadConfig",
"url":11,
"doc":"Get an upload config. Parameters      key: string The key of the upload config Returns    - object | void The upload config found under the given key and file name, if present, otherwise None",
"func":1
},
{
"ref":"control.content.Content.getUploadObject",
"url":11,
"doc":"Get an upload object. Parameters      key: string The key of the upload object fileName: string, optional None The file name of the upload object. If not passed, the file name is derived from the config of the key. Returns    - object | void The upload object found under the given key and file name, if present, otherwise None",
"func":1
},
{
"ref":"control.admin",
"url":17,
"doc":""
},
{
"ref":"control.admin.Admin",
"url":17,
"doc":"Get the list of relevant projects, editions and users. Admin users get the list of all users. Normal users get the list of users associated with  the project of which they are organiser  the editions of which they are editor or reviewer Guests and not-logged-in users cannot see any user. If the user has rights to modify the association between users and projects/editions, he will get the controls to do so. Upon initialization the project/edition/user data will be read and assembled in a form ready for generating html.  Overview of assembled data  projects All project records in the system, keyed by id. If a project has editions, the editions are available under key  editions as a dict of edition records keyed by id. If a project has users, the users are available under key  users as a dict keyed by user id and valued by the user records. If an edition has users, the users are available under key  users as a dict keyed by role and then by user id and valued by a tuple of the user record and his role.  users All user records in the system, keyed by id.  myIds All project and edition ids to which the current user has a relationship. It is a dict with keys  project and  edition and the values are sets of ids."
},
{
"ref":"control.admin.Admin.update",
"url":17,
"doc":"Reread the tables of users, projects, editions. Typically needed when you have used an admin function to perform a user administration action. This may change the permissions and hence the visiblity of projects and editions. It also changes the possible user management actions in the future.",
"func":1
},
{
"ref":"control.admin.Admin.authUser",
"url":17,
"doc":"Check whether a user may change the role of another user. The questions are: \"which  other site-wide roles can the current user assign to the other user?\" (when no table or record is given). \"which project/edition scoped roles can the current user assign to or remove from the other user with respect to the relevant record in the given table?\". Note that the current site-wide role of the other user is never included in the set of resulting roles. There are also additional business rules. This function will return the empty set if these rules are violated.  Business rules  Users have exactly one site-wise role.  Users may demote themselves.  Users may not promote themselves unless  . see later.  Users may have zero or one project/edition-scoped role per project/edition  When assigning new site-wide or project/edition-scoped roles, these roles must be valid roles for that scope.  When assigning a new site-wide role, None is not one of the possible new roles: you cannot change the status of an authenticated user to \"not logged in\".  When assigning project/edition scoped roles, removing such a role from a user for a certain project/edition means that the other user is removed from that project or edition.  Roles are ranked in power. Users with a higher role are also authorised to all things for which lower roles give authorisation. The site-wide roles are ranked as:  root - admin - user - guest - not logged in  The project/edition roles are ranked as:  (project) organiser - (edition) editor - (edition) reviewer  Site-wide power does not automatically carry over to project/edition-scoped power.  Users cannot promote or demote people that are currently as powerful as themselves.  In normal cases there is exactly one root, but:  If a situation occurs that there is no root and no admin, any authenticated user my grab the role of admin.  If a situation occurs that there is no root, any admin may grab the role of root.  Roots may appoint admins.  Roots and admins may change site-wide roles.  Roots and admins may appoint project organisers, but may not assign edition-scoped roles.  Project organisers may appoint edition editors and reviewers.  Edition editors may appoint edition reviewers.  However, roots and admins may also be project organisers and edition editors for some projects and some editions.  Normal users and guests can not administer site-wide roles.  Guests can not be put in project/edition-scoped roles. Parameters      otherUser: string | void the other user as string (eppn) If None, the question is: what are the roles in which an other user may be put wrt to this project/edition? table: string, optional None the relevant table:  project or  edition ; this is the table in which the record sits relative to which the other user will be assigned a role. If None, the role to be assigned is a site wide role. record: ObjectId | AttrDict, optional None the relevant record; it is the record relative to which the other user will be assigned an other role. If None, the role to be assigned is a site wide role. Returns    - boolean, frozenset The boolean indicates whether the current user may modify the role of the target user. The frozenset is the set of assignable roles to the other user by the current user with respect to the given table and record or site-wide. If the boolean is false, the frozenset is empty. But if the frozenset is empty it might be the case that the current user is allowed to remove the role of the target user.",
"func":1
},
{
"ref":"control.admin.Admin.wrap",
"url":17,
"doc":"Produce a list of projects and editions and users for root/admin usage. The first overview shows all projects and editions with their associated users and roles. Only items that are relevant to the user are shown. If the user is authorised to change associations between users and items, they will be editable. The second overview is for admin/roots only. It shows a list of users and their site-wide roles, which can be changed.",
"func":1
},
{
"ref":"control.admin.Admin.saveRole",
"url":17,
"doc":"Saves a role into a user or cross table record. It will be checked whether the new role is valid, and whether the user has permission to perform this role assignment. Parameters      u: string The eppn of the user. newRole: string | void The new role for the target user. None means: the target user will lose his role. table: string Either None or  project or  edition , indicates what users we are listing: site-wide users or users related to a project or to an edition. recordId: ObjectId or None Either None or the id of a project or edition, corresponding to the  table parameter. Returns    - dict with keys:   stat : indicates whether the save may proceed;   messages : list of messages for the user,   updated : new content for the user managment div.",
"func":1
},
{
"ref":"control.admin.Admin.linkUser",
"url":17,
"doc":"Links a user in certain role to a project/edition record. It will be checked whether the new role is valid, and whether the user has permission to perform this role assignment. If the user is already linked to that project/edition, his role will be updated, otherwise a new link will be created. Parameters      u: string The eppn of the target user. newRole: string The new role for the target user. table: string Either  project or  edition . recordId: ObjectId The id of a project or edition, corresponding to the  table parameter. Returns    - dict with keys:   stat : indicates whether the save may proceed;   messages : list of messages for the user,   updated : new content for the user managment div.",
"func":1
},
{
"ref":"control.admin.Admin.createUser",
"url":17,
"doc":"Creates new user. This action is only valid in test, pilot or custom mode. The current user must be an admin or root. Parameters      user: string The user name of the user. This should be different from the user names of existing users. The name may only contain the ASCII digits and lower case letters, plus dash, dot, and underscore. Spaces will be replaced by dots; all other illegal characters by underscores. Returns    - dict Contains the following keys:   status : whether the create action was successful   messages : messages issued during the process",
"func":1
},
{
"ref":"control.admin.Admin.deleteUser",
"url":17,
"doc":"Deletes a test user. This action is only valid in test, pilot or custom mode. The current user must be an admin or root. The user to be deleted should be a test user, not linked to any project or edition. Parameters      user: string The user name of the user. Returns    - dict Contains the following keys:   status : whether the create action was successful   messages : messages issued during the process",
"func":1
},
{
"ref":"control.messages",
"url":18,
"doc":""
},
{
"ref":"control.messages.Messages",
"url":18,
"doc":"Sending messages to the user and the server log. This class is instantiated by a singleton object. It has methods to issue messages to the screen of the webuser and to the log for the sysadmin. They distinguish themselves by the  severity :  debug ,  info ,  warning ,  error . There is also  plain , a leaner variant of  info . All those methods have two optional parameters:  logmsg and  msg . The behaviors of these methods are described in detail in the  Messages.message() function.  ! hint \"What to disclose?\" You can pass both parameters, which gives you the opportunity to make a sensible distinction between what you tell the web user (not much) and what you send to the log (the gory details). Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings ."
},
{
"ref":"control.messages.Messages.setFlask",
"url":18,
"doc":"Enables messaging to the web interface.",
"func":1
},
{
"ref":"control.messages.Messages.debugAdd",
"url":18,
"doc":"Adds a quick debug method to a destination object. The result of this method is that instead of saying   self.Messages.debug (logmsg=\"blabla\")   you can say   self.debug (\"blabla\")   It is recommended that in each object where you store a handle to Messages, you issue the statement   Messages.addDebug(self)  ",
"func":1
},
{
"ref":"control.messages.Messages.debug",
"url":18,
"doc":"Issue a debug message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.error",
"url":18,
"doc":"Issue an error message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.warning",
"url":18,
"doc":"Issue a warning message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.good",
"url":18,
"doc":"Issue a success message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.info",
"url":18,
"doc":"Issue a informational message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.special",
"url":18,
"doc":"Issue an emphasised informational message. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.plain",
"url":18,
"doc":"Issue a informational message, without bells and whistles. See  Messages.message() ",
"func":1
},
{
"ref":"control.messages.Messages.message",
"url":18,
"doc":"Workhorse to issue a message in a variety of ways. It can issue log messages and screen messages. Messages passed in  msg go to the web interface, the ones passed in  logmsg go to the log. If there is not yet a web interface,  msg messages are suppressed if there is also a  logmsg , otherwise they will be directed to the log as well. Parameters      tp: string The severity of the message. There is a fixed number of types:   debug Messages are prepended with  DEBUG:  . Log messages go to stderr. Messages will only show up on the web page if the app runs in debug mode.   plain Messages are not prepended with anything. Log messages go to standard output.   info Messages are prepended with  INFO:  . Log messages go to standard output.   warning Messages are prepended with  WARNING:  . Log messages go to standard error.   error Messages are prepended with  ERROR:  . Log messages go to standard error. It also raises an exception, which will lead to a 404 response (if flask is running, that is). But this stopping can be prevented by passing  stop=False . msg: string | void If not None, it is the contents of a screen message. This happens by the built-in  flash method of Flask. logmsg: string | void If not None, it is the contents of a log message. stop: boolean, optional True If False, an error message will not lead to a stop.",
"func":1
},
{
"ref":"control.messages.Messages.client",
"url":18,
"doc":"Adds javascript code whose execution displays a message. Parameters      tp, msg: string, string As in  message() replace: boolean, optional False If True, clears all previous messages. Returns    - dict an onclick attribute that can be added to a link element.",
"func":1
},
{
"ref":"control.messages.Messages.onFlask",
"url":18,
"doc":"Whether the webserver is running. If False, mo messages will be sent to the screen of the webuser, instead those messages end up in the log. This is useful in the initial processing that takes place before the flask app is started."
},
{
"ref":"control.static",
"url":19,
"doc":""
},
{
"ref":"control.static.Static",
"url":19,
"doc":"All about generating static pages."
},
{
"ref":"control.static.Static.sanitizeDC",
"url":19,
"doc":"Checks for missing (sub)-fields in the Dublin Core. Parameters      table: string The kind of info: site, project, or edition. This influences which fields should be present. dc: dict The Dublin Core info Returns    - void The dict is changed in place.",
"func":1
},
{
"ref":"control.static.Static.htmlify",
"url":19,
"doc":"Translate fields in a dict into html. Certain fields will trigger a markdown to html conversion. Certain fields will be normalized to lists: if the type of such a field is not list, it will be turned into a one-element list. There will also be generated a field whose name has the string  Comma appended, it will be a comma-separated list of the items in that field. Parameters      info: dict The input data Returns    - AttrDict The resulting data. NB: it is brand-new data which does not share any data with the input data. Fields are either transformed from markdown to HTML, or copied.",
"func":1
},
{
"ref":"control.static.Static.genPages",
"url":19,
"doc":"Generate html pages for a published edition. We assume the data of the projects and editions is already in place. As to the viewers: we compare the viewers and versions in the  data/viewers directory with the viewers and versions in the  published/viewers directory, and we copy viewer versions that are missing in the latter from the former. Exactly what will be generated depends on the parameters. There are the following things to generate:   S : site wide files, outside projects   P : project wide files, outside editions   E : edition pages  S will always be (re)generated. If a particular project is specified, the  P for that project will also be (re)generated. If a particular edition is specified, the  E for that edition will also be (re)generated. Parameters      pPubNUm, ePubNUm: integer or boolean or void Specifies which project and edition must be (re)generated, if they are integers. The integers is the numbers of the published project and edition. The following combinations are possible:   None ,  None : only  S is (re)generated;   p ,  None :  S and  P for project with number  p are (re)generated;   p ,  e :  S and  P and  E are (re)generated for project with number  p and edition with number  e within that project;   True ,  True : everything will be regenerated. Returns    - boolean Whether the generation was successful.",
"func":1
},
{
"ref":"control.static.Static.getData",
"url":19,
"doc":"Prepares page data of a certain kind. Pages are generated by filling in templates and partials on the basis of JSON data. Pages may require several kinds of data. For example, the index page needs data to fill in a list of projects and editions. Other pages may need the same kind of data. So we store the gathered data under the kinds they have been gathered. For some kinds we may restrict the data fetching to specified items: for  projectpages and  editionpages . When an edition has changed, we want to restrict the regeneration of pages to only those pages that need to change. And we also update things outside the projects and editions. Still, when an edition changes, the page with All editions also has to change. And if the edition was the first in a project to be published, a new project will be published as well, and hence the  All projects page needs to change. If an edition is published next to other editions in a project, the project page needs to change, since it contains thumbnails of all its editions. So, the general rule is that we will always regenerate the thumbnails and the All-projects and All-edition pages, but not all of the project pages and edition pages.  ! note \"Not all kinds will be restricted\" The kinds  viewers ,  textpages ,  site will never be restricted. The kinds  projects ,  editions are needed for thumbnails, and are never restricted. The kinds  project ,  edition are called by the collection of kinds  project and  edition , and are also not restricted. That leaves only the  projectpages and  editionpages needing to be restricted. Parameters      kind: string The kind of data we need to prepare. pNumGiven: integer or void Restricts the data fetching to projects with this publication number eNumGiven: integer or void Restricts the data fetching to editions with this publication number Returns    - dict or array The data itself. It is also stored in the member  data of this object, under key  kind . It will not be computed twice.",
"func":1
},
{
"ref":"control.static.Static.getDbData",
"url":19,
"doc":"Get the raw data contained in the json export from Mongo DB. This is the metadata of the site, the projects, and the editions. We store them as is in member  dbData . Later we distil page data from this, i.e. the data that is ready to fill in the variables of the templates. We assume this data has been exported when projects and editions got published, into files named  db.json .",
"func":1
},
{
"ref":"control.environment",
"url":20,
"doc":""
},
{
"ref":"control.environment.var",
"url":20,
"doc":"Retrieves the value of an environment variable. Parameters      name: string The name of the environment variable Returns    - string | void If the variable does not exist, None is returned.",
"func":1
},
{
"ref":"control.app",
"url":21,
"doc":""
},
{
"ref":"control.app.appFactory",
"url":21,
"doc":"Sets up the main flask app. The main task here is to configure routes, i.e. mappings from url-patterns to functions that create responses  ! note \"WebDAV enabling\" This flask app will later be combined with a webdav app, so that the combined app has the business logic of the main app but can also handle webdav requests. The routes below contain a few patterns that are used for authorising WebDAV calls: the onses starting with  /auth and  /cannot . See also  control.webdavapp . Parameters      objects a slew of objects that set up the toolkit with which the app works: settings, messaging and logging, MongoDb connection, 3d viewer support, higher level objects that can fetch chunks of content and distribute it over the web page. Returns    - object A WebDAV-enabled flask app, which is a wsgi app.",
"func":1
},
{
"ref":"control.viewers",
"url":22,
"doc":""
},
{
"ref":"control.viewers.Viewers",
"url":22,
"doc":"Knowledge of the installed 3D viewers. This class knows which (versions of) viewers are installed, and has the methods to invoke them. It is instantiated by a singleton object. Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages ."
},
{
"ref":"control.viewers.Viewers.addAuth",
"url":22,
"doc":"Give this object a handle to the Auth object. The Viewers and Auth objects need each other, so one of them must be given the handle to the other after initialization.",
"func":1
},
{
"ref":"control.viewers.Viewers.check",
"url":22,
"doc":"Checks whether a viewer version exists. Given a viewer and a version, it is looked up whether the code is present. If not, reasonable defaults returned instead by default. Parameters      viewer: string The viewer in question. version: string The version of the viewer in question. Returns    - string | void The version is returned unmodified if that viewer version is supported. If the viewer is supported, but not the version, the default version of that viewer is taken, if there is a default version, otherwise the latest supported version. If the viewer is not supported, None is returned.",
"func":1
},
{
"ref":"control.viewers.Viewers.getViewInfo",
"url":22,
"doc":"Gets viewer-related info that an edition is made with. Parameters      edition: AttrDict The edition record. Returns    - tuple of string  The name of the viewer  The name of the scene",
"func":1
},
{
"ref":"control.viewers.Viewers.getFrame",
"url":22,
"doc":"Produces a set of buttons to launch 3D viewers for a scene. Make sure that if there is no scene file present, no viewer will be opened. Parameters      edition: AttrDict The edition in question. actions: iterable of string The actions for which we have to create buttons. Typically  read and possibly also  update . Actions that are not recognized as viewer actions will be filtered out, such as  create and  delete . viewer: string The viewer in which the scene is currently loaded. versionActive: string | void The version of the viewer in which the scene is currently loaded, if any, otherwise None actionActive: string | void The mode in which the scene is currently loaded in the viewer ( read or  update ), if any, otherwise None sceneExists: boolean Whether the scene file exists. Returns    - string The HTML that represents the buttons.",
"func":1
},
{
"ref":"control.viewers.Viewers.genHtml",
"url":22,
"doc":"Generates the HTML for the viewer page that is loaded in an iframe. When a scene is loaded in a viewer, it happens in an iframe. Here we generate the complete HTML for such an iframe. Parameters      urlBase: string The first part of the root url that is given to the viewer. The viewer code uses this to retrieve additional information. The root url will be completed with the  action and the  viewer . sceneFile: string The name of the scene file in the file system. viewer: string The chosen viewer. version: string The chosen version of the viewer. action: string The chosen mode in which the viewer is launched ( read or  update ). subMode: string | None The sub mode in which the viewer is to be used ( update or  create ). Returns    - string The HTML for the iframe.",
"func":1
},
{
"ref":"control.viewers.Viewers.getRoot",
"url":22,
"doc":"Composes the root url for a viewer. The root url is passed to a viewer instance as the url that the viewer can use to fetch its data. It is not meant for the static data that is part of the viewer software, but for the model related data that the viewer is going to display. See  getStaticRoot() for the url meant for getting parts of the viewer software. Parameters      urlBase: string The first part of the root url, depending on the project and edition. action: string The mode in which the viewer is opened. Depending on the mode, the viewer code may communicate with the server with different urls. For example, for the voyager, the  read mode (voyager-explorer) uses ordinary HTTP requests, but the  update mode (voyager-story) uses WebDAV requests. So this app points voyager-explorer to a root url starting with  /data , and voyager-story to a root url starting with  /webdav . These prefixes of the urls can be configured per viewer in the viewer configuration in  yaml/viewers.yml .",
"func":1
},
{
"ref":"control.viewers.Viewers.getStaticRoot",
"url":22,
"doc":"Composes the static root url for a viewer. The static root url is passed to a viewer instance as the url that the viewer can use to fetch its assets. It is not meant for the model related data, but for the parts of the viewer software that it needs to get from the server. See  getRoot() for the url meant for getting model-related data. Parameters      urlBase: string The first part of the root url, depending on the project and edition. action: string The mode in which the viewer is opened. Depending on the mode, the viewer code may communicate with the server with different urls. For example, for the voyager, the  read mode (voyager-explorer) uses ordinary HTTP requests, but the  update mode (voyager-story) uses WebDAV requests. So this app points voyager-explorer to a root url starting with  /data , and voyager-story to a root url starting with  /webdav . These prefixes of the urls can be configured per viewer in the viewer configuration in  yaml/viewers.yml .",
"func":1
},
{
"ref":"control.wrap",
"url":23,
"doc":""
},
{
"ref":"control.wrap.Wrap",
"url":23,
"doc":"Wrap concepts into HTML. This class knows how to wrap several higher-level concepts into HTML, such as projects, editions and users, depending on specific purposes, such as showing widgets to manage projects and editions. It is instantiated by a singleton object. Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Viewers: object Singleton instance of  control.viewers.Viewers ."
},
{
"ref":"control.wrap.Wrap.addAuth",
"url":23,
"doc":"Give this object a handle to the Auth object. The Wrap and Auth objects need each other, so one of them must be given the handle to the other after initialization.",
"func":1
},
{
"ref":"control.wrap.Wrap.addContent",
"url":23,
"doc":"Give this object a handle to the Content object. The Wrap and Content objects need each other, so one of them must be given the handle to the other after initialization.",
"func":1
},
{
"ref":"control.wrap.Wrap.projectsMain",
"url":23,
"doc":"Wrap the list of projects for the main display. Parameters      site: AttrDict The record that corresponds to the site as a whole. It acts as a master record of the projects. projects: list of AttrDict The project records. Returns    - string The HTML of the project list",
"func":1
},
{
"ref":"control.wrap.Wrap.editionsMain",
"url":23,
"doc":"Wrap the list of editions of a project for the main display. Parameters      project: AttrDict The master project record of the editions. editions: list of AttrDict The edition records. Returns    - string The HTML of the edition list",
"func":1
},
{
"ref":"control.wrap.Wrap.sceneMain",
"url":23,
"doc":"Wrap the scene of an edition for the main display. Parameters      projectId: ObjectId The id of the project to which the edition belongs. edition: AttrDict The edition record of the scene. viewer: string The viewer that will be used. version: string The version of the chosen viewer that will be used. action: string The mode in which the viewer should be opened. sceneExists: boolean Whether the scene file exists Returns    - string The HTML of the scene",
"func":1
},
{
"ref":"control.wrap.Wrap.getCaption",
"url":23,
"doc":"Produces a caption of a project or edition. Parameters      visual: string A link to an image to display in the caption. titleText: string The text on the caption. status: string The status of the project/edition: visible/hidden/published/in progress. The exact names statusCls: string The CSS class corresponding to  status button: string Control for a certain action, or empty if the user is not authorised. url: string The url to navigate to if the user clicks the caption.",
"func":1
},
{
"ref":"control.wrap.Wrap.wrapCaption",
"url":23,
"doc":"Assembles a caption from building blocks.",
"func":1
},
{
"ref":"control.wrap.Wrap.contentButton",
"url":23,
"doc":"Puts a button on the interface, if that makes sense. The button, when pressed, will lead to an action on certain content. It will be checked first if that action is allowed for the current user. If not the button will not be shown.  ! note \"Delete buttons\" Even if a user is authorised to delete a record, it is not allowed to delete master records if its detail records still exist. In that case, no delete button is displayed. Instead we display a count of detail records.  ! note \"Create buttons\" When placing a create button, the relevant record acts as the master record, to which the newly created record will be added as a detail. Parameters      table: string The relevant table. record: string | ObjectId | AttrDict The relevant record. action: string The type of action that will be performed if the button triggered. permitted: boolean, optional None If the permission for the action is already known before calling this function, it is passed here. If this parameter is None, we'll compute the permission. insertTable: string, optional None If the action is \"create\", this is the table in which a record get inserted. The  table and  record arguments are then supposed to specify the  master record of the newly inserted record. Needed to determine whether a press on the button is permitted. key: string, optional None If present, it identifies a field that is stored inside the record. href: string, optional None If present, contains the href attribute for the button. confirm: boolean, optional False Whether to ask the user for confirmation",
"func":1
},
{
"ref":"control.helpers",
"url":24,
"doc":""
},
{
"ref":"control.helpers.lcFirst",
"url":24,
"doc":"",
"func":1
},
{
"ref":"control.helpers.prettify",
"url":24,
"doc":"",
"func":1
},
{
"ref":"control.helpers.genViewerSelector",
"url":24,
"doc":"",
"func":1
},
{
"ref":"control.helpers.console",
"url":24,
"doc":"",
"func":1
},
{
"ref":"control.helpers.run",
"url":24,
"doc":"Runs a shell command and returns all relevant info. The function runs a command-line in a shell, and returns whether the command was successful, and also what the output was, separately for standard error and standard output. Parameters      cmdline: string The command-line to execute. workDir: string, optional None The working directory where the command should be executed. If  None the current directory is used.",
"func":1
},
{
"ref":"control.helpers.htmlEsc",
"url":24,
"doc":"Escape certain HTML characters by HTML entities. To prevent them to be interpreted as HTML in cases where you need them literally. Parameters      val: string The input value",
"func":1
},
{
"ref":"control.helpers.htmlUnEsc",
"url":24,
"doc":"Unescape certain HTML entities by their character values. Parameters      val: string The input value",
"func":1
},
{
"ref":"control.helpers.hEmpty",
"url":24,
"doc":"",
"func":1
},
{
"ref":"control.helpers.hScalar",
"url":24,
"doc":"",
"func":1
},
{
"ref":"control.helpers.hScalar0",
"url":24,
"doc":"",
"func":1
},
{
"ref":"control.helpers.hList",
"url":24,
"doc":"",
"func":1
},
{
"ref":"control.helpers.hDict",
"url":24,
"doc":"",
"func":1
},
{
"ref":"control.helpers.hData",
"url":24,
"doc":"",
"func":1
},
{
"ref":"control.helpers.showDict",
"url":24,
"doc":"Shows selected keys of a dictionary in a pretty way. Parameters      keys: iterable of string For each key passed to this function, the information for that key will be displayed. If no keys are passed, all keys will be displayed. tight: boolean, optional True Whether to use the details element to compactify the representation. Returns    - displayed HTML An expandable list of the key-value pair for the requested keys.",
"func":1
},
{
"ref":"control.prepare",
"url":25,
"doc":""
},
{
"ref":"control.prepare.prepare",
"url":25,
"doc":"Prepares the way for setting up the Flask webapp. Several classes are instantiated with a singleton object; each of these objects has a dedicated task in the app:   control.config.Config.Settings : all configuration aspects   control.messages.Messages : handle all messaging to user and sysadmin   control.mongo.Mongo : higher-level commands to the MongoDb   control.viewers.Viewers : support the third party 3D viewers   control.wrap.Wrap : several lengthy functions to wrap concepts into HTML   control.datamodel.Datamodel : factory for handling fields, inherited by  Content   control.content.Content : retrieve all data that needs to be displayed   control.publish.Publish : publish an edition as static pages   control.auth.Auth : compute the permission of the current user to access content   control.pages.Pages : high-level functions that distribute content over the page  ! note \"Should be run once!\" These objects are used in several web apps:  the main web app  a copy of the main app that is enriched with the webdav functionality However, these objects should be initialized once, before either app starts, and the same objects should be passed to both invocations of the factory functions that make them ( control.app.appFactory ). The invocations are done in  control.webdavapp.appFactory . Parameters      migrate: boolean, optional False If True, overrides the  trivial parameter. It will initialize those objects that are needed for the migration of data. design: boolean, optional False If True, overrides the  trivial parameter. It will initialize those objects that are needed for static page generation in the  Published directory, assuming that the project/edition files have already been exported. trivial: boolean, optional False If  design is False and  trivial is True, skips the initialization of most objects. Useful if the pure3d app container should run without doing anything. This happens when we just want to start the container and run shell commands inside it, for example after a complicated refactoring when the flask app has too many bugs. Returns    - AttrDict A dictionary keyed by the names of the singleton objects and valued by the singleton objects themselves.",
"func":1
},
{
"ref":"control.publish",
"url":26,
"doc":""
},
{
"ref":"control.publish.Publish",
"url":26,
"doc":"Publishing content as static pages. It is instantiated by a singleton object. Parameters      Settings: AttrDict App-wide configuration data obtained from  control.config.Config.Settings . Messages: object Singleton instance of  control.messages.Messages . Mongo: object Singleton instance of  control.mongo.Mongo . Tailwind: object Singleton instance of  control.tailwind.Tailwind ."
},
{
"ref":"control.publish.Publish.getPubNums",
"url":26,
"doc":"Determine project and edition publication numbers. Those numbers are inside the project and edition records in the database if the project/edition has been published before; otherwise we pick an unused number for the project; and within the project an unused edition number. When we look for those numbers, we look in the database records, and we look on the filesystem, and we take the number one higher than the maximum number used in the database and on the file system.",
"func":1
},
{
"ref":"control.publish.Publish.generatePages",
"url":26,
"doc":"",
"func":1
},
{
"ref":"control.publish.Publish.updateEdition",
"url":26,
"doc":"",
"func":1
},
{
"ref":"control.publish.Publish.addSiteFiles",
"url":26,
"doc":"",
"func":1
},
{
"ref":"control.publish.Publish.addProjectFiles",
"url":26,
"doc":"",
"func":1
},
{
"ref":"control.publish.Publish.addEditionFiles",
"url":26,
"doc":"",
"func":1
},
{
"ref":"control.publish.Publish.removeProjectFiles",
"url":26,
"doc":"",
"func":1
},
{
"ref":"control.publish.Publish.removeEditionFiles",
"url":26,
"doc":"",
"func":1
}
]