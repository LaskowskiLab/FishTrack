
check="$(rclone lsf aperkes: | grep pivideos | wc -l)"

i=$HOSTNAME

echo $check

if [ "$check" -lt 1 ]; then
    echo Fail!
    bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "**Warning** $i has expired rclone token"
fi
