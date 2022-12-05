class EditSessions:
    def __init__(self, Mongo, Auth):
        """Managing edit sessions of users.

        This class has methods to create and delete edit sessions for users,
        which guard them from overwriting each other's data.

        Edit sessions prevent users from editing the same piece of content,
        in particular it prevents multiple `edit`-mode 3D viewers
        being active with the same scene.

        It is instantiated by a singleton object.

        Here are the rules.

        The idea is that content may only be modified (updated/deleted) if it is
        guarded by an edit session.
        An edit session is a MongoDb record that holds a user id and fields that
        specify a piece of content, and a creation time and an access time.
        The access time is the creation time, until a second attempt is made to
        create an edit session with the same content/user specification.
        Then we retain the current session, and set the access time to the time
        of this subsequent event.

        When users are done, the edit session is deleted.

        User specification: when a session is created, the _id of the current user
        is stored in the userId field of the editSession record.

        Content specification: we need to specify content in MongoDb records and
        on the file system.

        !!! caution "Disclaimer"
            We do not attempt to make a water-tight locking system, because the
            situation is a bit complex, due to the fact that most file system content
            is edited through a 3rd party 3D viewer (currently: Voyager-Story).
            Moreover, there may be multiple scenes for a single 3D model, and these
            scenes may refer to the same articles, although every scene contains
            its own metadata of the articles.

        In this fuzzy situation we choose a rather coarse mod of action:
        at most one Voyager-Story is allowed to be fired up per edition.
        If a Voyager Story is active, the model and none of the scenes, and none
        of the articles and media can be modified by other users.

        But we exert finer control where we can: the metadata fields in the
        database.

        Editing some content requires that some other content is locked.

        E.g. editing a scene requires that the 3d-model file and the articles
        in that edition are also locked.
        And editing the model means that all scenes must be locked.

        So in effect, we only need the key "model", to lock the whole edition.
        So whenever somebody starts working with voyager-story, the whole edition
        must be locked, except the icons.

        Here are the items to be locked by edit sessions:

        * *icons*: the project or edition or scene icons.
        * *editions*: the 3d model of the edition in question, all of its scenes, and
          the articles folder, with the media subfolder.

        Content on MongoDB is specified by: *table*, *recordId*, *key*, where
        key is a field specifier as in the `fields` dictionary of `datamodel.yml`.
        We will only edit fields if they fall under one of these keys.

        Content on the file system is specified by: *projectId*, *editionId*, *sceneId*
        *key*. Key is a specifier that points to certain content:

        Parameters
        ----------
        Mongo: object
            Singleton instance of `control.mongo.Mongo`.
        Auth: object
            Singleton instance of `control.auth.Auth`.
        """
        self.Mongo = Mongo

    def create(self, table, recordId, key=None):
        """Create an edit session of a field in a record for the current user.

        For some fields and record this also guards the editing of releated material
        on the file system.

        !!! note "Editions and models"
            If the table is `editions` and the key is None, the current model of
            the edition will be covered. That means that only the user holding this
            session may:

            * upload a new version of this model;
            * modify any scene of this model;
            * modify articles and media in the articles and articles/media directories.

        !!! note "Scenes and articles and media"
            If the table is `scenes` and the key is None, the current scene will be
            covered. That means that only the user holding this session may:

            * upload a new version of this scene;
            * modify the scene;
            * modify articles and media in the articles and articles/media directories.

        Parameters
        ----------
        table: string
            The table of the edited material
        recordId: ObjectId
            The record of the edited material
        key: string, optional None
            identifier of the edited field if present, otherwise the session
            is about related material on the file system.

        Returns
        -------
        ObjectId
            If a session with these specs (including the user) already exists,
            the user is already in this edit session, and the id of the current
            session is returned. There will b e an indicator in the record of
            the time of this acces.
            Otherwise, a new record will be created, with the create time and access
            time set, and the id of the record is returned.
        """
        pass
