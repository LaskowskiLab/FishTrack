for i in $(cat $1); do

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    echo $HOSTNAME
    rclone copy AmazonBox:/src/ ~/recording/src/
    crontab ~/recording/src/crontabs/crontab-pi.txt
    exit
EOF
echo 'End ' $i

done
