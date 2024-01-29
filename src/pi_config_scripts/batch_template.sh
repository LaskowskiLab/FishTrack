for i in $(cat $1); do

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    echo $HOSTNAME
    cat ~/recording/src/suffix.txt
    cat ~/recording/suffix.txt
    cp ~/recording/src/suffix.txt ~/recording
    exit
EOF
echo 'End ' $i

done
