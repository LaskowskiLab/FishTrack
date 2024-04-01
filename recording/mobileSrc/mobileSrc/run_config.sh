#!/bin/sh

## Run's video. Input argument are hours, minutes, and framerate
# e.g., run_vid.sh 10 0 2 would record for 10 hours and 0 minutes at 2 fps

config=${1-0}
echo $config
if [[ "$config" == "0" ]]; then
    config="/home/pi/recording/mobileSrc/configs/default.config"
fi

. $config
echo "Using config:"
cat $config

if [ -n $on_time ]; then
    echo "WARNING: you entered a schedule in the config, but your video will start right now"
    echo "did you mean to schedule_recording ?"
fi
## Check for some necessary variables and set them if they don't exist
if [ -z ${hours} ]; then
    echo "hours not set, using default: 0"
    hours=0
fi

if [ -z ${minutes} ]; then
    echo "minutes not set, using default: 5"
    minutes=5
fi

if [ -z ${fps} ]; then
    echo "frame rate not set, using default: 25"
    fps=25
fi

if [ -z ${width} ]; then
    echo "width not set, using default: 1080"
    width=1080
fi

if [ -z ${height} ]; then
    echo "height not set, using default: 1080"
    height=1080
fi

if [ -z ${quality} ]; then
    quality=17
fi

if [ -z ${verbose} ]; then
    verbose=0
fi

if [ -z ${format} ]; then
    format="h264"
fi

if [ -z ${suffix+x} ]; then
    if [ -f "/home/pi/recording/suffix.txt" ]; then
        suffix=$(cat ~/recording/suffix.txt)
    else
        suffix='rogue'    
    fi
else
    echo "Suffix found!"
fi
echo "suffix set to: " $suffix

if [ -z ${directory+x} ]; then
    if [ -f "/home/pi/recording/directory.txt" ]; then
        data_dir=$(cat ~/recording/directory.txt)
    else
        data_dir='/home/pi/recording/'
    fi
else
    data_dir=$directory
fi

if [ "${data_dir: -1}" != "/" ]; then
    data_dir=$data_dir"/"
fi
echo "directory set to: " $data_dir

## Find the name, regardless of the pi.
pi_name=${HOSTNAME: -5}
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

touch $directory_path$pi_name.$dt_stamp.h264
ln -fs $directory_path$pi_name.$dt_stamp.h264 /home/pi/recording/current.link

echo 0 > /home/pi/recording/current_size.txt
## Add the -n flag or --nopreview to turn off preview, this might help with dropped frames
#raspistill -t 43200000 -tl 1000 --nopreview -vf -hf -q 20 -h 500 -w 500 -o $directory_path$pi_name.$year_stamp.%01d.jpg -dt
#raspivid --width 1080 --height 1080 --framerate $fps --qp 17 --nopreview --timeout $((($hours*60 + $minutes)*60*1000)) --output $directory_path$pi_name.$dt_stamp.h264
# with new pi's this code will work: 
rpicam-vid --width $width --height $height --framerate $fps --quality $quality --nopreview --timeout $((($hours*60 + $minutes)*60*1000)) --output $directory_path$pi_name.$dt_stamp.$format -v $verbose

wait
## Use this line if the video will be too big:
#raspivid --width 500 --height 500 --framerate 1 --qp 17 --timeout $((14*60*60*1000)) --segment $((60*60*1000)) --output $directory_path$pi_name.$date_stamp-%02d.h264
