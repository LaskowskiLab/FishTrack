#!/bin/sh

## The start of this replicates a lot of  run_cam.sh to get the correct file names
## It then combines all the images into a .zip and drops it in recording

## Find the name, regardless of the pi.
pi_name=${HOSTNAME: -4}
if [[ $pi_name == "rypi" ]]; then
    pi_name='pi01'
fi

date > /home/pi/recording/hourly_check.txt
pgrep raspivid >> /home/pi/recording/hourly_check.txt
echo "(a number means it's recording, if there's no number it's not)" >> /home/pi/recording/hourly_check.txt

grep 'mmal' /home/pi/recording/cronlog.log | head -1 >> /home/pi/recording/hourly_check.txt
grep 'token' /home/pi/recording/cronlog.log | head -1 | grep 'token' | cut -c -52 >> /home/pi/recording/hourly_check.txt
grep 'tvservice' /home/pi/recording/cronlog.log | head -1 >> /home/pi/recording/hourly_check.txt

## Grab most recent video clip? 
ffmpeg -framerate 1 -sseof -2 -i /home/pi/recording/current.link -update 1 -q:v 1 /home/pi/recording/recent_cap.jpg
rclone copy /home/pi/recording/recent_cap.jpg AmazonBox:/pivideos/$pi_name/_monitoring_

## Copies and deletes the *.zip files in the recording directory (without checking sub directories)
rclone copy /home/pi/recording/hourly_check.txt AmazonBox:/pivideos/$pi_name/_monitoring_
