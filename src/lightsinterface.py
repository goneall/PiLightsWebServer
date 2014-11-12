'''
Created on Nov 11, 2014

@author: Gary O'Neall
Licensed under the Apache 2.0 License

Interface module for the lightpi
Currently, these are just stubs used to test the web interface
'''

playlist = [{'id':1, 'name':'name1', 'path':'path1'}, {'id':2, 'name':'name2', 'path':'path2'}]

def getplaylist():
    #TODO: Implement
    return playlist

def playlist_move_up(position):
    playlist2 = playlist # implement
    
def delete_playlist_song(position):
    playlist2 = playlist # TODO: implement

if __name__ == "__main__":
    print 'This module intefaces to the lightshowpi modules'