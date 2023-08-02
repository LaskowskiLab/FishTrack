for i in $(cat $1); do
ssh -o "StrictHostKeyChecking=no" $i << EOF
    rclone copy --exclude suffix.txt AmazonBox:/src/ ~/recording/src/
    cp ~/recording/src/aliases.txt ~/.bash_aliases
    exit
EOF

done
