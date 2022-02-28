#!/bin/bash

## Get current time in seconds
current_time=$(date "+%H:%M:%S")
secs0=$(date -d "1970-01-01 $current_time" +%s)

## Calculate time in seconds that each image was saved
n_files=$(ls /home/ammon/Documents/Scripts/FishTrack/recording/now | wc -l)
n_servers=$(cat $1 | wc -l)

echo $current_time
if [ "$n_files" -lt "$n_servers" ]; then
    echo 'Missing files!'
    bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "ALERT: Images missing in last upload"
else
    echo "Images checked, all present"
fi

for i in $(ls /home/ammon/Documents/Scripts/FishTrack/recording/now); do
    ds=${i: -10}
    hour=${ds:0:2}
    min=${ds:2:2}
    sec=${ds:4:2}
    secs=$(date -d "1970-01-01 $hour:$min:$sec" +%s)

    diff="$(($secs - $secs0))"
    diff=${diff#-}
    if [ "$diff" -gt "1200" ]; then
        echo "ALERT: $i too old"
        bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "ALERT: $i is too old, check it!"
    else
        echo "$i - ok"
    fi
done
echo 'Times checked, all done. Have a nice day'

bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "Test: Everything appears to be working"
