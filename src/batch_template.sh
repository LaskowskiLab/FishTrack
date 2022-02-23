for i in $(cat $1); do
ssh $i << EOF
    sudo apt install zip
    zip -r ~/recording/2022.02.22.zip ~/recording/2022.02.22/
    exit
EOF

done
