for i in $(cat $1); do

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    rclone copy AmazonBox:/src/ ~/recording/src/
    crontab ~/recording/src/crontabs/crontab-pause.txt
    exit
EOF
echo 'End ' $i

done
