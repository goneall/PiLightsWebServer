#!/bin/bash
# Plays entire playlist - single parameter playlist name
while true; do
   sudo python $SYNCHRONIZED_LIGHTS_HOME/py/synchronized_lights.py $1
done
