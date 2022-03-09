for i in $(cat $1); do

echo $i
ssh $i << EOF
    echo $HOSTNAME
    pkill raspistill
    nohup bash /home/pi/recording/src/run_cam.sh >> /home/pi/recording/src/cronlog.log 2>&1 &
    pgrep raspistill
    exit
EOF
echo 'End ' $i


done
