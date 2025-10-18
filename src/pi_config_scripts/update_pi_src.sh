for i in $(cat $1); do

## This line is dicey if they're currently recording, but is often safe
#crontab /home/pi/recording/mobileSrc/crontabs/base_cron.txt

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    rclone copy AmazonBox:mobileSrc ~/recording/mobileSrc
    cp ~/recording/mobileSrc/mobile_aliases.txt ~/.bash_aliases
    cp ~/recording/mobileSrc/readme.txt ~/recording
    exit
EOF
echo 'End ' $i

done
