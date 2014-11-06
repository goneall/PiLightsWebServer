from logging import handlers
import logging
from flask import Flask, url_for, render_template
LOGFILE_NAME = '/var/log/lightsite/lightsite.log'
#LOGFILE_NAME = 'lightsite.log'
WEB_ROUTE = '/lights'    # Web routing to the light site application
app = Flask(__name__)
#app.debug=True
# Enable logging
file_handler = handlers.RotatingFileHandler(LOGFILE_NAME)
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)

@app.route(WEB_ROUTE)
def hello():
    return render_template('lightsite.html', lightOn=False)

if __name__ == "__main__":
    app.run('0.0.0.0')