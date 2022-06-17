#!/bin/bash

secs10=10
secs2=3
t_end=${1-4}

timestamp=$(date)
echo $timestamp

export PATH="/home/ammon/anaconda3/bin:$PATH"
source activate tracking

while (( SECONDS < $secs10 )); do
    echo 'tick'
    echo $SECONDS
    if (( SECONDS > t_end )); then
        echo 'Time is up'
        break
    fi
done

