for i in $(cat $1); do
ssh -o "StrictHostKeyChecking=no" $i << EOF
    rclone copy AmazonBox:/src/ ~/recording/src/
    cp ~/recording/src/aliases.txt ~/.bash_aliases
    exit
EOF

done
