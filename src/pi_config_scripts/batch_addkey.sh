for i in $(cat $1); do

echo $i
echo $2

ssh -o StrictHostKeyChecking=no $i << EOF
    sudo apt-get install rclone
    echo $HOSTNAME
    mkdir .ssh
    echo $2 >> ~/.ssh/authorized_keys
    exit
EOF
echo 'End ' $i

done
