#!/bin/bash

## Code to iterate through remote images, convert them into video, feed them into Trex, and send the parsed data back to the remote Box server
## This code will run for however many minutes specified (if specified), or for 120 minutes, or until done
# Written by Ammon Perkes for use in the Laskowski Lab
# For questions contact perkes.ammon@gmail.com


working_dir="/home/ammon/Documents/Scripts/FishTrack/working_dir" ## Directory where all temporary files will be made.
model_dir="/home/ammon/Documents/Scripts/FishTrack/sleap/models"
MINUTES=0 ## Resets MINUTES to 0, not that this is particularly important I don't think...
t_end=${2-120} ## Sets end time to 2 hours (120 minutes) if no end time is specified. Use # for infinite running

crop_dict='/home/ammon/Documents/Scripts/FishTrack/src/current_crop.tsv'
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
    n="${d##pi}"  # Grab number off directory
    n="${n##0}"   # Drop leading 0 if necessary. 
    n="${n%/}"    # Drop trailing /
    echo $n
    #if [ "$n" -gt "12" ]; then 
    #    echo "only doing first 12, moving on"
    #    continue
    #fi
    echo "running $d"
    subdir_list=$(rclone lsf aperkes:pivideos/$d --dirs-only | grep 20)
    echo $subdir_list
    if [ -z "$subdir_list" ]; then
        echo "No recent folders found, moving on"
        continue
    fi
    for s in $subdir_list; do

        y="${s%%.*}" 
        echo $y
        if [ "$y" == '2022' ] ; then
            echo "Skipping 2022: " $s
            continue
        fi
        echo "Working on $s"
        echo "Working on $s" > $working_dir/flag.working.txt
        pi_id="${d::-1}"
        file_list=$(rclone lsf aperkes:pivideos/$d$s) ##Check that this shouldn't be $d/$s
        echo $file_list
        if [[ "$file_list" == *"flag.complete"* ]]; then
            echo "Complete flag found, not entirely sure what that means, but moving on"
            continue
        elif [[ "$file_list" == *"flag.check"* ]]; then
            #echo "Check flag found, going to do it"
            echo "Check flag found, skipping for now"
            continue
            rclone moveto aperkes:pivideos/$d$s'flag.check.txt' aperkes:pivideos/$d$s'flag.working.txt'
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

## This will copy all h264, so that's good, but I need to grab multiple
            rclone copy aperkes: $working_dir --include "/pivideos/"$d$s"*.h264" -P
            h264_list=$(ls $working_dir/pivideos/"$d$s"*.h264)
            for h in $h264_list; do
                #h264_path=$working_dir/pivideos/"$d$s"$h
                #video_path=$working_dir/${h%h264}mp4

                h264_path=$h
                h264_name="$(basename $h)"
                video_path=$working_dir/${h264_name%h264}mp4

                echo "$h264_path"
                echo $video_path

                ffmpeg -i $h264_path -c copy -crf 13 $video_path -y
                rm $h264_path ## delete downloaded h264
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
            done
        else 
            echo "No video yet. skipping for now"
            continue
        
        fi 
## At this point, I should have either copied or made a video, on to processing:
## Feed the video into SLEAP
        # Tracking
        echo "Skipping sleap for now"
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
