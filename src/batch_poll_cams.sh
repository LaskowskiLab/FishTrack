
rm ~/Documents/Scripts/FishTrack/recording/now/*.jpg

for i in $(cat $1); do
ssh $i << EOF
    raspistill -o ~/Desktop/CCtest/test.jpg
    exit
EOF

scp $i:~/Desktop/CCtest/test.jpg ~/Documents/Scripts/FishTrack/recording/now/$i.jpg

done
