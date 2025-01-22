
rclone copy aperkes:piManager/monitoring/Checks /tmp/Checks
#rclone copy aperkes:piManager/ScheduleTest.csv /tmp

check_dir="/tmp/Checks"
match_string="(a number means it's recording, if there's no number it's not)"
schedule_file="/tmp/ScheduleTest.csv"

for file in "$check_dir"/*; do
## But would be easy enough to vix
    if [[ $file != *"pi"* ]]; then
        v_n=${file##*V}
        v_n=${v_n%%.*}
        pi='V'$v_n
        #echo "Skipping $file, $pi"
        #continue
    else
        pi_n=${file##*pi}
        pi_n=${pi_n%%.*}
        pi="pi"$pi_n

    fi

    echo $pi
    day_hour=$( date +"%d%H" )
    if [[ -f "$file" ]]; then
        first_line=$(sed -n '1p' "$file")
        check_array=($first_line)
        check_day=${check_array[1]}
        check_time=${check_array[3]}
        check_hour=${check_time%%:*}
        check_dh=$check_day$check_hour
        hour_diff=$(($day_hour-$check_dh))
## check this down below, because I want more info

        second_line=$(sed -n '2p' "$file")

## Check if it's not recording
        if [[ "$second_line" == "$match_string" ]]; then
            echo "$file Not recording!"
            pi_sched=$(grep "$pi" $schedule_file)

            #echo $pi_sched
            #off_check=$(grep ",off," $pi_sched)
            #echo $pi_sched $off_check
            if [[ "$pi_sched" == *",on,"* ]]; then
                echo "Should be recording!"
                bash ~/Documents/Scripts/FishTrack/src/send_mail.sh "*** ALERT!! *** $pi has stopped recording, but seems to be scheduled"
###  Need to add in what to do for configs...
            else
                echo "But that's fine"
            fi
        else
            echo "$file recording!"
        fi

## Now check the hour difference, knowing whether it should be scheduled
        if [[ $hour_diff -gt 2 ]]; then
            if [[ "$pi_sched" != *",off,"* ]]; then
                echo "Should be recording!"
                bash ~/Documents/Scripts/FishTrack/src/send_mail.sh "*Warning* $pi should be recording, but hasn't checked in for over 2 hours"
            elif [[ $hour_diff -gt 24 ]]; then
                echo "Last update occured more than 24 hours ago"
                bash ~/Documents/Scripts/FishTrack/src/send_mail.sh "*Warning* $pi missed its daily check-in"
            fi
        fi

#break
    fi
done

#rm /tmp/ScheduleTest.csv
rm -r /tmp/Checks
