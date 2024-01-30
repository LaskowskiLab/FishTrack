#!/bin/sh

#########INPUT ARGUMENTS###############################################################
## Commands below are read as INPUT-VALUE, so 1-0 means the first input will equal ZERO
#######################################################################################

#First input: Hours. Edit the second number for how many hours you are recording.
n_hours=${1-0}

#Second input: Minutes. Edit the second number for how long your trial is.
n_minutes=${2-2}

#Third input: FPS. Edit the second number for your FPS.
f_rate=${3-20}

n_time=$(($n_hours*60 + $n_minutes))

## Find the name, regardless of the pi.
pi_name=${HOSTNAME: -5}
if [[ $pi_name == "rypi" ]]; then
    pi_name='Jon01'
fi


#################################################################
#########TIME STAMPS FOR FILE MANAGEMENT#########################
#################################################################
year_stamp=$(date "+%Y.%m")
day_stamp=$(date "+%Y.%m.%d")
dt_stamp=$(date "+%Y.%m.%d.%H.%M")



################################################################
###################CREATES DIRECTORY ON PI######################
################################################################
directory_path=/home/pi/recording/$day_stamp/ 
mkdir -p $directory_path 


#########################################################
#########ECHO TRIAL START AND END TIME###################
#########################################################

echo "Start at "$(date +"%H:%M:%S")
dt_trial=$(date -d "$TIME $n_time min" +"%H:%M:%S")
echo "Trial ends at: "$dt_trial

########################################################
##############CAMERA COMMAND############################
########################################################

#if you want to change how long the video is running for, change INPUT arguments in the first CHUNK.
rpicam-vid --width 1600 --height 1200 --framerate $f_rate --quality 17 --nopreview --timeout $((($n_hours*60 + $n_minutes)*60*1000)) --output $directory_path$pi_name.$dt_stamp.h264 -v 0


