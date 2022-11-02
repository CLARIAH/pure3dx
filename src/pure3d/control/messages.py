import sys
from flask import abort

from control.helpers.generic import htmlEsc


class Messages:
    def __init__(self, config, flask=True):
        """Sending messages to the user and sysadmin.

        This class has methods to issue messages to the screen of the webuser
        and to the log for the sysadmin.

        It is instantiated by a singleton object.

        Parameters
        ----------
        config: AttrDict
            App-wide configuration data obtained from
            `control.config.Config.config`.
        """
        self.config = config
        self.messages = []
        self.flask = flask

    def clearMessages(self):
        self.messages.clear()

    def debugAdd(self, dest):
        def dbg(m):
            self.debug(logmsg=m)
        setattr(dest, "debug", dbg)

    def debug(self, msg=None, logmsg=None):
        if msg is not None:
            self._addMessage("debug", f"DEBUG: {msg}")
        if logmsg is not None:
            sys.stderr.write(f"DEBUG: {logmsg}\n")
            sys.stderr.flush()

    def error(self, msg=None, logmsg=None):
        if msg is not None:
            self._addMessage("error", f"ERROR: {msg}")
        if logmsg is not None:
            sys.stderr.write(f"ERROR: {logmsg}\n")
            sys.stderr.flush()
            if self.flask:
                abort(404)

    def warning(self, msg=None, logmsg=None):
        if msg is not None:
            self._addMessage("warning", f"WARNING: {msg}")
        if logmsg is not None:
            sys.stderr.write(f"WARNING: {logmsg}\n")
            sys.stderr.flush()

    def info(self, msg=None, logmsg=None):
        if msg is not None:
            self._addMessage("info", f"INFO: {msg}")
        if logmsg is not None:
            sys.stdout.write(f"INFO: {logmsg}\n")
            sys.stdout.flush()

    def plain(self, msg=None, logmsg=None):
        if msg is not None:
            self._addMessage("info", msg)
        if logmsg is not None:
            sys.stdout.write(f"{logmsg}\n")
            sys.stdout.flush()

    def generateMessages(self):
        html = ["""<div class="messages">"""]

        for (tp, msg) in self.messages:
            html.append(f"""<div class="msgitem {tp}">{htmlEsc(msg)}</div>""")

        html.append("</div>")
        self.clearMessages()
        return "\n".join(html)

    def _addMessage(self, tp, msg):
        config = self.config

        if config is None:
            sys.stderr.write(f"{tp}: {msg}\n")
            sys.stderr.flush()
        else:
            debugMode = config.debugMode
            if tp != "debug" or debugMode:
                self.messages.append((tp, msg))
