

space="$(df -hk /)"


percentage="${space%\% /}"
percentage="${percentage##* }"


if [ $percentage -gt "70" ]; then
    echo "waiting..."
    sleep 1800
fi
