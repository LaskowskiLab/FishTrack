#!/bin/sh

## Run's video. Input argument are hours, minutes, and framerate
# e.g., run_vid.sh 10 0 2 would record for 10 hours and 0 minutes at 2 fps
n_hours=${1-12}
n_minutes=${2-60}
f_rate=${3-1}

if [ -f "/home/pi/recording/suffix.txt" ]; then
    suffix=$(cat ~/recording/suffix.txt)
else
    suffix='rogue'    
fi

## Find the name, regardless of the pi.
pi_name=${HOSTNAME: -4}
if [[ $pi_name == "rypi" ]]; then
    pi_name='pi01'
fi

## The obvious behavior is to say 1 hour and 0 minutes, 
##   or 0 hours and 10 minutes. 

year_stamp=$(date "+%Y.%m")

## Run for 12 hours (43200000 ms), 1000 ms apart, -vf and -hf flip the video
## -h and -v set horizontal and vertical dimensions
## -dt saves with a timestamp
## using unix timestamp (-ts) would probably save milliseconds? 

date_stamp=$(date "+%Y.%m.%d")
dt_stamp=$(date "+%Y.%m.%d.%H.%M")


directory_path=/home/pi/recording/$date_stamp.$suffix/ 

#directory_path=/home/pi/recording/$date_stamp/ 

## Make directory for images
echo recording $directory_path$pi_name.$dt_stamp.h264

# -p will fill in missing directories
mkdir -p $directory_path 

## Add the -n flag or --nopreview to turn off preview, this might help with dropped frames
#raspistill -t 43200000 -tl 1000 --nopreview -vf -hf -q 20 -h 500 -w 500 -o $directory_path$pi_name.$year_stamp.%01d.jpg -dt
raspivid --width 1080 --height 1080 --framerate $f_rate --qp 17 --nopreview --timeout $((($n_hours*60 + $n_minutes)*60*1000)) --output $directory_path$pi_name.$dt_stamp.h264

## Use this line if the video will be too big:
#raspivid --width 500 --height 500 --framerate 1 --qp 17 --timeout $((14*60*60*1000)) --segment $((60*60*1000)) --output $directory_path$pi_name.$date_stamp-%02d.h264
