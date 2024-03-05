for i in $(cat $1); do

echo $i
ssh $i << EOF
    echo $HOSTNAME
    pkill rpicam
    bash ./recording/src/run_vid.sh
    exit
EOF
echo 'End ' $i


done
