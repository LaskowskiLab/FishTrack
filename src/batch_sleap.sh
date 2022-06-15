#!/bin/bash

## Code to iterate through remote images, convert them into video, feed them into Trex, and send the parsed data back to the remote Box server
## This code will run for however many minutes specified (if specified), or for 120 minutes, or until done
# Written by Ammon Perkes for use in the Laskowski Lab
# For questions contact perkes.ammon@gmail.com


working_dir="/home/ammon/Documents/Scripts/FishTrack/working_dir" ## Directory where all temporary files will be made.
model_dir="/home/ammon/Documents/Scripts/FishTrack/sleap/models"
MINUTES=0 ## Resets MINUTES to 0, not that this is particularly important I don't think...
t_end=${1-120} ## Sets end time to 2 hours (120 minutes) if no end time is specified

crop_dict='/home/ammon/Documents/Scripts/FishTrack/src/crop_dict.22.02.25.tsv'

## the trex has to happen inside the trex environment, so I may as well just do that now
export PATH="/home/ammon/anaconda3/bin:$PATH"
source activate sleap

DEBUG=true
### Get all the pis file list (filtered to include only names with "pi" in them)
dir_list=$(rclone lsf aperkes:pivideos --dirs-only | grep pi)


## Loop through each directory in the pivideos folder 
echo $dir_list
for d in $dir_list; do
    echo $d
    subdir_list=$(rclone lsf aperkes:pivideos/$d --dirs-only | grep batch.trex)
    echo $subdir_list
    if [ -z "$subdir_list" ]; then
        echo "No batch.trex folders found, moving on"
        continue
    fi
    for s in $subdir_list; do
        echo "Working on $s"
        pi_id="${d::-1}"
        file_list=$(rclone lsf aperkes:pivideos/$d$s) ##Check that this shouldn't be $d/$s
        echo $file_list
        if [[ "$file_list" == *"crop.mp4" ]]; then
            echo "Video found, copying for sleap"
            reclone copy aperkes: include "/pivideos/"$d$s"*.crop.mp4" $working_dir
            video_path=$working_dir/
            video_path=$working_dir/${d%/}.${s%/}.crop.mp4

        elif [[ "$file_list" == *"flag."* ]]; then
            echo "Flag found, skipping"

        else #copy all data from the cloud
## Make the working file
            echo "No video yet. Here, I'll make one."
            touch $working_dir/flag.working.txt
            hostname >> $working_dir/flag.working.txt
            date >> $working_dir/flag.working.txt
            if [ "$DEBUG" = false ] ; then
                rclone copy $working_dir/flag.working.txt aperkes:pivideos/$d$s
            fi
            rclone mkdir aperkes:pivideos/$d$s"output"
            echo "Territory marked."

## Copy images from remote
            #rclone copy aperkes:pivideos/$d$s $working_dir --include "*.jpg" ## Use this if you're taking all the images

            # But in practice you're grabbing zip archives
            z="${s::-1}.zip"
            echo "grabbing aperkes:pivideos/$d$s$z"
            rclone copy aperkes:pivideos/$d$s$z $working_dir -P
            echo ".zip archive copied!"

            mkdir -p $working_dir/current

            echo "unzipping..."
            unzip -q $working_dir/$z -d $working_dir/current

## Make the video from the images
            video_path=$working_dir/${d%/}.${s%/}.mp4
            dark_path=$working_dir/${d%/}.${s%/}_all.mp4
            
## Choose whether you want full quailty or compression (or both if you're feeling randy.)
            #pi_id="${d::-1}"
            d_str="${s::8}"
            echo $pi_id.$d_str
            if [[ "$z" == *"2022.02.22"* ]] ; then
                in_dir=$working_dir/current/home/pi/recording/2022.02.22/
                in_string=$in_dir$pi_id.$d_str%*.jpg
                echo $in_string
            else
                in_dir=$working_dir/current/
                in_string=$in_dir$pi_id.$d_str%*.jpg
            fi
            #ffmpeg -f image2 -r 60 -i $working_dir/current/image%*.jpg -c:v copy $video_path
            ffmpeg -f image2 -r 60 -i $in_string -vcodec libx264 -pix_fmt yuv420p -crf 17 $dark_path -y
            ## Make a second video, this time deleting all the images before the lights are on:
            echo "Deleting dark times"
            ls $in_dir | while read file; do
                f_strip=${file%.jpg}

                [ "${f_strip: -6}" -gt 160000 ] && rm "$in_dir$file"
                [ "${f_strip: -6}" -lt 063000 ] && rm "$in_dir$file"
            done

            ffmpeg -f image2 -r 60 -i $in_string -vcodec libx264 -pix_fmt yuv420p -crf 17 $video_path -y
