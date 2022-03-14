#!/bin/bash

nohup python3 plot.py &>/dev/null &
python3 simulation.py

# stop the plottting when the simulation
# finishes or is canceled with ^C
ps aux | grep -v grep | grep plot.py | awk '{print $2}' | xargs kill