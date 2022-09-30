#!/bin/bash

## Code to iterate through remote images, convert them into video, feed them into Trex, and send the parsed data back to the remote Box server
## This code will run for however many minutes specified (if specified), or for 120 minutes, or until done
# Written by Ammon Perkes for use in the Laskowski Lab
# For questions contact perkes.ammon@gmail.com


working_dir="/home/ammon/Documents/Scripts/FishTrack/working_dir" ## Directory where all temporary files will be made.
model_dir="/home/ammon/Documents/Scripts/FishTrack/sleap/models"
MINUTES=0 ## Resets MINUTES to 0, not that this is particularly important I don't think...
t_end=${1-120} ## Sets end time to 2 hours (120 minutes) if no end time is specified. Use # for infinite running

crop_dict='/home/ammon/Documents/Scripts/FishTrack/src/crop_dict.22.09.01.tsv'
center_dict='/home/ammon/Documents/Scripts/FishTrack/src/center_dict.22.02.25.tsv'

## the trex has to happen inside the trex environment, so I may as well just do that now
export PATH="/home/ammon/anaconda3/bin:$PATH"
source activate sleap

DEBUG=false
### Get all the pis file list (filtered to include only names with "pi" in them)
dir_list=$(rclone lsf aperkes:pivideos --dirs-only | grep pi)


