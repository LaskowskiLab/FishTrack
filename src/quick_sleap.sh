
center_dict='/home/ammon/Documents/Scripts/FishTrack/src/center_dict.22.02.25.tsv'
model_dir='/home/ammon/Documents/Scripts/FishTrack/sleap/models'

export PATH="/home/ammon/anaconda3/bin:$PATH"
source activate sleap

source_dir="/home/ammon/Documents/Scripts/FishTrack/sleap/KirstenSLEAP/"


for f in $source_dir*.crop.mp4
do
    video_file=${f#"$source_dir"}
    pi_id="${video_file::4}"
    echo working on $video_file

    sleap-track -m $model_dir/finetuned352.centroid -m $model_dir/finetuned352.centered_instance --peak_threshold .4 --tracking.tracker flow --tracking.similarity iou $f
    sleap-convert $f.predictions.slp --format analysis -o $f.h5
    python process_h5.py -i $f.h5 -x $center_dict -c $pi_id
done
