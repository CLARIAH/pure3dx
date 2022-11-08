from control.generic import AttrDict


class Users:
    def __init__(self, Settings, Messages, Mongo):
        """All about users and the current users.

        This class has methods to login/authenticate a user,
        to logout/deauthenticate users, to retrieve users' data.

        It is instantiated by a singleton object.

        Parameters
        ----------
        Settings: `control.helpers.generic.AttrDict`
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        Mongo: object
            Singleton instance of `control.mongo.Mongo`.
        """
        self.Settings = Settings
        self.Messages = Messages
        Messages.debugAdd(self)
        self.Mongo = Mongo

    def wrapTestUsers(self, userActive):
        """Generate HTML for login buttons for test users.

        Only produces a non-empty result if the app is in test mode.

        Parameters
        ----------
        userActive: ObjectId
            The id of the user that is currently logged in.
            The button for this users will be rendered as the active one.
        """
        Settings = self.Settings
        Mongo = self.Mongo

        if not Settings.testMode:
            return ""

        def wrap(title, href, cls, text):
            return (
                f'<a title="{title}" href="{href}" class="button small {cls}">'
                f"{text}</a>"
            )

        active = "active" if userActive is None else ""

        html = []
        html.append(wrap("if not logged in", "/logout", active, "logged out"))

        for user in sorted(Mongo.execute("users", "find"), key=lambda r: r["name"]):
            user = AttrDict(user)

            active = "active" if str(user._id) == userActive else ""
            html.append(wrap(user.role, f"/login?userid={user._id}", active, user.name))

        return "\n".join(html)
