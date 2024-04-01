
. /home/pi/recording/current.config

if [ -z ${project_suffix+x} ]; then
    if [ -f "/home/pi/recording/suffix.txt" ]; then
        project_suffix=$(cat /home/pi/recording/suffix.txt)
    else
        project_suffix='rogue'    
    fi
else
    echo "Suffix found!"
fi
suffix=$project_suffix

current_time=$(date "+%H%M")
restart_count=$(cat ~/recording/restart_count.txt)
if [[ "$suffix" != "PAUSED" ]]; then
    if [[ "$restart_count" -lt 2 ]] || [[ $restart == 0 ]]; then
        bash /home/pi/recording/mobileSrc/send_mail.sh "Hi, $HOSTNAME here: I just restarted, I'm going to just wait for you to check me"
    elif [[ "$current_time" -gt "0600" ]] && [[ "$current_time" -lt "2000" ]]; then
        bash /home/pi/recording/mobileSrc/watch_mobile.sh /home/pi/recording/current.config
    fi
fi
