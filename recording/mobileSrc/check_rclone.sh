
check="$(rclone lsf AmazonBox: | grep pivideos | wc -l)"

i=$HOSTNAME

echo $check

if [ "$check" -lt 1 ]; then
    echo Fail!
    bash ~/recording/mobileSrc/send_mail.sh "**Warning** $i has expired rclone token"
fi
