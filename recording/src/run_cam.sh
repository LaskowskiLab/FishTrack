#!/bin/sh

## Find the name, regardless of the pi.
pi_name=${HOSTNAME: -4}
if [[ $pi_name == "rypi" ]]; then
    pi_name='pi01'
fi

#pi_name=pi22 ## Be sure to change this for each pi
year_stamp=$(date "+%Y.%m")

## Run for 12 hours (43200000 ms), 1000 ms apart, -vf and -hf flip the video
## -h and -v set horizontal and vertical dimensions
## -dt saves with a timestamp
## using unix timestamp (-ts) would probably save milliseconds? 

date_stamp=$(date "+%Y.%m.%d")

## Be sure to check the parent directory exists

## Use the batch.trex. tag if you want to have this batch processed
directory_path=/home/pi/recording/$date_stamp.batch.trex/ 

#directory_path=/home/pi/recording/$date_stamp/ 

## Make directory for images
echo $directory_path$pi_name.$year_stamp

# -p will fill in missing directories
mkdir -p $directory_path 

## Add the -n flag or --nopreview to turn off preview, this might help with dropped frames
raspistill -t 43200000 -tl 1000 -bm --nopreview -vf -hf -q 20 -h 500 -w 500 -o $directory_path$pi_name.$year_stamp.%01d.jpg -dt
