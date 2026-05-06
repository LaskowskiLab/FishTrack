for i in $(cat $1); do

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    echo $HOSTNAME
    echo "Log Backup:" >> ~/recording/old_log.log
    date >> ~/recording/old_log.log
    cat ~/recording/cronlog.log >> ~/recording/old_log.log
    date > ~/recording/cronlog.log
    exit
EOF
echo 'End ' $i

done
