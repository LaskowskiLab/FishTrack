## Script to schedule pi's on

## Set suffix as first input, or "rogue" if there is none. 
suffix=${1:-rogue}

## Rename suffix so that files are saved properly
bash ~/recording/src/set_suffix $suffix

## Set crontab to the schedule that runs the pi
crontab ~/recording/src/crontabs/crontab-pi.txt

