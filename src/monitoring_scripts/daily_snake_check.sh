
bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "Hi there, me again, I'm performing my daily Snake pipeline check for $HOSTNAME"

echo ""

snake_dir="/home/ammon/Documents/Scripts/FishTrack/src/snake_pipelines"
total_files=$(cat $snake_dir/path_lists/jay.sailfins.paths.txt | wc -l)
finished_files=$(ls "$snake_dir"/snake/results/csv | grep 2024 |  wc -l)

tmp_path="/home/ammon/Documents/Scripts/FishTrack/src/tmp_snake.txt"
pgrep snakemake > $tmp_path
tmp_l=$(wc -l < $tmp_path)
tmp_l=$(cat $tmp_path | wc -l)
echo $tmp_l

if [ $tmp_l -gt "0" ]; then
    bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "It looks like snakemake is still running"
else
    bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "It looks like snakemake has stopped, hopefully that's what you want"
fi

space="$(df -hk /)"
percentage="${space%\% /}"
percentage="${percentage##* }"


bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "So far Snake has finished $finished_files of $total_files videos"
bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "Current disc usage is $percentage %"


