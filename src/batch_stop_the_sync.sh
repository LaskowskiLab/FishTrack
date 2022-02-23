for i in $(cat $1); do
ssh $i << EOF
    pkill rclone
    exit
EOF

done
