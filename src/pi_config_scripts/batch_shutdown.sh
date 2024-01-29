for i in $(cat $1); do
ssh $i << EOF
    pkill raspivid
    sudo shutdown
    exit
EOF

done
