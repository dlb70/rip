#!/usr/bin/env bash
# CMD=bash
# T1="echo 1 && $CMD"
# T2="echo 2 && $CMD"
# T3="echo 3 && $CMD"
# T4="echo 4 && $CMD"
# T5="echo 5 && $CMD"
# T6="echo 6 && $CMD"
# T7="echo 7 && $CMD"
# T8="echo 8 && $CMD"

T1="./router.bash 1"
T2="./router.bash 2"
T3="./router.bash 3"
T4="./router.bash 4"
T5="./router.bash 5"
T6="./router.bash 6"
T7="./router.bash 7"
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

#python3 rip.py config/$i.cfg
