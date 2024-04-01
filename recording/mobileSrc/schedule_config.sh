#!/bin/sh

## Schedule multiple videos.

config=${1-0}
if [[ "$config" == 0 ]]; then
    config="/home/pi/recording/mobileSrc/configs/default.config"
fi
. $config

echo "Using config:"

cat $config
echo $schedule

if [ -z "$schedule" ]; then
    echo "WARNING: You are trying to schedule a recording, but there's no schedule in your config. Please add some times in the schedule= line"
    exit 1; 
fi 


cmd="watch_mobile.sh $config"

dt=$(date "+%Y.%m.%d")
header="## Lines added using schedule_mobile.sh on $dt"
(crontab -u $(whoami) -l; echo "$header" ) | crontab -u $(whoami) -
for h_min in $schedule; do
    min="${h_min: -2}"
    hour="${h_min%$min}"
    line="$min $hour * * * $cmd >> /home/pi/recording/cronlog.log 2>&1"
    (crontab -u $(whoami) -l; echo "$line" ) | crontab -u $(whoami) -
done

wait
