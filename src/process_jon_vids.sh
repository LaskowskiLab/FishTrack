#! /bin/bash

## Code that will
# 1. Iterate through Jon's remote images (JON01)
# 2. Download all h264, one by one
# 3. Save one frame from each one (not the first frame, too dark)
# 4. Store the image from the first video of each day in one directory
# 5. Store all imgaes in a second directory 


fishtrack_path="/home/ammon/Documents/Scripts/FishTrack/"
working_dir=$fishtrack_path"working_dir/"

# This hasn't been implemented yet
#t_end=${2-#} ## Sets end time to be infinite by default, but you can specify

v1_dir=$working_dir"day1_imgs/"
vAll_dir=$working_dir"all_imgs/"

if test -d "$v1_dir"; then
    echo "Let's do this!"
else
    mkdir $working_dir
    mkdir $v1_dir
    mkdir $vAll_dir
    echo "Let's do this!"
fi
# uncomment these lines if you need a specific conda environment
#export PATH="/home/ammon/anaconda3/bin:$PATH"
#source activate sleap

## NOTE: remember to change aperkes if you're running on a different account
dir_list=$(rclone lsf aperkes:pivideos --dirs-only | grep JON)

echo $dir_list              ## this is your list of directories on box

for d in $dir_list; do      ## Loop through directories
    if [ $# -gt 0 ] ; then  # this allows you to optionally pick 1 directory
        if [ "$1" == 0 ]; then
            echo "Doing all directories..."
        elif [ "$d" != "$1/" ]; then
            echo "Directory specified as $1, skipping $d"
            continue
        fi
    fi
    echo "running $d"
    subdir_list=$(rclone lsf aperkes:pivideos/$d --dirs-only | grep chapter01 )
    for s in $subdir_list; do
        echo "Working on $s"
        echo "Working on $s" > $working_dir/flag.working.txt

        file_list=$(rclone lsf aperkes:pivideos/$d$s) ##Check that this shouldn't be $d/$s
        echo $file_list
        if [[ "$file_list" == *".jpg"* ]]; then
            echo "this one already has a jpg, can skip today"
            #echo "but I'm doing it anyway."
            continue
        fi
        if [[ "$file_list" == *".h264"* ]]; then
            echo "at least one h264 found, copying file(s)"
            rclone copy aperkes: $working_dir --include "/pivideos/"$d$s"*.h264" -P
            h264_list=$(ls $working_dir"pivideos/$d$s"*.h264)
            COUNT=0
            echo $h264_list
            for h in $h264_list; do
                h264_path=$h
                h264_name="$(basename $h)" ## this strips the path
                jpg_path=$working_dir${h264_name%h264}jpg

                echo $h264_path
                echo $jpg_path

                ffmpeg -i $h264_path -ss 5 -frames:v 1 -q:v 2 $jpg_path -y
                rm $h264_path ## delete downloaded h264
                if test -f "$jpg_path"; then
                    echo 'JPEG made, copying to local and remote'
                    if [ "$COUNT" == '0' ]; then
                        cp $jpg_path $v1_dir
                    fi
                    cp $jpg_path $vAll_dir
                    rclone move $jpg_path aperkes:pivideos/$d$s -P
                else
                    echo "Img failed. I'll just make a note here and move on..."
                    date >> $working_dir/flag.working.txt
                    echo "FFMPEG Failed" >> $working_dir/flag.working.txt
                    rclone copyto $working_dir/flag.working.txt aperkes:pivideos/$d$s'flag.check.txt'
                let COUNT++
                fi
            done
        rm -rf $working_dir/pivideos/"$d$s" ## Remove the whole directory 
        fi
    done
done



