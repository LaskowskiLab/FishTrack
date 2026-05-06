

space="$(df -hk /)"


percentage="${space%\% /}"
percentage="${percentage##* }"


if [ $percentage -gt "75" ]; then
    echo "waiting..."
    sleep 1300
fi
