#!/bin/sh

## The start of this replicates a lot of  run_cam.sh to get the correct file names
## It then combines all the images into a .zip and drops it in recording

## Find the name, regardless of the pi.
pi_name=${HOSTNAME: -4}
if [[ $pi_name == "rypi" ]]; then
    pi_name='pi01'
fi

## Copy only the *.zip files in the recording directory (without checking sub directories)
rclone copy /home/pi/recording --include "*.zip" --max-depth 2 AmazonBox:/pivideos/$pi_name
