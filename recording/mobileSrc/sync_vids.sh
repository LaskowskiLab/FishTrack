#!/bin/sh

## The start of this replicates a lot of  run_cam.sh to get the correct file names
## It then combines all the images into a .zip and drops it in recording

config=${1-0}
echo $config
if [[ "$config" == "0" ]]; then
    config="/home/pi/recording/mobileSrc/current.config"
fi


. $config

## Get video format (pi4 vs pi5)
if [ -z ${format} ]; then
    format="h264"
fi

## Find the name, regardless of the pi.
if [ -z ${pi_name} ]; then
    pi_name=${HOSTNAME: -4}
else
    num=${HOSTNAME: -2}
    pi_name=${pi_name//\*/$num} ## replace * with num
fi

### If the above failed, just use the hostname
if [ -z "$pi_name" ]; then
    pi_name=$HOSTNAME
fi



## Copies and deletes the *.zip files in the recording directory (without checking sub directories)
rclone move /home/pi/recording --include "*.$format" --max-depth 2 --transfers 1 --delete-empty-src-dirs AmazonBox:/pivideos/$pi_name
