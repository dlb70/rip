#!/usr/bin/env bash
### Initialization script for RIP simulation ###

for i in 1 2 3; do
  echo $i;
  gnome-terminal -e "python3 rip.py config/$i.cfg" -t "Router $i" &
  sleep 0.2
done
