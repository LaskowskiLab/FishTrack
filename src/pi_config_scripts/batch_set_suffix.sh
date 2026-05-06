for i in $(cat $1); do

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    bash ./recording/mobileSrc/set_suffix.sh skc.ch1
    exit
EOF
echo 'End ' $i

done
