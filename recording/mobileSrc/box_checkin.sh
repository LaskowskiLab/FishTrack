#!/bin/sh

## The start of this replicates a lot of  run_cam.sh to get the correct file names
## It then combines all the images into a .zip and drops it in recording

## Find the name, regardless of the pi.
pi_name=${HOSTNAME: -4}

scheduled=${1-1}

hour=$(date +"%H")
dhour="$((hour-6))"
dseconds="$((dhour*60*60))"

date > /home/pi/recording/hourly_check.txt
pgrep rpicam >> /home/pi/recording/hourly_check.txt
echo "(a number means it's recording, if there's no number it's not)" >> /home/pi/recording/hourly_check.txt

grep 'mmal' /home/pi/recording/cronlog.log | head -1 >> /home/pi/recording/hourly_check.txt
grep 'ERROR' /home/pi/recording/cronlog.log | head -1 >> /home/pi/recording/hourly_check.txt
grep 'token' /home/pi/recording/cronlog.log | head -1 | grep 'token' | cut -c -52 >> /home/pi/recording/hourly_check.txt
grep 'tvservice' /home/pi/recording/cronlog.log | head -1 >> /home/pi/recording/hourly_check.txt
## Check for zhombie camera process
# This always shows the grep line, which isn't ideal...
#pgrep rpicam | xargs ps -f | grep Z >> /home/pi/recording/hourly_check.txt

## Grab most recent video clip? 
#ffmpeg -framerate 1 -sseof -2 -i /home/pi/recording/current.link -update 1 -q:v 1 /home/pi/recording/recent_cap.jpg -y
rm /home/pi/recording/recent_cap.jpg

#if pgrep rpicam; then
if [[ "$scheduled" == 1 ]]; then
    ffmpeg -framerate 1 -i /home/pi/recording/current.link -ss $dseconds -vframes 1 -update true /home/pi/recording/recent_cap.jpg -y
else
    libcamera-still -q 20 -t 1 -o /home/pi/recording/recent_cap.jpg --nopreview
fi

filename=$(ls -lrt /home/pi/recording/current.link | nawk '{print $11}')

filesize=$(ls -lrt $filename | nawk '{print $5}')
oldsize=$(cat /home/pi/recording/current_size.txt)

if pgrep rpicam; then
    if [[ "$filesize" == "$oldsize" ]]; then
        echo "File not growing!" >> /home/pi/recording/hourly_check.txt
    fi
fi

echo $filesize > /home/pi/recording/current_size.txt

rclone copy /home/pi/recording/recent_cap.jpg AmazonBox:/pivideos/$pi_name/_monitoring_


## Copies and deletes the *.zip files in the recording directory (without checking sub directories)
rclone copy /home/pi/recording/hourly_check.txt AmazonBox:/pivideos/$pi_name/_monitoring_
