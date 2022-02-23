#!/bin/bash

## Code to iterate through remote images, convert them into video, feed them into Trex, and send the parsed data back to the remote Box server
## This code will run for however many minutes specified (if specified), or for 120 minutes, or until done
# Written by Ammon Perkes for use in the Laskowski Lab
# For questions contact perkes.ammon@gmail.com


working_dir="/home/ammon/Documents/Scripts/FishTrack/working_dir" ## Directory where all temporary files will be made.
MINUTES=0 ## Resets MINUTES to 0, not that this is particularly important I don't think...
t_end=${1-120} ## Sets end time to 2 hours (120 minutes) if no end time is specified

## the trex has to happen inside the trex environment, so I may as well just do that now
export PATH="/home/ammon/anaconda3/bin:$PATH"
source activate tracking

### Get all the pis file list (filtered to include only names with "pi" in them)
dir_list=$(rclone lsf laskolab:pivideos --dirs-only | grep pi)


## Loop through each directory in the pivideos folder 
for d in $dir_list; do
    subdir_list=$(rclone lsf laskolab:pivideos/$d --dirs-only | grep batch.trex)
    for s in $subdir_list; do
        echo "Working on $s"
        file_list=$(rclone lsf laskolab:pivideos/$d$s) ##Check that this shouldn't be $d/$s
        #echo $file_list
        if [[ "$file_list" == *"flag."* ]]; then
            echo "Flag found, moving on"

        else #copy all images
## Make the working file
            touch $working_dir/flag.working.txt
            hostname >> $working_dir/flag.working.txt
            date >> $working_dir/flag.working.txt
            rclone copy $working_dir/flag.working.txt laskolab:pivideos/$d$s
            rclone mkdir laskolab:pivideos/$d$s"output"
            echo "Territory marked."

## Copy images from remote
            #rclone copy laskolab:pivideos/$d$s $working_dir --include "*.jpg" ## Use this if you're taking all the images

            # But in practice you're grabbing zip archives
            rclone copy laskolab:pivideos/$d$s/$s.zip $working_dir/current.zip 
            echo ".zip archive copied!"

            mkdir -p $working_dir/current

            unzip $working_dir/current.zip -d $working_dir/current

## Make the video from the images
            video_path=$working_dir/${d%/}.${s%/}.mp4
            
## Choose whether you want full quailty or compression (or both if you're feeling randy.)
            #ffmpeg -f image2 -r 60 -i $working_dir/current/image%*.jpg -c:v copy $video_path
            ffmpeg -f image2 -r 60 -i $working_dir/current/image%*.jpg -vcodec libx265 -crf 28 $video_path

## Make the output directory on remote and copy video to there
            if test -f "$video_path"; then
                echo 'Video made, copying to remote'
                rclone copy $video_path laskolab:pivideos/$d$s
            else
                echo "Video failed. I'll just make a note here and move on..."
                date >> $working_dir/flag.working.txt
                echo "FFMPEG Failed" >> $working_dir/flag.working.txt
                rclone copy $working_dir/flag.working.txt laskolab:pivideos/$d$s
                rclone moveto laskolab:pivideos/$d$s'flag.working.txt' laskolab:pivideos/$d$s'flag.check.txt'
                break
            fi
## Crop the video based on markers
            python ~/Documents/Scripts/FishTrack/crop_by_tags.py $video_path
            #cp $video_path ${video_path%.mp4}'_crop.mp4'
## If this fails, should we just run on the uncropped video or quit? 
            if test -f "${video_path%.mp4}'_crop.mp4'"; then
                echo 'Video cropped, updating path'
                video_path=${video_path%.mp4}'_crop.mp4'
            else
                echo "Cropping failed. I'll just make a note here and move on..."
                date >> $working_dir/flag.working.txt
                echo "CROP Failed" >> $working_dir/flag.working.txt
                rclone copy $working_dir/flag.working.txt laskolab:pivideos/$d$s
                rclone moveto laskolab:pivideos/$d$s'flag.working.txt' laskolab:pivideos/$d$s'flag.check.txt'
                break
            fi


## Feed the video into tgrabs then trex

## NOTE: All this is very specific to parameters and arena. Running this willy nilly will be a bit unpredictable.
            tgrabs -i $video_path -blob_size_range [.2,1] -threshold 30 -nowindow -o $video_path'.pv'

            trex -i $video_path.pv -track_intensity_range [50,150] -track_max_speed 30 -track_max_individuals 4 -track_max_reassign_time 0.02 -auto_quit -nowindow -output_dir $working_dir/raw
## Check the trex worked
            if test -f "$working_dir/raw/data/*.npz"; then
                echo 'Trex output generated, moving on to parsing in python'
            else
                echo "Trex or Tgrabs failed. I'll just make a note here and move on..."
                date >> $working_dir/flag.working.txt
                echo "TREX Failed" >> $working_dir/flag.working.txt
                rclone copy $working_dir/flag.working.txt laskolab:pivideos/$d$s
                rclone moveto laskolab:pivideos/$d$s'flag.working.txt' laskolab:pivideos/$d$s'flag.check.txt'
                break
            fi
## Correct the IDs (to make sure a consistent top to bottom naming convention)
            python correct-IDs.py $working_dir/raw/data
## Parse the output (hopefully there are a reasonable number of fish...)
            for f in $working_dir/raw/data/*.npz; do
                infile=$f
                outfile=${f%.npz}'.csv'
                python parse-trex.py -i $infile -o $outfile -m
                rclone copy $outfile laskolab:pivideos/$d$d"output/"
            done
## Check that output parsed correctly
            if test -f "$outfile"; then
                echo 'Python parsing seems successful, time to upload'
            else
                echo "Parsing failed, could be due to Trex. I'll just make a note here and move on..."
                echo "PARSE Failed" >> $working_dir/flag.working.txt
                date >> $working_dir/flag.working.txt
                rclone copy $working_dir/flag.working.txt laskolab:pivideos/$d$s
                rclone moveto laskolab:pivideos/$d$s'flag.working.txt' laskolab:pivideos/$d$s'flag.check.txt'
                break
            fi

## Upload output to box (including changing working > finished)
            rclone mkdir laskolab:pivideos/$d$s"output/raw"
            rclone copy $working_dir/raw laskolab:pivideos/$d$s"output/raw"

            date >> $working_dir/flag.working.txt
            rclone copy $working_dir/flag.working.txt laskolab:pivideos/$d$s
            rclone moveto laskolab:pivideos/$d$s'flag.working.txt' laskolab:pivideos/$d$s'flag.complete.txt'

            echo "deleting everything and moving on"
            rm $working_dir/raw/data/* ##I know rm -r would do this
            rmdir $working_dir/raw/data #But putting a recursive delete inside a bash script seems like a terrible idea
            rm $working_dir/raw/*       #This will delete everything fairly carefully
            rmdir $working_dir/raw
            rm $working_dir/*
        fi 
    done
## Check if it's been running longer than the alotted time. If so quit. 
    if (( MINUTES > t_end )); then
        "Time's up, exiting."
        break
    fi
## Upload log of what you did
    log_name=$(date '+%Y.%m.%d')'-'$(hostname)'-log.txt'
    rclone copy $working_dir/log.txt laskolab:pivideos/batch_logs/log_name
done

## TODO:
# Update python code to prevent bad crops
## Check check check check
source deactivate
