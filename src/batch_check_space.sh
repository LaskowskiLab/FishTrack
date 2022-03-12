for i in $(cat $1); do

echo $i
ssh $i << EOF
    echo $HOSTNAME
    pgrep raspistill
    df -h | grep 'root'
    exit
EOF
echo 'End ' $i


done
