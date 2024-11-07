import os
from .control.webdavapp import appFactory

flaskAppName = os.environ.get("FLASK_APP", None)

if flaskAppName:
    print(f"Making Flask app {flaskAppName}")
    app = appFactory()
