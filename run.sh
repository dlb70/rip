#!/usr/bin/env bash
### Initialization script for RIP simulation ###

GEOM="--geometry=50x26"

for i in {1..7}; do
  echo $i;
  gnome-terminal $GEOM -e "python3 rip.py config/$i.cfg" -t "Router $i" &
  sleep 0.2
done
