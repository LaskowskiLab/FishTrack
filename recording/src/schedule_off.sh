## Script to schedule pi's on

## Set suffix as first input, or "rogue" if there is none. 
suffix=${1:-PAUSED}

## This shouldn't matter, but is a backup against people forgetting
bash ~/recording/src/set_suffix.sh $suffix

## Set crontab to the schedule that doesn't record 
crontab ~/recording/src/crontabs/crontab-pause.txt

