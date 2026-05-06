
## This will turn on the list of pi's right now, using whatever the current.config is
for i in $(cat $1); do

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    echo 0 > /home/pi/recording/restart_count.txt
    nohup bash ~/recording/mobileSrc/watch_mobile.sh ~/recording/current.config > /home/pi/recording/cronlog.log 2>&1 </dev/null &
    exit
EOF
echo 'End ' $i
done
