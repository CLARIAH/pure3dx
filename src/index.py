import os
from control.webdavapp import appFactory

# NB: it is intentionally from control.webdavapp and not from .control.webdavapp
# Otherwise, the deployment over gunicorn fails with a relative import error message.
# NB: there is no __init__.py at the toplevel of src.
# Otherwise, the deployment via the flask dev server fails with an import error.


flaskAppName = os.environ.get("FLASK_APP", None)

if flaskAppName:
    print(f"Making Flask app {flaskAppName}")
    app = appFactory()
