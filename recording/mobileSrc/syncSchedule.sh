
recordingDir="/home/pi/recording/"
srcDir=$recordingDir"mobileSrc/"
rclone copy AmazonBox:piManager/ScheduleTest.csv $srcDir
pi_name=${HOSTNAME: -4}
#piLine="$(cat $srcDir"ScheduleTest.csv" | grep "pi24")"
piLine="$(cat $srcDir"ScheduleTest.csv" | grep $pi_name)"
echo $piLine
## split and strip pi line to get pi,suffix,config

pi=${piLine%%,*}
suffix=${piLine#*,}
config=${suffix#*,}

suffix=${suffix%%,*}

config=${config%%,*}

if [ "${config,,}" = "on" ]; then
    echo "On!"
    bash $srcDir"schedule_on.sh"
elif [ "${config,,}" = "off" ]; then
    echo "Off!" 
    bash $srcDir"schedule_off.sh"
elif [ -f $srcDir"configs/"$config ]; then 
    echo Found it! 
    crontab $srcDir"base_cron.txt"
    bash $srcDir"schedule_config.sh" $srcDir"configs/"$config
else
    echo Count not find config
    bash $srcDir"send_mail.sh" "***Warning*** Could not find config for $pi"
fi

bash $srcDir"set_suffix.sh" $suffix
