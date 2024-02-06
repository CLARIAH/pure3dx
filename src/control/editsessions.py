class EditSessions:
    EXPIRATION = 600
    EXPIRATION_VIEWER = 3600

    def __init__(self, Mongo, Auth):
        """Managing edit sessions of users.

        This class has methods to create and delete edit sessions for users,
        which guard them from overwriting each other's data.

        Edit sessions prevent users from editing the same piece of content,
        in particular it prevents multiple `edit`-mode 3D viewers
        being active with the same scene.

        It is instantiated by a singleton object.

        ### What are edit sessions?

        First of all, this machinery is only called upon if the user is *authorised*
        to edit the relevant piece of content.
        Whether an authorised user may proceed depends on whether the content
        in question is not currently being edited by an other user.

        The idea is that content may only be modified (updated/deleted) if it is
        guarded by an edit session.
        An edit session is a MongoDb record that holds a user id and fields that
        specify a piece of content, and a time stamp.
        The timestamp counts as the start of the session.

        When users are done, the edit session is deleted.

        The idea is, that before a user is granted edit access to content, it is checked
        first whether there is an existing edit session for that user and that content.
        If so, edit access is not granted.
        If there is no such editsession, access is granted, and a new
        editsession is made.
        Whenever the user terminates the editing action, the editsession is deleted.
        A user can also save withoout terminating the edit action. In that case the
        timestamp is set to the current time.
        Editsessions will be removed after a certain amount of time.

        So, editsessions contain:

        * a user specification
        * a content specification
        * a time specification

        **User specification**: when a session is created, the _id of the current user
        is stored in the userId field of the editSession record.

        **Content specification**: we need to specify content in MongoDb records and
        on the file system.

        !!! caution "Disclaimer"
            We do not attempt to make a water-tight locking system, because the
            situation is a bit complex, due to the fact that most file system content
            is edited through a 3rd party 3D viewer (currently: Voyager-Story).
            Moreover, there may be multiple scenes for a single 3D model, and these
            scenes may refer to the same articles, although every scene contains
            its own metadata of the articles.

        In this fuzzy situation we choose a rather coarse mode of action:

        * at most one Voyager-Story is allowed to be fired up per edition;
        * file actions are guarded together with the mongo records that are also
          affected by those actions.

        That means that content specifications boil down to:

        * `table`: the name of the table in which the meta data record sits
        * `recordId`: the id of the record in which the metadata sits

        We list all possible non-mongo actions and indicate the corresponding content
        specifications (the id values are imaginary):

        * **viewer sessions that allow editing actions**:
          `table="edition" recordId="176ba"`

        *   **icon file changes**
            * **site level**: `table="site" recordId="954fe"`
            * **project level**: `table="project" recordId="065af"`
            * **edition level**: `table="edition" recordId="176ba"`

        *   **model file changes**
            `table="edition" recordId="176ba"`

        *   **scene file changes**
            `table="edition" recordId="176ba"`

            !!! note "scene locks are edition wide"
                Even if you want to change an icon of a single scene,
                you need a full edition-level edit session.

        ### Expiring edit sessions

        Edit sessions expire if the user is done with the action for which they needed
        the session.
        But sometimes users forget to finalise their actions, and for those cases we
        need something that prevents edit sessions to be immortal.

        We let the server expire sessions that reach their expiration time.

        When edit sessions have expired this way, other users may claim
        editsessions for that content.

        Expiration does not delete the session, but flags it as terminated.

        Only when another uses asks for a new edit session with the same content
        specs, the terminated session is deleted, after which a new one is created
        for that other user.

        If the original user, who has not saved his material in time, tries to
        save content guarded by a terminated session, it will be allowed if the expired
        session still exists.
        Because in that case no other user has claimed an editsession for the
        content, and hence no other user has modified it.

        But if the terminated session has been deleted because of a new edit session
        by another user, the original user will be notified when he attempts to save.
        The user cannot proceed, the only thing he can do is to copy the content to
        the clipboard, try to obtain a new session, and paste the content in
        that session.

        If a user tries to save content without there being a corresponding
        edit session.

        Parameters
        ----------
        Mongo: object
            Singleton instance of `control.mongo.Mongo`.
        Auth: object
            Singleton instance of `control.auth.Auth`.
        """
        self.Mongo = Mongo

    def lookup(self, table, recordId):
        """Look up an edit session.

        Parameters
        ----------
        table: string
            The table of the edited material
        recordId: ObjectId
            The id of the record of the edited material

        Returns
        -------
        ObjectId | void
            If the editsession has been found, the id of that session,
            otherwise None
        """
        pass

    def create(self, table, recordId, session=False, extend=False):
        """Create or extend an edit session of a field in a record for the current user.

        The system can create new editsessions or extend existing editsessions.

        Creation is needed when the user wants to start editing a piece of content
        that he was not already editing.

        Extending is needed when a user is editing a piece of content and performs
        a save, while continuing editing the content.

        Parameters
        ----------
        table: string
            The table of the edited material
        recordId: ObjectId
            The id of the record of the edited material
        session: boolean, optional False
            Whether the editsession is for a viewer session or for something else.
            This has only influence on the amount of time after which the
            session expires.
        extend: boolean, optional False
            If called with `extend=False` a new editsession is required, otherwise
            an existing edit session is timestamped with the current time.

        Returns
        -------
        boolean
            Whether the operation succeeded. False means that the user should not get
            the opportunity to continue the edit action.
        """
        pass

    def terminates(self, table, recordId):
        """Delete an edit session.

        Parameters
        ----------
        table: string
            The table of the edited material
        recordId: ObjectId
            The id of the record of the edited material

        Returns
        -------
        void
        """
        pass

    def timeout(self):
        """Terminate all outdated edit sessions.

        An outdated editsession is one whose timestamp lies too far in the past.

        For sessions that correspond to a viewer session, this amount is
        given in the class member `EXPIRATION_VIEWER`.

        For other sessions it is given by the much shorter `EXPIRATION`.

        This method should be called every minute or so.

        """
        pass