## Make the output directory on remote and copy video to there
            if test -f "$dark_path"; then
                echo 'Video made, copying to remote'
                rclone copy $dark_path aperkes:pivideos/$d$s -P
                echo 'removing images (DEBUG)'
                rm -r $working_dir/current
            else
                echo "Video failed. I'll just make a note here and move on..."
                date >> $working_dir/flag.working.txt
                echo "FFMPEG Failed" >> $working_dir/flag.working.txt
                if [ "$DEBUG" = false ] ; then 
                    rclone copy $working_dir/flag.working.txt aperkes:pivideos/$d$s
                    rclone moveto aperkes:pivideos/$d$s'flag.working.txt' aperkes:pivideos/$d$s'flag.check.txt'
                fi
                break
            fi
            if [ "$DEBUG" = true ] ; then
                echo "Trying to crop"
                #continue
            fi
## Crop the video based on markers
            python ~/Documents/Scripts/FishTrack/src/crop_by_tags.py -i $video_path -x $crop_dict -c $pi_id
            #cp $video_path ${video_path%.mp4}'_crop.mp4'
## If this fails, should we just run on the uncropped video or quit? 
            if [ "$DEBUG" = true ] ; then
                crop_path=${video_path%.mp4}'.crop.mp4'
                if test -f "$crop_path"; then
                    echo 'Video cropped, updating path'
                    video_path=$crop_path
                else
                    echo "Cropping Failed or something, check on this"
                fi
                echo "Continuing..."
                if test -f "$video_path"; then
                    echo 'Video made, copying to remote'
                    rclone copy $video_path aperkes:pivideos/$d$s -P
                else
                    echo 'cropping failed or something' 
                fi
                continue
            fi
            if test -f "${video_path%.mp4}'.crop.mp4'"; then
                echo 'Video cropped, updating path'
                video_path=${video_path%.mp4}'.crop.mp4'
            else
                echo "Cropping failed. I'll just make a note here and move on..."
                date >> $working_dir/flag.working.txt
                echo "CROP Failed" >> $working_dir/flag.working.txt
                rclone copy $working_dir/flag.working.txt aperkes:pivideos/$d$s
                rclone moveto aperkes:pivideos/$d$s'flag.working.txt' aperkes:pivideos/$d$s'flag.check.txt'
                break
            fi


## Feed the video into SLEAP
            # Tracking
            sleap-track -m $model_dir/finetuned352.centroid -m $model_dir/finetuned352.centered_instance --tracking.tracker flow --tracking.similarity iou $video_path 
            # Convert to h5
            sleap-convert $video_path.predictions.slp --format analysis -o $video_path.h5


## Check the trex worked
            if test -f "$working_dir/$video_path.h5"; then
                echo 'SLEAP output generated, moving on to parsing in python'
            else
                echo "SLEAP failed. I'll just make a note here and move on..."
                date >> $working_dir/flag.working.txt
                echo "SLEAP Failed" >> $working_dir/flag.working.txt
                rclone copy $working_dir/flag.working.txt aperkes:pivideos/$d$s
                rclone moveto aperkes:pivideos/$d$s'flag.working.txt' aperkes:pivideos/$d$s'flag.check.txt'
                break
            fi
## Parse the output from sleap
            python process_h5.py -i $working_dir/$video_path.h5 -x $crop_dict -c $pi_id 

## Parse the output (hopefully there are a reasonable number of fish...)
## Check that output parsed correctly
            if test -f "$working_dir/$video_path"; then
                echo 'Python parsing seems successful, time to upload'
            else
                echo "Parsing failed, could be due to Trex. I'll just make a note here and move on..."
                echo "PARSE Failed" >> $working_dir/flag.working.txt
                date >> $working_dir/flag.working.txt
                rclone copy $working_dir/flag.working.txt aperkes:pivideos/$d$s
                rclone moveto aperkes:pivideos/$d$s'flag.working.txt' aperkes:pivideos/$d$s'flag.check.txt'
                break
            fi

## Upload output to box (including changing working > finished)
            rclone mkdir aperkes:pivideos/$d$s"output"
            rclone copy $working_dir/$video_path.h5 aperkes:pivideos/$d$d"output/"
            rclone copy $working_dir/$video_path.predictions.slp aperkes:pivideos/$d$d"output/"
            rclone copy $working_dir/$video_path.csv aperkes:pivideos/$d$d"output/"
            rclone copy $working_dir/$video_path.npy aperkes:pivideos/$d$d"output/"

            date >> $working_dir/flag.working.txt
            rclone copy $working_dir/flag.working.txt aperkes:pivideos/$d$s
            rclone moveto aperkes:pivideos/$d$s'flag.working.txt' aperkes:pivideos/$d$s'flag.complete.txt'

            echo "deleting everything and moving on"
            #rm $working_dir/*
        fi 
    done
## Check if it's been running longer than the alotted time. If so quit. 
    if (( MINUTES > t_end )); then
        "Time's up, exiting."
        break
    fi
## Upload log of what you did
done

log_name=$(date '+%Y.%m.%d')'-'$(hostname)'-log.txt'
echo $log_name
#rclone copy $working_dir/log.txt aperkes:pivideos/batch_logs/log_name

## TODO:
# Update python code to prevent bad crops
## Check check check check
conda deactivate
