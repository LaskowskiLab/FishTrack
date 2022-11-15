for i in $(cat $1); do
ssh $i << EOF
    pkill raspivid
    rclone copy AmazonBox:/src/ ~/recording/src/
    crontab ~/recording/src/crontab-kirsten.txt
    exit
EOF

done
