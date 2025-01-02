
recordingDir="/home/ammon/Documents/Scripts/FishTrack/recording/"
srcDir=$recordingDir"mobileSrc/"
echo rclone copy aperkes:pivideos/ScheduleTest.csv $srcDir
pi_name=${HOSTNAME: -4}
piLine="$(cat $srcDir"ScheduleTest.csv" | grep "pi24")"
#piLine="$(cat $srcDir"ScheduleTest.csv" | grep $pi_name)"
echo $piLine
## split and strip pi line to get pi,suffix,config

pi=${piLine%%,*}
suffix=${piLine#*,}
config=${suffix#*,}

suffix=${suffix%%,*}

config=${config%%,*}
echo $pi
echo $suffix
echo $config

if [ "${config,,}" = "on" ]; then
    echo "On!"
    echo bash $srcDir"schedule_config.sh" $srcDir"configs/default.config"
elif [ "${config,,}" = "off" ]; then
    echo "Off!" 
    echo bash $srcDir"schedule_off.sh"
elif [ -f $srcDir"configs/"$config ]; then 
    echo Found it! 
    echo bash $srcDir"schedule_config.sh" $srcDir"configs/"$config
else
    echo Count not fine config
    echo bash $srcDir"send_mail.sh" "***Warning*** Could not find config for $pi"
fi

echo bash $srcDir"set_suffix.sh" $suffix
