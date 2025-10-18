for i in $(cat $1); do

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    echo $HOSTNAME
    stop_recording
    echo Arethereanyclones4me? | sudo -S shutdown
    exit
EOF
echo 'End ' $i

done
