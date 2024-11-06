from .generic import AttrDict
from .config import Config as ConfigCls


class MessagesCls:
    def __init__(self, dummy):
        pass

    def debugAdd(self, dummy):
        pass

    def info(self, logmsg=None):
        print(f"INFO: {logmsg}\n")

    def error(self, logmsg=None):
        print(f"ERROR: {logmsg}\n")


def prepare():
    """Prepares some objects of the Flask app for a task outside the web app.

    Several classes are instantiated with a singleton object;
    each of these objects has a dedicated task in the app:

    * `control.config.Config.Settings`: all configuration aspects
    * `control.messages.Messages`: handle all messaging to user and sysadmin

    Returns
    -------
    AttrDict
        A dictionary keyed by the names of the singleton objects and valued
        by the singleton objects themselves.

    """
    settingsAtts = dict(migrate=True, design=False)
    Settings = ConfigCls(MessagesCls(None), **settingsAtts).Settings
    Messages = MessagesCls(Settings)

    return AttrDict(Settings=Settings, Messages=Messages)
