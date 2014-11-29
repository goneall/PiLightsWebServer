#!/bin/bash
#
# Plays the entire playlist.  Single parameter, playlist file

while true; do
  sudo python $SYNCHRONIZED_LIGHTS_HOME/py/synchronized_lights.py $1
done