import os

from wsgidav.wsgidav_app import WsgiDAVApp

from control.config import Config
from control.messages import Messages


config = Config(Messages(None), dataDirOnly=True).config

BASE = os.path.dirname(os.path.dirname(__file__))

WEBDAV_METHODS = dict(
    HEAD="view",
    GET="view",
    PUT="edit",
    POST="edit",
    OPTIONS="view",
    TRACE="view",
    DELETE="edit",
    PROPFIND="view",
    PROPPATCH="edit",
    MKCOL="edit",
    COPY="edit",
    MOVE="edit",
    LOCK="edit",
    UNLOCK="edit",
)


config = {
    "provider_mapping": {
        "/webdav/": {
            "root": config.dataDir,
            "readonly": False,
        },
    },
    "simple_dc": {"user_mapping": {"*": True}},
    "verbose": 1,
}


def getWebdavApp():
    return WsgiDAVApp(config)
