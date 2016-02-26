#!/usr/bin/env bash
### Initialization script for RIP simulation ###

for i in {1..7}; do
  echo $i
  gnome-terminal -e "python3 rip.py $i.cfg" -t "Router $i" &
done
