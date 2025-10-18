for i in $(cat $1); do

echo $i
#pub_key=$(cat $2)
pub_key=$2
ssh -o StrictHostKeyChecking=no $i << EOF
    echo $HOSTNAME
    echo $pub_key >> ~/.ssh/authorized_keys
    exit
EOF
echo 'End ' $i

done
