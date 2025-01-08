
## Monitoring script to make sure the file keeps growing

config=${1-0}
if [[ "$config" == 0 ]]; then
    config="/home/pi/recording/mobileSrc/configs/default.config"
fi
. $config


bash /home/pi/recording/mobileSrc/run_config.sh $config &

sleep 30 ## make sure to give it enough time to update the link
filename=$(ls -lrt /home/pi/recording/current.link | nawk '{print $11}')

if [ -z ${hours} ]; then
    hours=0
fi

if [ -z ${minutes} ]; then
    minutes=5
fi

if [ -z ${restart} ]; then
    restart=0
fi

## Every set amount of time, check that the date matches the real current date
duration=$((hours*60 + minutes - 1))
#start_time=$(date "+%H")*60 + $(date "+%M")
start_time=$(date "+%H%M")
end_time=$(date -d "$duration minutes" +"%y%m%dH%M")
#echo $start_time
## Double brackets causes base errors for strings starting with 0. 
while [ $(date "+%H%M") -lt "1859" ] && [ $(date "+y%m%d%H%M") -lt "$end_time" ]; do
    sleep 70 # wait 60 seconds, then check 

    current_time=$(date "+%y%m%d%H%M") ## might as well prevent weird edge cases
    sleep 2       # needs time to write a frame
    file_time=$(date -r $filename "+%y%m%d%H%M") # could run into problems at y3k
    #echo $current_time $file_time
    if [ "$current_time" -gt "$file_time" ]; then # File is not growing! It's a zombie!!
        if [ "$restart" == 1 ] && [ "$restart_count" -lt "10" ] ; then

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
