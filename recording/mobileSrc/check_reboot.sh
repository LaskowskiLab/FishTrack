
suffix=$(cat ~/recording/suffix.txt)
current_time=$(date "+%H%M")
restart_count=$(cat ~/recording/restart_count.txt)
echo $restart_count
if [[ "$suffix" != "PAUSED" ]]; then
    if [ "$restart_count" -gt 2 ]; then
	sleep 120 ## Need to wait for wifi to kick in 
        bash /home/pi/recording/mobileSrc/send_mail.sh "Hi, $HOSTNAME here: I'm at 2 restarts already, I'm going to just wait for you to check me"
    elif [ "$current_time" -gt "0600" ] && [ "$current_time" -lt "1900" ]; then
        bash /home/pi/recording/mobileSrc/watch_mobile.sh /home/pi/recording/mobileSrc/current.config 
    fi
fi
