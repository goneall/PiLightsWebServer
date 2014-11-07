from logging import handlers
import logging
import sqlite3
from os import path
from flask import Flask, render_template, g, request, flash, redirect, url_for
from contextlib import closing
# Configuration
#LOGFILE_NAME = '/var/log/lightsite/lightsite.log'
LOGFILE_NAME = 'lightsite.log'
WEB_ROUTE_MAIN = '/lights'    # Web routing to the light site application
WEB_ROUTE_SCHED = WEB_ROUTE_MAIN + '/schedule'  # Web routing to the schedule app
DATABASE = 'db'
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)

app.debug=app.config['DEBUG']
# Enable logging
file_handler = handlers.RotatingFileHandler(app.config['LOGFILE_NAME'])
if (app.config['DEBUG']):
    file_handler.setLevel(logging.DEBUG)
else:
    file_handler.setLevel(logging.WARN)
app.logger.addHandler(file_handler)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('lightsdb.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    if (not path.isfile(app.config['DATABASE'])):
        init_db()
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route(app.config['WEB_ROUTE_MAIN'])
def hello():
    return render_template('lightsite.html', lightOn=False)

@app.route(app.config['WEB_ROUTE_SCHED'])
def schedule():
    cursor = g.db.execute('select id, day, hour, minute, turnon, turnoff, startplaylist, stopplaylist from schedule order by id')
    entries = []
    for row in cursor.fetchall():
        entries[0] = dict(id=row[0], day=row[1], minute=row[2], turnon=row[3], startplaylist=row[4], stoplaylist=row[5])
    return render_template('schedule.html')

@app.route(app.config['WEB_ROUTE_MAIN']+'/add', methods=['POST'])
def add_schedule():
    g.db.execute('insert into schedule (day, hour, minute, turnon, turnoff, startplaylist, stopplayist) values (?, ?, ?, ?, ?, ?, ?)',
                 request.form['day'], request.form['hour'], request.form['minute'], request.form['turnon'],
                 request.form['startplaylist'], request.form['stopplaylist'])
    g.db.commit()
    flash('Schedule updated')
    return redirect(url_for('schedule'))

if __name__ == "__main__":
    
    app.run('0.0.0.0')