
## Set restart count high so that it doesn't reset when video stops
echo 10 > /home/pi/recording/restart_count.txt
pkill -2 rpicam
