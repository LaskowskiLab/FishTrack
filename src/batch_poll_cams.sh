
rm ~/Documents/Scripts/FishTrack/recording/now/*.jpg

for i in $(cat $1); do
ssh -o StrictHostKeyChecking=no $i << EOF
    raspistill -o ~/recording/cam_check.jpg
    exit
EOF

scp $i:~/recording/cam_check.jpg ~/Documents/Scripts/FishTrack/recording/now/$i.jpg

done
