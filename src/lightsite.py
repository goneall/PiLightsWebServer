#!/usr/bin/env python
# Licensed under the Apache 2.0 License
# Author Gary O'Neall gary@sourceauditor.com
"""
Primary web application to control the lightshowPi

Usage: sudo lightsite.py
Website can be accessed on port 5000
The file also contains the default configuration parameters
"""
from logging import handlers
import logging
import sqlite3
import lightsinterface
from os import path, listdir
from hashlib import sha256
from flask import Flask, render_template, g, request, flash, redirect, url_for, session
from werkzeug.security import safe_join
from contextlib import closing
# Configuration
LOGFILE_NAME = '/var/log/lightsite/lightsite.log'
PORT = 5000
WEB_ROUTE_MAIN = '/lights'    # Web routing to the light site application
WEB_ROUTE_SCHED = WEB_ROUTE_MAIN + '/schedule'  # Web routing to the schedule app
WEB_ROUTE_PLAYLIST = WEB_ROUTE_MAIN + '/playlist'   # Web routing to the playlist app
DATABASE = 'db'
MUSIC_PATH = '/home/pi/music'  # Path to music directory
DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('PILIGHTSWEB_SETTINGS')
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
        # Add current playlist
        current_playlist = lightsinterface.getplaylist()
        for song in current_playlist:
            db.execute('insert into playlist(playorder, name, path) values (?, ?, ?)',
                              [song['playorder'], song['name'], song['path']])
        # Add one user
        password_hash = sha256('password')
        password_digest = password_hash.hexdigest()
        db.execute('insert into users(username, password) values (?, ?)', ['gary', password_digest])
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

