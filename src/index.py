from logging.config import dictConfig

import os
from control.webdavapp import appFactory
from control.environment import var
from control.files import dirMake

# NB: it is intentionally from control.webdavapp and not from .control.webdavapp
# Otherwise, the deployment over gunicorn fails with a relative import error message.
# NB: there is no __init__.py at the toplevel of src.
# Otherwise, the deployment via the flask dev server fails with an import error.


def logConfig(app):
    """Configure logging.

    Flask and Gunicorn use the standard Python logging module.

    We configure logging in such a way that:

    *   the logging goes to file
    *   the files are rotated on a daily basis with a backup of 31 days
    *   the files reside on a persistent volume, when the app is deployed on k8s

    When the app runs in debug mode, there is no gunicorn, and we configure
    a default formatter and wsgi log handler for Flask.

    Otherwise, Flask runs under Gunicorn, and we configure a generic formatter
    and and console log handler for Gunicorn.
    On top of that

    *   we configure gunicorn loggers;
    *   we hook up the flask logger to the gunicorn loggers

    Parameters
    ----------
    app: object
        The flask app. Needed when we need to hook up the flask loggers
        with the gunicorn loggers.
    """

    logDir = var("LOG_DIR")
    runMode = var("runmode")
    logDir = f"{logDir}/{runMode}"
    dirMake(logDir)
    debug = var("flaskdebug") == "v"
    debugRep = "-debugmode" if debug else ""
    logFile = f"{logDir}/flask{debugRep}.log"
    print(f"log file = {logFile}")

    if debug:
        dictConfig(
            {
                "version": 1,
                "formatters": {
                    "default": {
                        "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                    }
                },
                "handlers": {
                    "wsgi": {
                        "class": "logging.handlers.TimedRotatingFileHandler",
                        "filename": logFile,
                        "formatter": "default",
                        "when": "D",
                        "interval": 1,
                        "backupCount": 30,
                    }
                },
                "root": {"level": "INFO", "handlers": ["wsgi"]},
            }
        )
    else:
        dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "root": {"level": "INFO", "handlers": ["console"]},
                "loggers": {
                    "gunicorn.error": {
                        "level": "INFO",
                        "handlers": ["console"],
                        "propagate": True,
                        "qualname": "gunicorn.error",
                    },
                    "gunicorn.access": {
                        "level": "INFO",
                        "handlers": ["console"],
                        "propagate": True,
                        "qualname": "gunicorn.access",
                    },
                },
                "handlers": {
                    "console": {
                        "class": "logging.handlers.TimedRotatingFileHandler",
                        "filename": logFile,
                        "formatter": "generic",
                        "when": "D",
                        "interval": 1,
                        "backupCount": 30,
                    },
                },
                "formatters": {
                    "generic": {
                        "format": "%(asctime)s [%(process)d] [%(levelname)s] %(message)s",
                        "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
                        "class": "logging.Formatter",
                    }
                },
            }
        )


flaskAppName = os.environ.get("FLASK_APP", None)

if flaskAppName:
    print(f"Making Flask app {flaskAppName}")
    app = appFactory()
    logConfig(app)
