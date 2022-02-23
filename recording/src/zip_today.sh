#!/bin/sh

## The start of this replicates a lot of  run_cam.sh to get the correct file names
## It then combines all the images into a .zip and drops it in recording

## Find the name, regardless of the pi.
pi_name=${HOSTNAME: -4}
if [[ $pi_name == "rypi" ]]; then
    pi_name='pi01'
fi

year_stamp=$(date "+%Y.%m")
date_stamp=$(date "+%Y.%m.%d")

## Use the batch.trex. tag if you want to have this batch processed
directory_path=/home/pi/recording/$date_stamp.batch.trex/ 

#directory_path=/home/pi/recording/$date_stamp/ 

# Again, use the batch.trex. tag if you want this to be grabbed during batch processing
cd $directory_path
zip ../$date_stamp.batch.trex.zip *
