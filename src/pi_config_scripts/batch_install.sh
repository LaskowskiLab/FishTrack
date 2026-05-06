for i in $(cat $1); do

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    echo $HOSTNAME
    rclone copy AmazonBox:/src/ ~/recording/src
    echo ****PASSWORD****? | sudo -S apt-get install at -y
    exit
EOF
echo 'End ' $i

done
