for i in $(cat $1); do

echo $i
ssh $i << EOF
    echo $HOSTNAME
    passwd
    Pformosa
    Arethereanyclones4me?
    Arethereanyclones4me?
    exit
EOF
echo 'End ' $i

done
