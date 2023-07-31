for i in $(cat $1); do

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    rclone copy AmazonBox:/src/ ~/recording/src/
    copy ~/recording/src/aliases.txt ~/.bash_aliases
    . ~/.bash_aliases
    schedule_ON ${2:-rogue}
    exit
EOF
echo 'End ' $i

done
