#!/usr/bin/env python
'''
Created on Nov 11, 2014

@author: Gary O'Neall
Licensed under the Apache 2.0 License

Interface module for the lightshowPi

The environment variable $PLAYLIST_FILE must be set for the file used as a playlist
'''
import subprocess
from configuration_manager import songs, set_songs
from hardware_controller import turn_on_lights, turn_off_lights, initialize, clean_up
from os import path
import sys

lights_are_on = False
playlist_playing = False
initialized = False
playing_process = None
playlist_file = '$PLAYLIST_FILE'

def getplaylist():
    current_songs = songs()
    # Format of the songs is name, path, number of votes
    # Need to convert the number of votes into a play order
    current_songs.sort(current_songs, key=lambda song: len(song[2]), reverse=True)
    playlist = []
    order = 1
    for song in current_songs:
        playlist.append({'playorder':order, 'name':song[0], 'path':song[1]})
        order = order + 1
    return playlist

def update_playlist(updated_playlist):
    new_songs = []
    updated_playlist.sort(updated_playlist, key=lambda item: item['playorder'])
    last_song = updated_playlist[len(updated_playlist)-1]
    max_order = last_song['playorder']
    with open(path.expandvars(playlist_file), 'w') as f:
        for item in updated_playlist:
            # Hack alert - I don't really understand the votes and what information we
            # are loosing here
            # Create a set the same size as the list size - play order
            vote_set = set()
            num_votes = max_order - item['playorder']
            for vote in range(0, num_votes):
                vote_set.add(str(vote))
            new_songs.append([item['name'], item['path'], vote_set])
            f.write(item['name'] + '\t' + item['path'] + '\n')
        set_songs(new_songs)

def lights_on():
    global lights_are_on, playlist_playing
    initialize_interface()
    if playlist_playing:
        stop_playlist()
    turn_on_lights()
    lights_are_on = True

def lights_off():
    global lights_are_on, playlist_playing
    initialize_interface()
    if playlist_playing:
        stop_playlist()
    turn_off_lights()
    lights_are_on = False

def start_playlist():
    global lights_are_on, playlist_playing, playing_process
    initialize_interface()
    if lights_are_on:
        lights_off()
    if playing_process:
        playing_process.kill()
        playing_process = None
    args = [path.expandvars('$SYNCHRONIZED_LIGHTS_HOME/py/synchronized_lights.py'), 
                    '--playlist='+path.expandvars(playlist_file)]
    playing_process = subprocess.Popen(args)
    playlist_playing = True
   

def stop_playlist():
    global lights_are_on, playlist_playing, playing_process
    initialize_interface()
    if lights_are_on:
        lights_off()
    if playing_process:
        playing_process.kill()
    playlist_playing = False
        
def initialize_interface():
    global initialized
    if not initialized:
        initialize()
        initialized = True
        
def cleanup():
    global initialized
    clean_up()
    initialized = False
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print 'This module intefaces to the lightshowpi modules'
    elif sys.argv[1].strip() == '--lightson':
        lights_on()
    elif sys.argv[1].strip() == '--lightsoff':
        lights_off()
    elif sys.argv[1].strip() == '--startplaylist':
        start_playlist()
    elif sys.argv[1].strip() == '--stopplaylist':
        stop_playlist()
    else:
        print 'Invalid argument.  Expected --lightson, --lightsoff, --startplaylist, or --stopplaylist'
