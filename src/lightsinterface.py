'''
Created on Nov 11, 2014

@author: Gary O'Neall
Licensed under the Apache 2.0 License

Interface module for the lightpi
Currently, these are just stubs used to test the web interface
'''

# TODO: Replace with a call to playlist
playlist = [{'playorder':1, 'name':'name1', 'path':'path1'}, {'playorder':2, 'name':'name2', 'path':'path2'}]

def getplaylist():
    #TODO: Implement
    return playlist

def update_playlist(updated_playlist):
    #TODO Implement
    playlist = updated_playlist

def lights_on():
    #TODO: Implement
    lisghtson=True

def lights_off():
    #TODO: Implement
    lightsoff=True

def start_playlist():
    #TODO Implement
    startPlaylist=True
    
if __name__ == "__main__":
    print 'This module intefaces to the lightshowpi modules'