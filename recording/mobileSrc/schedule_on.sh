## Script to schedule pi's on

## Set suffix as first input, or "rogue" if there is none. 
suffix=${1:-rogue}

cp /home/pi/recording/mobileSrc/configs/default.config /home/pi/recording/current.config

## Rename suffix so that files are saved properly
bash /home/pi/recording/mobileSrc/set_suffix.sh $suffix

## Set crontab to the schedule that runs the pi
## To prevent annoying messages, this only turns it on in the evening
current_time=$(date +%H)
if [[ "$current_time" > "18" ]]; then
    crontab /home/pi/recording/mobileSrc/crontabs/base_cron.txt
else
    crontab /home/pi/recording/mobileSrc/crontabs/base_cron.txt | at 19
fi
