import sys
from .flask import flashMsg


class Messages:
    def __init__(self, Settings, onFlask=True):
        """Sending messages to the user and the server log.

        This class is instantiated by a singleton object.

        It has methods to issue messages to the screen of the webuser
        and to the log for the sysadmin.

        They distinguish themselves by the *severity*:
        **debug**, **info**, **warning**, **error**.
        There is also **plain**, a leaner variant of **info**.

        All those methods have two optional parameters:
        `logmsg` and `msg`.

        The behaviors of these methods are described in detail in
        the `Messages.message()` function.

        !!! hint "What to disclose?"
            You can pass both parameters, which gives you the opportunity
            to make a sensible distinction between what you tell the
            web user (not much) and what you send to the log (the gory details).

        Parameters
        ----------
        Settings: AttrDict
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        """
        self.Settings = Settings
        self.onFlask = False
        """Whether the webserver is running.

        If False, mo messages will be sent to the screen of the webuser,
        instead those messages end up in the log.
        This is useful in the initial processing that takes place
        before the flask app is started.
        """

    def setFlask(self):
        """Enables messaging to the web interface."""
        self.onFlask = True

    def debugAdd(self, dest):
        """Adds a quick debug method to a destination object.

        The result of this method is that instead of saying

        ```
        self.Messages.debug (logmsg="blabla")
        ```

        you can say

        ```
        self.debug ("blabla")
        ```

        It is recommended that in each object where you store a handle
        to Messages, you issue the statement

        ```
        Messages.addDebug(self)
        ```
        """

        def dbg(m):
            """Inner function to be set as method to the class."""
            self.debug(logmsg=m)

        setattr(dest, "debug", dbg)

    def debug(self, msg=None, logmsg=None):
        """Issue a debug message.

        See `Messages.message()`
        """
        self.message("debug", msg, logmsg)

    def error(self, msg=None, logmsg=None):
        """Issue an error message.

        See `Messages.message()`
        """
        self.message("error", msg, logmsg)

    def warning(self, msg=None, logmsg=None):
        """Issue a warning message.

        See `Messages.message()`
        """
        self.message("warning", msg, logmsg)

    def good(self, msg=None, logmsg=None):
        """Issue a success message.

        See `Messages.message()`
        """
        self.message("good", msg, logmsg)

    def info(self, msg=None, logmsg=None):
        """Issue a informational message.

        See `Messages.message()`
        """
        self.message("info", msg, logmsg)

    def special(self, msg=None, logmsg=None):
        """Issue an emphasised informational message.

        See `Messages.message()`
        """
        self.message("special", msg, logmsg)

    def plain(self, msg=None, logmsg=None):
        """Issue a informational message, without bells and whistles.

        See `Messages.message()`
        """
        self.message("plain", msg, logmsg)

    def message(self, tp, msg, logmsg):
        """Workhorse to issue a message in a variety of ways.

        It can issue log messages and screen messages.

        Messages passed in `msg` go to the web interface, the ones
        passed in `logmsg` go to the log.

        If there is not yet a web interface, `msg` messages are suppressed if there
        is also a `logmsg`, otherwise they will be directed to the log as well.

        Parameters
        ----------
        tp: string
            The severity of the message.
            There is a fixed number of types:

            * `debug`
              Messages are prepended with `DEBUG: `.
              Log messages go to stderr.
              Messages will only show up on the web page
              if the app runs in debug mode.

            * `plain`
              Messages are not prepended with anything.
              Log messages go to standard output.

            * `info`
              Messages are prepended with `INFO: `.
              Log messages go to standard output.

            * `warning`
              Messages are prepended with `WARNING: `.
              Log messages go to standard error.

            * `error`
              Messages are prepended with `ERROR: `.
              Log messages go to standard error.

        msg: string | void
            If not None, it is the contents of a screen message.
            This happens by the built-in `flash` method of Flask.
        logmsg: string | void
            If not None, it is the contents of a log message.

        """
        Settings = self.Settings
        onFlask = self.onFlask

        stream = sys.stderr if tp in {"debug", "error", "warning"} else sys.stdout
        label = "" if tp == "plain" else f"{tp.upper()}: "

        if not onFlask:
            if msg is not None and logmsg is None:
                stream.write(f"{label}{msg}\n")
            if logmsg is not None:
                stream.write(f"{label}{logmsg}\n")
            stream.flush()
        else:
            debugMode = Settings.debugMode
            H = Settings.H

            if tp == "debug" and not debugMode:
                return

            if msg is not None:
                cls = "info" if tp == "plain" else tp
                m = H.he(msg)
                flashMsg(f"{label}{m}", cls)
            if logmsg is not None:
                stream.write(f"{label}{logmsg}\n")
                stream.flush()

    def client(self, tp, message, replace=False):
        """Adds javascript code whose execution displays a message.

        Parameters
        ----------
        tp, msg: string, string
            As in `message()`
        replace: boolean, optional False
            If True, clears all previous messages.

        Returns
        -------
        dict
            an onclick attribute that can be added to a link element.
        """
        replace = "true" if replace else "false"
        return dict(onclick=f"addMsg('{tp}', '{message}', {replace});")
