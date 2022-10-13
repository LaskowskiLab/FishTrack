#!/bin/sh

## Find the name, regardless of the pi.
pi_name=${HOSTNAME: -5}
if [[ $pi_name == "rypi" ]]; then
    pi_name='pi01'
fi

#pi_name=pi22 ## Be sure to change this for each pi
year_stamp=$(date "+%Y.%m")

## Run for 12 hours (43200000 ms), 1000 ms apart, -vf and -hf flip the video
## -h and -v set horizontal and vertical dimensions
## -dt saves with a timestamp
## using unix timestamp (-ts) would probably save milliseconds? 

day_stamp=$(date "+%Y.%m.%d")
dt_stamp=$(date "+%Y.%m.%d.%H.%M")

## Be sure to check the parent directory exists

## Use the batch.trex. tag if you want to have this batch processed
directory_path=/home/pi/recording/$day_stamp.chapter01/ 

#directory_path=/home/pi/recording/$dt_stamp/ 

## Make directory for images
echo $directory_path$pi_name.$year_stamp

# -p will fill in missing directories
mkdir -p $directory_path 

## Add the -n flag or --nopreview to turn off preview, this might help with dropped frames
#raspistill -t 43200000 -tl 1000 --nopreview -vf -hf -q 20 -h 500 -w 500 -o $directory_path$pi_name.$year_stamp.%01d.jpg -dt
raspivid --width 1600 --height 1200 --framerate 1 --qp 17 --nopreview --timeout $((1*25*60*1000)) --output $directory_path$pi_name.$dt_stamp.h264

## Use this line if the video will be too big:
#raspivid --width 500 --height 500 --framerate 1 --qp 17 --timeout $((14*60*60*1000)) --segment $((60*60*1000)) --output $directory_path$pi_name.$dt_stamp-%02d.h264