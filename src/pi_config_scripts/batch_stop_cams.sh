for i in $(cat $1); do
ssh $i << EOF
    pkill raspistill
    exit
EOF

done
