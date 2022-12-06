space='test'


bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "Good morning! I'm performing my daily pi check"
count=0
for i in $(cat $1); do
count=$((count+1)) 

echo $i
echo $count
space="$(ssh -o "StrictHostKeyChecking=no" $i " df -hk /")"

if [ -z "$space" ]; then
    echo "it's blank!"
    bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "Could not connect to $i"
    continue
    fi

raspi_id="$(ssh -o "StrictHostKeyChecking=no" $i " pgrep raspivid ")"

echo $space
echo $raspi_id

percentage="${space%\% /}"
percentage="${percentage##* }"
echo $percentage
if [ $percentage -gt "50" ]; then
    echo getting full
    bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "**Warning** $i at $percentage %"
else
    echo Plenty of space
    #bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "TEST: $i at $percentage %"
fi

if [ -z "$raspi_id" ]; then
    echo Empty
    bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "$i is not recording"
else
    echo Recording

    #bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "TEST: $i is recording ($raspi_id)"
    fi

done

bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "That's all, I checked $count pi's. Have a nice day!"

