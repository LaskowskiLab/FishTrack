for i in $(cat $1); do

echo $i

ssh -o StrictHostKeyChecking=no $i << EOF
    rclone copy AmazonBox:/src/ ~/recording/src/
    cp ~/recording/src/aliases.txt ~/.bash_aliases
    bash ~/recording/src/schedule_off.sh
    exit
EOF

echo 'End ' $i

done
