for i in $(cat $1); do

echo $i
ssh $i << EOF
    echo $HOSTNAME
    passwd
    Pformosa
    REDACTED
    REDACTED
    exit
EOF
echo 'End ' $i

done
