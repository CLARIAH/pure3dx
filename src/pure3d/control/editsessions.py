class EditSessions:
    def __init__(self, Mongo):
        """Managing edit sessions of users.

        This class has methods to create and delete edit sessions for users,
        which guard them from overwriting each other's data.

        Edit sessions prevent users from editing the same piece of content,
        in particular it prevents multiple `edit`-mode 3D viewers
        being active with the same scene.

        It is instantiated by a singleton object.

        Parameters
        ----------
        Mongo: object
            Singleton instance of `control.mongo.Mongo`.
        """
        self.Mongo = Mongo
