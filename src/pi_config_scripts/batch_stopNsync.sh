for i in $(cat $1); do

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    pkill rpicam
    bash ~/recording/mobileSrc/sync_vids.sh &
    exit
EOF
echo 'End ' $i

done
