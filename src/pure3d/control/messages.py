import sys
from control.flask import stop

from control.generic import htmlEsc


class Messages:
    def __init__(self, Settings, flask=True):
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

        When the controllers of the flask app call methods that produce
        messages for the screen of the webusers,
        these messages are accumulated,
        and sent to the web client with the next response.

        Parameters
        ----------
        Settings: `control.helpers.generic.AttrDict`
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        flask: boolean, optional True
            If False, mo messages will be sent to the screen of the webuser,
            instead those messages end up in the log.
            This is useful in the initial processing that takes place
            before the flask app is started.
        """
        self.Settings = Settings
        self.messages = []
        self.flask = flask

    def debugAdd(self, dest):
        """Adds a quick debug method to a destination object.

        The result of this method is that nstead of saying

        ```
        self.Messages.debug(logmsg="blabla")
        ```

        you can say

        ```
        self.debug("blabla")
        ```

        It is recommended that in each object where you store a handle
        to Messages, you issue the statement

        ```
        Messages.addDebug(self)
        ```
        """

        def dbg(m):
            self.debug(logmsg=m)

        setattr(dest, "debug", dbg)

    def debug(self, msg=None, logmsg=None):
        """Issue a debug message.

        See `Messages.message()`
        """
        self.message("debug", msg=msg, logmsg=logmsg)

    def error(self, msg=None, logmsg=None):
        """Issue an error message.

        See `Messages.message()`
        """
        self.message("error", msg=msg, logmsg=logmsg)

    def warning(self, msg=None, logmsg=None):
        """Issue a warning message.

        See `Messages.message()`
        """
        self.message("warning", msg=msg, logmsg=logmsg)

    def info(self, msg=None, logmsg=None):
        """Issue a informational message.

        See `Messages.message()`
        """
        self.message("info", msg=msg, logmsg=logmsg)

    def plain(self, msg=None, logmsg=None):
        """Issue a informational message, without bells and whistles.

        See `Messages.message()`
        """
        self.message("plain", msg=msg, logmsg=logmsg)

    def message(self, tp, msg, logmsg):
        """Workhorse to issue a message in a variety of ways.

        It can issue log messages and screen messages.

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
              It also raises an exception, which will lead
              to a 404 response (if flask is running, that is).

        msg: string, optional None
            If not None, it is the contents of a screen message.
        logmsg: string, optional None
            If not None, it is the contents of a log message.
        """
        Settings = self.Settings
        stream = sys.stderr if tp in {"debug", "error", "warning"} else sys.stdout
        label = "" if tp == "plain" else f"{tp}: "

        if Settings is None:
            stream.write(f"{label}{msg}\n")
            stream.write(f"{label}{logmsg}\n")
            stream.flush()
        else:
            debugMode = Settings.debugMode
            if tp == "debug" and not debugMode:
                return

            if msg is not None:
                self.messages.append((tp, msg))
            if logmsg is not None:
                stream.write(f"{label}{logmsg}\n")
                stream.flush()

            if tp == "error" and self.flask:
                stop()

    def clearMessages(self):
        """Clears the accumulated messages."""
        self.messages.clear()

    def generateMessages(self):
        """Wrap the accumulates messages into html.

        They are ready to be included in a response.

        The list of accumulated messages will be cleared afterwards.
        """
        html = ["""<div class="messages">"""]

        for (tp, msg) in self.messages:
            cls = "info" if tp == "plain" else tp
            label = "" if tp == "plain" else tp.upper()
            html.append(f"""<div class="msgitem {cls}">{label}: {htmlEsc(msg)}</div>""")

        html.append("</div>")
        self.clearMessages()
        return "\n".join(html)
