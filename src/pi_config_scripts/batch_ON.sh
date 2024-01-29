for i in $(cat $1); do

echo $i

ssh -o StrictHostKeyChecking=no $i << EOF
    rclone copy AmazonBox:/src/ ~/recording/src/
    cp ~/recording/src/aliases.txt ~/.bash_aliases
    exit
EOF

## This has to be a separate line so that it can use command arguments here
ssh -o "StrictHostKeyChecking=no" $i "bash /home/pi/recording/src/schedule_on.sh ${2:-rogue}"

echo 'End ' $i

done
