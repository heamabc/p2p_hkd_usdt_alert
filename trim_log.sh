#!/bin/bash
number_of_line="$(wc -l log/p2p_notification.log)"
number_of_line=${number_of_line:0:3}
number_of_line=${number_of_line:-0}

if [ "$number_of_line" -gt 100 ];
then
    now=$(date +"%T")
    echo "Current time : $now. Number of line is greater then or equal to 100, need to trim"
    echo "$(tail -100 log/p2p_notification.log)" > log/p2p_notification.log
fi
