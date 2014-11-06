from logging import handlers
import logging
from flask import Flask
from flask import render_template
LOGFILE_NAME = '/var/log/lightsite/lightsite.log'

app = Flask(__name__)
# Enable logging
file_handler = handlers.RotatingFileHandler(LOGFILE_NAME)
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)

@app.route("/")
def hello(name=None):
  return render_template('lightsite.html')

if __name__ == "__main__":
  app.run('0.0.0.0')
