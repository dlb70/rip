#!/usr/bin/env bash
while python3 rip.py config/$1.cfg; do
    read -p "Press [ENTER] to restart router, [CTRL+C] to exit."
done