@app.route(app.config['WEB_ROUTE_MAIN']+'/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        if username and username.strip() != '':
            cursor = g.db.execute('select password from users where username=?', [username.strip()])
            row = cursor.fetchone()
            if row:
                passwordstr = request.form['password']
                password_hash = sha256(passwordstr)
                if row[0] == password_hash.hexdigest():
                    session['logged_in'] = True
                    flash('You are logged in')
                else:
                    error = 'Invalid password'
            else:
                error = 'Username does not exist'
        else:
            error = 'Must provide a username'
    if error or request.method == 'GET':
        return render_template('login.html', error=error)
    else:
        return redirect(url_for('lightstatus'))

@app.route(app.config['WEB_ROUTE_MAIN']+'/logout')
def logout():
    session.pop('logged_in', None)
    flash('You are logged out')
    return redirect(url_for('lightstatus'))

@app.route(app.config['WEB_ROUTE_MAIN'])
def lightstatus():
    return render_template('lightsite.html', lightson=lightsinterface.lights_are_on, playliston=lightsinterface.playlist_playing)


@app.route(app.config['WEB_ROUTE_MAIN'] + '/update', methods=['POST'])
def updatelights():
    if (request.form['lightstatus'] == u'lightson'):
        lightsinterface.lights_on()
    elif (request.form['lightstatus'] == u'playliston'):
        lightsinterface.start_playlist()
    else:
        lightsinterface.lights_off()
    return redirect(url_for('lightstatus'))
    
@app.route(app.config['WEB_ROUTE_SCHED'])
def schedule():
    cursor = g.db.execute('select id, day, hour, minute, turnon, turnoff, startplaylist, stopplaylist from schedule order by day,hour,minute')
    rows = cursor.fetchall()
    entries = [dict(id=row[0], day=row[1], hour=row[2], minute=row[3], turnon=row[4], turnoff=row[5], 
                    startplaylist=row[6], stopplaylist=row[7]) for row in rows]
    return render_template('schedule.html', entries=entries)

@app.route(app.config['WEB_ROUTE_SCHED']+'/add', methods=['POST'])
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
        logging.error('Error adding new schedule record: '+str(ex))
        g.db.rollback()
        flash('Error adding schedule')
    finally:
        g.db.commit()
    return redirect(url_for('schedule'))

@app.route(app.config['WEB_ROUTE_SCHED']+'/delete', methods=['POST'])
def delete_schedule():
    schedule_id = int(request.form['delete_entry'])
    message = ''
    try:
        g.db.execute('delete from schedule where id=?', [schedule_id])
        message = 'Schedule item deleted'
    except Exception as ex:
        logging.error('Error deleting schedule record '+str(schedule_id)+':'+ str(ex))
        message = 'Error deleting schedule record'
    finally:
        g.db.commit()
    flash(message)
    return redirect(url_for('schedule'))
        
@app.route(app.config['WEB_ROUTE_PLAYLIST'])
def playlist():
    playlist = get_playlist_db()
    directory = get_files_not_in_playlist(playlist)
    return render_template('playlist.html', playlist=playlist, directory=directory)

def get_files_not_in_playlist(playlist):
    retval = []
    playlist_files = [playlist_item['path'] for playlist_item in playlist]
    song_files = listdir(app.config['MUSIC_PATH'])
    songnum = 0
    for songfile in song_files:
        if songfile.endswith('.mp3'):
            songfilepath = path.join(app.config['MUSIC_PATH'],songfile)
            if not songfilepath in playlist_files:
                retval.append(dict(id=songnum, filename=songfile))
                songnum = songnum + 1
    return retval

@app.route(app.config['WEB_ROUTE_PLAYLIST']+'/add', methods=['POST'])
def add_song():
    if 'add_entry' in request.form:
        entry_info = request.form['add_entry']
        entry_parts = entry_info.split('+')
        dirid = entry_parts[0]
        pathname = safe_join(app.config['MUSIC_PATH'],entry_parts[1])
        name = request.form['name'+str(dirid)]
        if not name or name == '':
            name = path.split(pathname)[1]
        append_playlist(name, pathname)
    return redirect(url_for('playlist'))

def append_playlist(name, path):
    try:
        # get the maximum order
        cursor = g.db.execute('select max(playorder) from playlist')
        row = cursor.fetchone()
        next_playorder = 1
        if (row):
            next_playorder = row[0] + 1
        g.db.execute('insert into playlist (playorder, name, path) values (?, ?, ?)', 
                             [next_playorder, name, path])
        lightsinterface.update_playlist(get_playlist_db())
        flash('Song Added')
    except Exception as ex:
        logging.error('Error deleting song: '+str(ex))
        g.db.rollback()
        flash('Error deleting song')
    finally:
        g.db.commit();        
        
@app.route(app.config['WEB_ROUTE_PLAYLIST']+'/upload', methods=['POST'])
def upload_song():
    songfile = request.files['file']
    if (songfile):
        if (songfile.filename.endswith('.mp3')):
            file_path = safe_join(app.config['MUSIC_PATH'], songfile.filename)
            songfile.save(file_path)
            name = request.form['name']
            if (not name or name == ''):
                name = path.split(file_path)[1]
            append_playlist(name, file_path)
        else:   #not mp3 file
            flash('File must be an mp3 file')
    return redirect(url_for('playlist'))

@app.route(app.config['WEB_ROUTE_PLAYLIST']+'/update', methods=['POST'])
def update_playlist():
    updated_playlist = None
    if ('move_up' in request.form):
        songid = int(request.form['move_up'])
        updated_playlist = move_song_up(songid)
    if ('delete_entry' in request.form):
        songid = int(request.form['delete_entry'])
        updated_playlist = delete_song(songid)  
        flash('Song deleted')
    lightsinterface.update_playlist(updated_playlist)
    return redirect(url_for('playlist'))

def delete_song(songid):
    try:
        g.db.execute('delete from playlist where id=?', [songid])
    except Exception as ex:
        logging.error('Error deleting song: '+str(ex))
        g.db.rollback()
        flash('Error deleting song')
    finally:
        g.db.commit();
    return get_playlist_db()

def move_song_up(songid):
    # Get the current list
    cursor = g.db.execute('select id, playorder, name, path from playlist order by playorder')
    rows = cursor.fetchall()
    current_position = -1
    current_row_index = -1
    min_position = 9999
    max_position = -1
    rowcounter = 0
    for row in rows:    # get the positions
        if (row[1] < min_position):
            min_position = row[1]
        if (row[1] > max_position):
            max_position = row[1]
        if (row[0] == songid):
            current_position = row[1]
            current_row_index = rowcounter
        rowcounter = rowcounter + 1
    try:
        if (current_position == min_position):
            # roll around to the max position - this also works for a list of one song
            for i in range(1, len(rows)):
                g.db.execute('update playlist set playorder=? where id=?', [i-1, rows[i][0]])
            g.db.execute('update playlist set playorder=? where id=?', [len(rows), rows[0][0]])
        else:
            # Swap entries
            g.db.execute('update playlist set playorder=? where id=?', [rows[current_row_index][1], rows[current_row_index-1][0]])
            g.db.execute('update playlist set playorder=? where id=?', [rows[current_row_index-1][1], rows[current_row_index][0]])
    except Exception as ex:
        logging.error('Error changing playlist order: '+str(ex))
        g.db.rollback()
        flash('Error moving song')
    finally:
        g.db.commit();
    return get_playlist_db()

def get_playlist_db():
    cursor = g.db.execute('select id, playorder, name, path from playlist order by playorder')
    rows = cursor.fetchall()
    return [dict(id=row[0], playorder=row[1], name=row[2], path=row[3], filename=path.split(row[3])[1]) for row in rows]


if __name__ == "__main__":   
    app.run('0.0.0.0', port=app.config['PORT'])
