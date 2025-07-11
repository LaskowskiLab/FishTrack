
model_dir='/data/sleapModels'

export PATH="/home/ammon/mambaforge/bin:$PATH"
source activate sleap

working_dir="/data/tracking/kirsten.behaviors/working_dir2"

echo This is a test

for f in $(cat /data/tracking/kirsten.behaviors/initial.2days.list2.txt); do 
    echo working on $f
    pidate=$(echo $f | cut -c -14)
    fdate=${pidate#*.}
    pi=$(echo $f | cut -c -3)
    dir_name=$fdate'.kas.ch1'
    f_path='pivideos/'$pi'/'$dir_name'/'$f
    echo $f_path
    f_name=$f
    if [ ! -f $working_dir/$f_name.h5 ]; then

        rclone copy aperkes:$f_path $working_dir -P
        #ffmpeg -i $working_dir/$f_name $working_dir/$f_name.copy.mp4 ## don't think I need this...?
## You will need to change your models here
        sleap-track -m $model_dir/kirsten.behaviors.364.scale40.centroid -m $model_dir/kirsten.behaviors.364.scale40.centered $working_dir/$f_name --peak_threshold 0.5 --tracking.tracker simplemaxtracks --tracking.max_tracking 1 --tracking.max_tracks 8 --tracking.track_window 5 --tracking.pre_cull_to_target 1 --tracking.similarity iou -o $working_dir/$f_name.predictions.slp
        sleap-convert $working_dir/$f_name.predictions.slp --format analysis -o $working_dir/$f_name.h5
    else
        echo File already exists
    fi
    rm $working_dir/$f_name
    
done
