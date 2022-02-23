for i in $(cat $1); do
ssh $i << EOF
    rclone copy AmazonBox:/src/ ~/recording/src/
    crontab ~/recording/src/crontab-pi.txt
    exit
EOF

done
