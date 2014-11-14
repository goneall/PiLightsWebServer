PiLightsWebServer
=================

Web server running on a Raspberry Pi to control Christmas Lights

Usaage:
./lightsite.py
Starts up the web server on port 5000

The webserver can be configured with a configuration file in the environment variable PILIGHTSWEB_SETTING.

Following are the configuration variables:
* PORT - Port number for the webserver.  Default 5000.
* WEB_ROUTE_MAIN - Web routing for the main application.  Default '/lights'    
* WEB_ROUTE_SCHED - Web routing for the scheduling application.  Default WEB_ROUTE_MAIN + '/schedule'  
* WEB_ROUTE_PLAYLIST - Web routing for the playlist management app.  Default WEB_ROUTE_MAIN + '/playlist'
* DATABASE - File name of the SQLite database to hold user, schedule, and playlist information.  Default 'db'
* MUSIC_PATH - File path to the directory containing music MP3 files.  Default '/home/pi/music'
* DEBUG - If true, enable debug mode.  Default True

PiLightsWebServer uses the Apache 2.0 license (see LICENSE for text).

This web server uses (and depends on) Flask.

Flask can be installed by entering the following:
* sudo apt-get install pyton-pip
* sudo pip install Flask
