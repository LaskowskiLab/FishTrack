
## Monitoring script to make sure the file keeps growing

config=${1-0}
if [[ "$config" == 0 ]]; then
    config="/home/pi/recording/mobileSrc/configs/default.config"
fi
. $config

bash /home/pi/recording/mobileSrc/run_config.sh $config &
sleep 2
filename=$(ls -lrt /home/pi/recording/current.link | nawk '{print $11}')

## Every set amount of time, check that the date matches the real current date
while [[ $(date "+%H%M") -lt "1859" ]]; do
    sleep 30 # wait 60 seconds, then check 

    current_time=$(date "+%y%m%d%H%M") ## might as well prevent weird edge cases
    sleep 2       # needs time to write a frame
    file_time=$(date -r $filename "+%y%m%d%H%M") # could run into problems at y3k
    #echo $current_time $file_time
    if [[ "$current_time" -gt "$file_time" ]]; then # File is not growing! It's a zombie!!
        if [[ "$restart" == 1 ]]; then

            report="Hey, this is $HOSTNAME. My file stopped growing so I am going to try a restart to prevent dataloss. Hope to see you soon!"
            bash /home/pi/recording/mobileSrc/send_mail.sh "$report"
            sudo reboot
        else
            report="Hey, this is $HOSTNAME. My file stopped growing, hopefully that's what you want, I'm exiting now"
	    bash /home/pi/recording/mobileSrc/send_mail.sh "$report"
            exit 1;
        fi
    else
        echo "Still growing: " $file_time
    fi
	
done

wait
## On reboot, pi will check the time and restart if it's the right time, and send a message
# Schedule a message to slack a few minutes after startup (to give time for wifi): 
## Also in crontab: @reboot sleep 300 && send_mail.sh "And we're back! $HOSTNAME rebooted 5 min ago"
