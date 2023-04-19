for i in $(cat $1); do

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    echo $HOSTNAME
    exit
EOF
echo 'End ' $i

done
