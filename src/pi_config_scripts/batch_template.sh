for i in $(cat $1); do

echo $i
ssh -o StrictHostKeyChecking=no $i << EOF
    cp ~/recording/mobileSrc/configs/kas_agg.txt ~/recording/mobileSrc/current.config
    echo 'alias upload_vids="bash ~/recording/mobileSrc/sync_vids.sh &"' >> ~/.bash_aliases
    exit
EOF
echo 'End ' $i

done
