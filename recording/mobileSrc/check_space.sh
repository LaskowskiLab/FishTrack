
i="$HOSTNAME"

echo $i
echo $count

space="$(df -hk /)"

echo $space

percentage="${space%\% /}"
percentage="${percentage##* }"
echo $percentage
if [ $percentage -gt "80" ]; then
    echo getting full
    bash ~/recording/mobileSrc/send_mail.sh "**Warning** $i at $percentage %"
else
    echo Doing ok...
fi

