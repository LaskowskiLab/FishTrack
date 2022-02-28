
date_stamp=$(date "+%Y.%m.%d")

remote_dir="/home/pi/recording/$date_stamp.batch.trex"
local_dir="/home/ammon/Documents/Scripts/FishTrack/recording/now"

## Remove old images
rm $local_dir/*.jpg

for i in $(cat $1); do
    scp $i:$remote_dir/$(ssh $i "ls $remote_dir | tail -2 | head -1") $local_dir

done

rclone sync /home/ammon/Documents/Scripts/FishTrack/recording/now aperkes:/'Laskowski Lab'/Ammon/now -P
