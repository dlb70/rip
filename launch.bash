#!/usr/bin/env bash


while python3 rip.py $1; do
    read -p "Press [ENTER] to restart router, [CTRL+C] to exit."
done
