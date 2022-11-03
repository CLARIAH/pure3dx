import sys
from flask import abort

from control.helpers.generic import htmlEsc


class Messages:
    def __init__(self, Settings, flask=True):
        """Sending messages to the user and the server log.


        This class has methods to issue messages to the screen of the webuser
        and to the log for the sysadmin.

        They distinguish themselves by the *severity*:
        **debug**, **info**, **warning**, **error**.
        There is also **plain**, a leaner variant of **info**.

        All those methods have two optional parameters:

        `logmsg`: text that goes into the log file
        `msg`: content that is accumulated for the next response.

        !!! hint "What to disclose?"
            You can pass both parameters, which gives you the opportunity
            to make a sensible distinction between what you tell the
            web user (not much) and what you send to the log (the gory details).

        It is instantiated by a singleton object.

        When the controllers of the flask app call methods that produce
        messages for the screen of the webusers,
        these messages are accumulated,
        and sent to the web client with the next response.

        Parameters
        ----------
        Settings: AttrDict
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

    def clearMessages(self):
        """Clears the accumulated messages.
        """
        self.messages.clear()

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

        When sent to the log, it goes to standard error.
        """
        if msg is not None:
            self._addMessage("debug", f"DEBUG: {msg}")
        if logmsg is not None:
            sys.stderr.write(f"DEBUG: {logmsg}\n")
            sys.stderr.flush()

    def error(self, msg=None, logmsg=None):
        """Issue an error message.

        When sent to the log, it goes to standard error.
        It also raises an exception, which will lead
        to a 404 response (if flask is running, that is).
        """
        if msg is not None:
            self._addMessage("error", f"ERROR: {msg}")
        if logmsg is not None:
            sys.stderr.write(f"ERROR: {logmsg}\n")
            sys.stderr.flush()
            if self.flask:
                abort(404)

    def warning(self, msg=None, logmsg=None):
        """Issue a warning message.

        When sent to the log, it goes to standard error.
        """
        if msg is not None:
            self._addMessage("warning", f"WARNING: {msg}")
        if logmsg is not None:
            sys.stderr.write(f"WARNING: {logmsg}\n")
            sys.stderr.flush()

    def info(self, msg=None, logmsg=None):
        """Issue a informational message.

        When sent to the log, it goes to standard output.
        """
        if msg is not None:
            self._addMessage("info", f"INFO: {msg}")
        if logmsg is not None:
            sys.stdout.write(f"INFO: {logmsg}\n")
            sys.stdout.flush()

    def plain(self, msg=None, logmsg=None):
        """Issue a informational message, without bells and whistles.

        When sent to the log, it goes to standard output.
        """
        if msg is not None:
            self._addMessage("info", msg)
        if logmsg is not None:
            sys.stdout.write(f"{logmsg}\n")
            sys.stdout.flush()

    def generateMessages(self):
        """Wrap the accumulates messages into html.

        They are ready to be included in a response.

        The list of accumulated messages will be cleared afterwards.
        """
        html = ["""<div class="messages">"""]

        for (tp, msg) in self.messages:
            html.append(f"""<div class="msgitem {tp}">{htmlEsc(msg)}</div>""")

        html.append("</div>")
        self.clearMessages()
        return "\n".join(html)

    def _addMessage(self, tp, msg):
        Settings = self.Settings

        if Settings is None:
            sys.stderr.write(f"{tp}: {msg}\n")
            sys.stderr.flush()
        else:
            debugMode = Settings.debugMode
            if tp != "debug" or debugMode:
                self.messages.append((tp, msg))
