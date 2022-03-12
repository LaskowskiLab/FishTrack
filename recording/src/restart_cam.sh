#! /usr/bin/env bash

## Quick script to restart run_cam.sh when it dies

# Kill existing raspistill process
pkill raspistill

# Restart new run_cam
bash /home/pi/recording/src/run_cam.sh >> /home/pi/recording/cronlog.log 2>&1
