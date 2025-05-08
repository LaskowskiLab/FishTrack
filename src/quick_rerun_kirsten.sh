
model_dir='/data/sleapModels'

export PATH="/home/ammon/mambaforge/bin:$PATH"
source activate sleap

working_dir="/data/tracking/kirsten.behaviors/working_dir"
out_dir="/data/tracking/kirsten.behaviors/working_dir2"

#path_list="/data/tracking/kirsten.behaviors/kirsten.behavior.paths.txt"
path_list="/data/tracking/kirsten.behaviors/all_video_paths.500mb.txt"
echo This is a test

for f in $(cat $path_list); do
    echo working on $f
    f_name=$(basename $f)
    if [ ! -f $out_dir/$f_name.h5 ]; then

        if [ ! -f $working_dir/$f_name ]; then
            #rclone copy aperkes:$f $working_dir -P
            rclone copy aperkes:/TenMinuteClips/$f $working_dir -P
        fi
        ffmpeg -i $working_dir/$f_name $working_dir/$f_name.copy.mp4 -y
## You will need to change your models here
        sleap-track -m $model_dir/kirsten.behaviors.364.scale40.centroid -m $model_dir/kirsten.behaviors.364.scale40.centered $working_dir/$f_name.copy.mp4 --peak_threshold 0.7 --tracking.tracker simplemaxtracks --tracking.max_tracking 1 --tracking.max_tracks 8 --tracking.track_window 5 --tracking.pre_cull_to_target 1 --tracking.similarity iou -o $out_dir/$f_name.predictions.slp
        sleap-convert $out_dir/$f_name.predictions.slp --format analysis -o $out_dir/$f_name.h5
    else
        echo File already exists
    fi
    
done
