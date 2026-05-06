for i in $(cat $1); do

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    rclone copy AmazonBox:mobileSrc ./recording/mobileSrc
    cp ./recording/mobileSrc/configs/theo.pilot.txt ./recording/current.config
    cp ~/recording/mobileSrc/mobile_aliases.txt .bash_aliases
    echo 'alias run_theo="bash ~/recording/mobileSrc/watch_mobile.sh ~/recording/mobileSrc/configs/theo.pilot.txt theo.pilot.txt 2>&1 >> ~/recording/cronlog.log &"' >> .bash_aliases
    exit
EOF
echo 'End ' $i

done
