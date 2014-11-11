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
app.secret_key = '\xf4\x9a\x8f\x08\xd6\xedg\xe4W1f\x87\x1a\x9al\xfa\x90\xb2!"R0b\x10'

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
def lightstatus():
    return render_template('lightsite.html', lightson=False, playliston=True)

@app.route(app.config['WEB_ROUTE_MAIN'] + '/update', methods=['POST'])
def updatelights():
    if (request.form['lightstatus'] == u'lightson'):
        lightson = True # replace with call to library
    elif (request.form['lightstatus'] == u'playliston'):
        playliston = True
    else:
        alloff = True
    return redirect(url_for('lightstatus'))
    
@app.route(app.config['WEB_ROUTE_SCHED'])
def schedule():
    cursor = g.db.execute('select id, day, hour, minute, turnon, turnoff, startplaylist, stopplaylist from schedule order by id')
    entries = [dict(id=row[0], day=row[1], hour=row[2], minute=row[3], turnon=row[4], turnoff=row[5], 
                    startplaylist=row[6], stopplaylist=row[7]) for row in cursor.fetchall()]
    return render_template('schedule.html', entries=entries)

@app.route(app.config['WEB_ROUTE_MAIN']+'/schedule/add', methods=['POST'])
def add_schedule():
    try:
        action = request.form['action']
        turnon = action == 'turnon'
        turnoff = action == 'turnoff'
        startplaylist = action == 'startplaylist'
        stopplaylist = action == 'stopplaylist'
        time = '0:0'
        if ('time' in request.form):
            time = request.form['time']
        timep = time.split(':')
        hour = timep[0]
        minute = 0
        if (len(timep) > 1):
            minute = timep[1]
        g.db.execute('insert into schedule (day, hour, minute, turnon, turnoff, startplaylist, stopplaylist) values (?, ?, ?, ?, ?, ?, ?)',
                     [request.form['day'], hour, minute, turnon,
                      turnoff, startplaylist, stopplaylist])
        flash('Schedule updated')
    except Exception as ex:
        logging.error('Error adding new schedule record: '+ex.message)
        flash('Error adding schedule')
    finally:
        g.db.commit()
    return redirect(url_for('schedule'))

@app.route(app.config['WEB_ROUTE_MAIN']+'/schedule/delete', methods=['POST'])
def delete_schedule():
    schedule_id = int(request.form['delete_entry'])
    try:
        g.db.execute('delete from schedule where id=?', [schedule_id])
        flash('Schedule item deleted')
    except Exception as ex:
        logging.error('Error deleting schedule record '+str(schedule_id)+':'+ ex.message)
        flash('Error deleting schedule record')
    finally:
        g.db.commit
    return redirect(url_for('schedule'))
        
@app.route(app.config['WEB_ROUTE_MAIN']+'/playlist')
def playlist():
    current_playlist = ['need to fill in', 'second song.mp3']
    return render_template('playlist.html', playlist=current_playlist)

@app.route(app.config['WEB_ROUTE_MAIN']+'/playlist/add')
def add_song():
    flash('Song Added')
    return redirect(url_for('playlist'))

if __name__ == "__main__":
    
    app.run('0.0.0.0')