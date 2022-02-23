for i in $(cat $1); do
ssh $i << EOF
    sudo apt install zip
    cd ~/recording/2022.02.22
    zip -r ../2022.02.22.zip * 
    exit
EOF

done
