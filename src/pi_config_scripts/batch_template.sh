for i in $(cat $1); do

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
=======
    bash ~/recording/mobileSrc/set_suffix.sh ammon.WinEff.pilot2
    nohup bash ~/recording/mobileSrc/watch_mobile.sh ~/recording/mobileSrc/configs/30fps12hr.config > /tmp/last_cron.txt 2>&1 </dev/null &
    exit
EOF
echo 'End ' $i

done
