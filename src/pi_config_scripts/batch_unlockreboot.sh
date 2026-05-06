for i in $(cat $1); do

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    echo $HOSTNAME
    sudo echo ## Allow users to reboot >> /etc/sudoers
    sudo echo pi ALL=NOPASSWD:/sbin/reboot >> /etc/sudors
    exit
EOF
echo 'End ' $i

done
