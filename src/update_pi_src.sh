for i in $(cat $1); do
ssh $i << EOF
    rclone copy AmazonLab:/src/ ~/recording/src/
    exit
EOF

done
