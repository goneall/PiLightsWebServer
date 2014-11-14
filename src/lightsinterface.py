'''
Created on Nov 11, 2014

@author: Gary O'Neall
Licensed under the Apache 2.0 License

Interface module for the lightshowPi
Currently, these are just stubs used to test the web interface
'''
from configuration_manager import songs, set_songs
from hardware_controller import turn_on_lights, turn_off_lights, initialize

lights_are_on = False
playlist_playing = False
initialized = False

def getplaylist():
    current_songs = songs()
    # Format of the songs is name, path, number of votes
    # Need to convert the number of votes into a play order
    sorted(current_songs, key=lambda song: len(song[2]), reverse=True)
    playlist = []
    order = 1
    for song in current_songs:
        playlist.append({'playorder':order, 'name':song[0], 'path':song[1]})
        order = order + 1
    return playlist

def update_playlist(updated_playlist):
    new_songs = []
    sorted(updated_playlist, key=lambda item: item.playorder)
    max_order = updated_playlist[len(updated_playlist)-1].playorder
    for item in updated_playlist:
        # Hack alert - I don't really understand the votes and what information we
        # are loosing here
        # Create a set the same size as the list size - play order
        vote_set = set()
        num_votes = max_order - item.playorder
        for vote in range(0, num_votes):
            vote_set.add(str(vote))
        new_songs.append([item.name, item.path, vote_set])
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
    global lights_are_on, playlist_playing
    initialize_interface()
    if lights_are_on:
        lights_off()
    #TODO: Implement
    
    
def stop_playlist():
    global lights_are_on, playlist_playing
    initialize_interface()
    if lights_are_on:
        lights_off()
        
def initialize_interface():
    global initialized
    if not initialized:
        initialize()
        initialized = True
    #TODO: Implement
    
if __name__ == "__main__":
    print 'This module intefaces to the lightshowpi modules'