from control.app import appFactory
from control.webdavapp import getWebdavApp
from control.dispatcher import dispatchWebdav


app = appFactory()
app.wsgi_app = dispatchWebdav(appFactory(), "/webdav/", getWebdavApp())
