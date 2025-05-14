
pi=${1-1}
pi_family=${2-V0}

i=pi@$pi_family$pi.local

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    nohup bash ~/recording/mobileSrc/watch_mobile.sh ~/recording/mobileSrc/current.config > /home/pi/recording/cronlog.log 2>&1 </dev/null &
    exit
EOF
echo 'End ' $i
