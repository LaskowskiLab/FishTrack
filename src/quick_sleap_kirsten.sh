
model_dir='/data/sleapModels'

export PATH="/home/ammon/mambaforge/bin:$PATH"
source activate sleap

working_dir="/data/tracking/kirsten.behaviors/working_dir"

echo This is a test

for f in $(cat /data/tracking/kirsten.behaviors/kirsten.behavior.paths.txt); do 
    echo working on $f
    f_name=$(basename $f)
    if [ ! -f $working_dir/$f_name.h5 ]; then

        #rclone copy aperkes:$f $working_dir -P
        ffmpeg -i $working_dir/$f_name $working_dir/$f_name.copy.mp4
## You will need to change your models here
        sleap-track -m $model_dir/kirsten.take2.centroid.20 -m $model_dir/kirsten.take2.centered_instance.20 $working_dir/$f_name.copy.mp4 --peak_threshold 0.7 --tracking.tracker simplemaxtracks --tracking.max_tracking 1 --tracking.max_tracks 8 --tracking.track_window 5 --tracking.pre_cull_to_target 1 --tracking.similarity iou -o $working_dir/$f_name.predictions.slp
        sleap-convert $working_dir/$f_name.predictions.slp --format analysis -o $working_dir/$f_name.h5
    else
        echo File already exists
    fi
    
done