## Loop through each directory in the pivideos folder 
echo $dir_list
for d in $dir_list; do
    if [ $# -gt 0 ] ; then
        if [ "$d" != "$1/" ]; then
        echo "Directory specified, skipping $d"
            continue 
        fi
    fi
    echo "running $d"
    subdir_list=$(rclone lsf aperkes:pivideos/$d --dirs-only | grep batch.trex)
    echo $subdir_list
    if [ -z "$subdir_list" ]; then
        echo "No batch.trex folders found, moving on"
        continue
    fi
    for s in $subdir_list; do
        echo "Working on $s"
        echo "Working on $s" > $working_dir/flag.working.txt
        pi_id="${d::-1}"
        file_list=$(rclone lsf aperkes:pivideos/$d$s) ##Check that this shouldn't be $d/$s
        echo $file_list
        if [[ "$file_list" == *"flag.complete"* ]]; then
            echo "Complete flag found, not entirely sure what that means, but moving on"
            continue
        elif [[ "$file_list" == *"flag.check"* ]]; then
            echo "Check flag found, going to do it"
            rclone moveto aperkes:pivideos/$d$s'flag.check.txt' aperkes:pivideos/$d$s'flag.working.txt'
            #continue
        fi

        if [[ "$file_list" == *"crop.mp4"* ]]; then
            echo "cropped mp4 found, skipping for now"
            continue
            rclone copy aperkes: $working_dir --include "/pivideos/"$d$s"*.crop.mp4"
            video_path=$working_dir/${d%/}.${s%/}.crop.mp4
            #video_path=$working_dir/pivideos/"$d$s"${d%/}.${s%/}.crop.mp4
        elif [[ "$file_list" == *"trex.mp4"* ]]; then
            echo "found an uncropped mp4. What do I do?" 
            echo " (Add some crop code here) "
        elif [[ "$file_list" == *".h264"* ]]; then ## Eventually I should streamline this, it's a lot of copy-pasta from below
            echo "h264 found, copying for conversion to .mp4"
            rclone copy aperkes: $working_dir --include "/pivideos/"$d$s"*.h264" -P
            h264_path=$working_dir/pivideos/"$d$s"${d%/}.${s%.batch.trex/}.h264
            video_path=$working_dir/${d%/}.${s%/}.mp4

            echo "$h264_path"
            ffmpeg -i $h264_path -crf 13 $video_path -y
            rm $h264_path
            if test -f "$video_path"; then
                echo 'Video made, copying to remote'
                rclone copy $video_path aperkes:pivideos/$d$s -P
            else
                echo "Video failed. I'll just make a note here and move on..."
                date >> $working_dir/flag.working.txt
                echo "FFMPEG Failed" >> $working_dir/flag.working.txt
                if [ "$DEBUG" = false ] ; then 
                    rclone copy $working_dir/flag.working.txt aperkes:pivideos/$d$s
                    rclone moveto aperkes:pivideos/$d$s'flag.working.txt' aperkes:pivideos/$d$s'flag.check.txt'
                fi
                continue
            fi
            if [ "$DEBUG" = true ] ; then
                echo "DEBUG: Moving on"
                continue
            fi
## Crop the video based on markers
## Trustratingly, I Haven't been able to get aruco tags into cv2 without breaking the sleap environment. 
            echo 'Environment shuffling so that my crop code works'
            conda deactivate
            conda activate tracking
            echo $video_path
            python ~/Documents/Scripts/FishTrack/src/crop_by_tags.py -i $video_path -x $crop_dict -c $pi_id
            conda deactivate
            conda activate sleap
            #cp $video_path ${video_path%.mp4}'_crop.mp4'
## If this fails, should we just run on the uncropped video or quit? 
            crop_path=${video_path%.mp4}'.crop.mp4'
            if [ "$DEBUG" = true ] ; then
                if test -f "$crop_path"; then
                    echo 'Video cropped, updating path and deleting video'
                    rm $video_path
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
            if test -f "$crop_path"; then
                echo 'Video cropped, updating path,copying to remote'
                rm $video_path
                video_path=$crop_path
                rclone move $video_path aperkes:pivideos/$d$s -P
            else
                echo "Cropping failed. I'll just make a note here and move on..."
                rm $video_path
                date >> $working_dir/flag.working.txt
                echo "CROP Failed" >> $working_dir/flag.working.txt
                rclone copy $working_dir/flag.working.txt aperkes:pivideos/$d$s
                rclone moveto aperkes:pivideos/$d$s'flag.working.txt' aperkes:pivideos/$d$s'flag.check.txt'
                continue
            fi

        else #copy all data from the cloud
## Make the working file
            echo "No video yet. skipping for now"
            continue
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
                echo "DEBUG: Moving on"
                continue
            fi
## Crop the video based on markers
## Trustratingly, I Haven't been able to get aruco tags into cv2 without breaking the sleap environment. 
            echo 'Environment shuffling so that my crop code works'
            conda deactivate
            conda activate tracking
            python ~/Documents/Scripts/FishTrack/src/crop_by_tags.py -i $video_path -x $crop_dict -c $pi_id
            conda deactivate
            conda activate sleap
            #cp $video_path ${video_path%.mp4}'_crop.mp4'
## If this fails, should we just run on the uncropped video or quit? 
            crop_path=${video_path%.mp4}'.crop.mp4'
            if [ "$DEBUG" = true ] ; then
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
            if test -f "$crop_path"; then
                echo 'Video cropped, updating path,copying to remote'
                rm $video_path
                video_path=$crop_path
                rclone copy $video_path aperkes:pivideos/$d$s -P
            else
                echo "Cropping failed. I'll just make a note here and move on..."
                date >> $working_dir/flag.working.txt
                echo "CROP Failed" >> $working_dir/flag.working.txt
                rclone copy $working_dir/flag.working.txt aperkes:pivideos/$d$s
                rclone moveto aperkes:pivideos/$d$s'flag.working.txt' aperkes:pivideos/$d$s'flag.check.txt'
                break
            fi


        fi 
## At this point, I should have either copied or made a video, on to processing:
## Feed the video into SLEAP
        # Tracking
        echo "Skipping sleap for now, need to retrain for babies"
        rm $video_path
        continue
        if test -f "$video_path.h5"; then
            echo "SLEAP Already ran, hope you like what it did"
        else
            echo "Tracking"
            sleap-track -m $model_dir/finetuned352.centroid -m $model_dir/finetuned352.centered_instance --peak_threshold 0.4 --tracking.tracker flow --tracking.similarity iou $video_path 
            # Convert to h5
            echo "Converting to h5"
            sleap-convert $video_path.predictions.slp --format analysis -o $video_path.h5
        fi
## Check that SLEAP worked
        if test -f "$video_path.h5"; then
            echo 'SLEAP output generated, uploading to Box and parsing in python'
            rclone copy $video_path.predictions.slp aperkes:pivideos/$d$s"output"
            rclone copy $video_path.h5 aperkes:pivideos/$d$s"output"
        else
            echo "SLEAP failed. I'll just make a note here and move on..."
            date >> $working_dir/flag.working.txt
            echo "SLEAP Failed" >> $working_dir/flag.working.txt
            rclone copy $working_dir/flag.working.txt aperkes:pivideos/$d$s
            rclone moveto aperkes:pivideos/$d$s'flag.working.txt' aperkes:pivideos/$d$s'flag.check.txt'
            continue
        fi
## Parse the output from sleap
        python process_h5.py -i $video_path.h5 -x $center_dict -c $pi_id 

## Parse the output (hopefully there are a reasonable number of fish...)
## Check that output parsed correctly
        if test -f "$video_path.csv"; then
            echo 'Python parsing seems successful, time to upload'
            rclone mkdir aperkes:pivideos/$d$s"output"
            rclone copy $video_path.csv aperkes:pivideos/$d$s"output"
            rclone copy $video_path.npy aperkes:pivideos/$d$s"output"
            rclone copy $video_path.png aperkes:pivideos/$d$s"output"
            rclone copy $video_path.txt aperkes:pivideos/$d$s"output"
            date >> $working_dir/flag.working.txt
            rclone copy $working_dir/flag.working.txt aperkes:pivideos/$d$s
            rclone moveto aperkes:pivideos/$d$s'flag.working.txt' aperkes:pivideos/$d$s'flag.complete.txt'
        else
            echo "Parsing failed, probably the .slp has too many tracks. I'll just make a note here and move on..."
            echo "PARSE Failed" >> $working_dir/flag.working.txt
            date >> $working_dir/flag.working.txt
            rclone copy $working_dir/flag.working.txt aperkes:pivideos/$d$s
            rclone moveto aperkes:pivideos/$d$s'flag.working.txt' aperkes:pivideos/$d$s'flag.check.txt'
            break
        fi

## Upload output to box (including changing working > finished)


        echo "not deleting anything and moving on"
        #rm $working_dir/*
## Check if it's been running longer than the alotted time. If so quit. 
    echo 'Time (minutes):'
    echo $MINUTES
    if (( MINUTES > $t_end )); then
        "Time's up, exiting."
        break
    fi
    done
done

## Upload log of what you did, Need to fix this.
#log_name=$(date '+%Y.%m.%d')'-'$(hostname)'-log.txt'
#echo $log_name
#rclone copy $working_dir/log.txt aperkes:pivideos/batch_logs/$log_name

## TODO:
# Update python code to prevent bad crops
## Check check check check
conda deactivate
