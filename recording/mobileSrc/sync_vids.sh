#!/bin/sh

## The start of this replicates a lot of  run_cam.sh to get the correct file names
## It then combines all the images into a .zip and drops it in recording

## Find the name, regardless of the pi.
. /home/pi/recording/current.config

if [[ -z "$box_dir" ]]; then
    pi_name=${HOSTNAME: -4}
else
    number=${HOSTNAME: -2}
    pi_name="${box_dir//\*/"$number"}" ## this clunky mess turns JON* into JON03
fi

## Copies and deletes the *.zip files in the recording directory (without checking sub directories)
rclone move /home/pi/recording --include "*.h264" --max-depth 2 --transfers 1 --delete-empty-src-dirs AmazonBox:/pivideos/$pi_name
