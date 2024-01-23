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

suffix="$(ssh -o "StrictHostKeyChecking=no" $i " cat ~/recording/src/suffix.txt")"
#raspi_id="$(ssh -o "StrictHostKeyChecking=no" $i " pgrep raspivid ")"
raspi_id="$(ssh -o "StrictHostKeyChecking=no" $i " pgrep rpicam-vid ")"


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
    bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "$i is *not recording*: $suffix"
else
    bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "$i is currently recording: $suffix"
    echo Recording

    #bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "TEST: $i is recording ($raspi_id)"
    fi

done

bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "I checked $count pi's."

dice=$(( 1 + $RANDOM % 10))
cyber_ip="$(hostname -I)"
bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "$cyber_ip"

#bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "$dice"

if [ $dice -gt "8" ]; then 
    joke="$(shuf -n 1 /home/ammon/Documents/Scripts/FishTrack/src/fish_jokes.txt)"

    bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "That's all! How about a joke before I go? $joke"
else
    bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "That's all, have a nice day!"

    fi

