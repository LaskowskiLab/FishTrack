space='test'


#bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "Good morning! I'm performing my daily pi check"
count=0
#for i in $(cat $1); do
dir_list=$(rclone lsf aperkes:pivideos --dirs-only | grep pi)
tmp_path="/home/ammon/Documents/Scripts/FishTrack/src/tmp.txt"
echo $dir_list
#dir_list="pi09/ pi10/"
for d in $dir_list; do 
    echo $d
    if [[ "epi" == *"$d"* ]]; then
        continue
    fi
    #echo /pivideos/"$d"_monitoring_/hourly_check.txt
    #rclone cat aperkes:/pivideos/"$d"hourly_check.txt
    rclone cat aperkes:/pivideos/"$d"_monitoring_/hourly_check.txt > $tmp_path
    #cat $tmp_path

    tmp_cat="$(cat $tmp_path)"
    tmp_l=$(wc -l < $tmp_path)
    echo $tmp_cat
    echo $tmp_l
    if [ $tmp_l -gt "3" ]; then
        bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "Sorry to interrupt, but you should check on $d ASAP, it looks like something is wrong:" 
        while IFS= read -r line; do
            bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "$line"
            done < $tmp_path
    fi
done
