
ssh -o StrictHostKeyChecking=no $1 << EOF
    raspistill -o ~/recording/cam_check.jpg
    exit
EOF

scp $1:~/recording/cam_check.jpg ~/Documents/Scripts/FishTrack/recording/now/$1.jpg

