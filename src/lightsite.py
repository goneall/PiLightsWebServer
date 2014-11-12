#!/usr/bin/env python
# Licensed under the Apache 2.0 License
# Author Gary O'Neall gary@sourceauditor.com
"""
Primary web application to control the lightshowPi

Usage: sudo lightsite.py
Website can be accessed on port 5000
"""
from logging import handlers
import logging
import sqlite3
import lightsinterface
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
    cursor = g.db.execute('select id, day, hour, minute, turnon, turnoff, startplaylist, stopplaylist from schedule order by day,hour,minute')
    rows = cursor.fetchall()
    entries = [dict(id=row[0], day=row[1], hour=row[2], minute=row[3], turnon=row[4], turnoff=row[5], 
                    startplaylist=row[6], stopplaylist=row[7]) for row in rows]
    return render_template('schedule.html', entries=entries)
@app.route(app.config['WEB_ROUTE_MAIN']+'/schedule/add', methods=['POST'])

def add_schedule():
    try:
        # actions
        action = request.form['action']
        turnon = action == 'turnon'
        turnoff = action == 'turnoff'
        startplaylist = action == 'startplaylist'
        stopplaylist = action == 'stopplaylist'
        
        # time
        hour = int(request.form['hour'])
        minutes = int(request.form['minutes'])
        ampm = request.form['ampm']
        if (ampm == 'PM'):
            hour = hour + 12
        if (minutes < 0 or minutes > 59):
            flash('Minutes must be greater than 0 and less than 59')
            raise Exception('Invalid minutes')
        g.db.execute('insert into schedule (day, hour, minute, turnon, turnoff, startplaylist, stopplaylist) values (?, ?, ?, ?, ?, ?, ?)',
                     [request.form['day'], hour, minutes, turnon,
                      turnoff, startplaylist, stopplaylist])
        flash('Schedule updated')
    except Exception as ex:
        logging.error('Error adding new schedule record: '+ex.message)
        g.db.rollback()
        flash('Error adding schedule')
    finally:
        g.db.commit()
    return redirect(url_for('schedule'))

@app.route(app.config['WEB_ROUTE_MAIN']+'/schedule/delete', methods=['POST'])
def delete_schedule():
    schedule_id = int(request.form['delete_entry'])
    message = ''
    try:
        g.db.execute('delete from schedule where id=?', [schedule_id])
        message = 'Schedule item deleted'
    except Exception as ex:
        logging.error('Error deleting schedule record '+str(schedule_id)+':'+ ex.message)
        message = 'Error deleting schedule record'
    finally:
        g.db.commit()
    flash(message)
    return redirect(url_for('schedule'))
        
@app.route(app.config['WEB_ROUTE_MAIN']+'/playlist')
def playlist():
    current_playlist = lightsinterface.getplaylist()
    return render_template('playlist.html', playlist=current_playlist)

@app.route(app.config['WEB_ROUTE_MAIN']+'/playlist/add', methods=['POST'])
def add_song():
    flash('Song Added')
    return redirect(url_for('playlist'))

@app.route(app.config['WEB_ROUTE_MAIN']+'/playlist/update', methods=['POST'])
def update_playlist():
    if ('move_up' in request.form):
        lightsinterface.playlist_move_up(int(request.form['move_up']))
    if ('delete_entry' in request.form):
        lightsinterface.delete_playlist_song(int(request.form['delete_entry']))        
        flash('Song deleted')
    return redirect(url_for('playlist'))

if __name__ == "__main__":   
    app.run('0.0.0.0')