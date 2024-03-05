## Script to schedule pi's on

## Set suffix as first input, or "rogue" if there is none. 
suffix=${1:-rogue}

## Rename suffix so that files are saved properly
bash ~/recording/src/set_suffix.sh $suffix

## Set crontab to the schedule that runs the pi
## To prevent annoying messages, this only turns it on in the evening
current_time=$(date +%H:%M)
if [[ "$current_time" > "18:15" ]]; then
    crontab ~/recording/src/crontabs/crontab-pi.txt
else
    crontab ~/recording/src/crontabs/crontab-pi.txt | at 18:15
fi
