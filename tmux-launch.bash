#!/usr/bin/env bash

if [ "$1" == "" ]; then
    dir="./config"
else
    dir="$1"
fi

T1="./launch.bash $dir/1.cfg"
T2="./launch.bash $dir/2.cfg"
T3="./launch.bash $dir/3.cfg"
T4="./launch.bash $dir/4.cfg"
T5="./launch.bash $dir/5.cfg"
T6="./launch.bash $dir/6.cfg"
T7="./launch.bash $dir/7.cfg"
T8="bash"

tmux new-session "$T1" \; \
    split-window -v "$T5" \; \
        split-window -h "$T7" \; \
            split-window -h "$T8" \; \
            select-pane -L \; \
        select-pane -L \; \
        split-window -h "$T6" \; \
    select-pane -U \; \
        split-window -h "$T3" \; \
            split-window -h "$T4" \; \
            select-pane -L \; \
        select-pane -L \; \
        split-window -h "$T2" \; \
    select-pane -L \; \

