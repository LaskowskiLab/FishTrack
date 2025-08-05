

space="$(df -hk /)"


percentage="${space%\% /}"
percentage="${percentage##* }"


if [ $percentage -gt "90" ]; then
    echo "waiting..."
    sleep 1800
fi
