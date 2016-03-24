#!/usr/bin/env bash
### Initialization script for RIP simulation ###

GEOM="--geometry=50x26"

dir="./$1"

for cfg in $dir/*.cfg; do
  echo $cfg;
  gnome-terminal $GEOM -e "./launch.bash $cfg" -t "Router $cfg" &
  sleep 0.2
done
