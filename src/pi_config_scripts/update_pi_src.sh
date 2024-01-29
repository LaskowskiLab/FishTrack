for i in $(cat $1); do
ssh -o "StrictHostKeyChecking=no" $i << EOF
    hostname 
    rclone copy AmazonBox:/src/ ~/recording/src/
    cp ~/recording/src/aliases.txt ~/.bash_aliases
    echo check_suffix
    echo rpicam-hello -t 500
    exit
EOF

done
