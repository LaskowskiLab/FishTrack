
#bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "Good morning! I'm performing my daily pi check"
#for i in $(cat $1); do
tmp_path="/home/ammon/Documents/Scripts/FishTrack/src/tmp_snake.txt"


## Check that snakemake is still running
pgrep snakemake > $tmp_path
tmp_l=$(wc -l < $tmp_path)
if [ $tmp_l -lt "1" ]; then
    bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "ALERT: snakemake appears to have stopped"
fi

## Check that there is still space

space="$(df -hk /)"
percentage="${space%\% /}"
percentage="${percentage##* }"

if [ $percentage -gt "80" ]; then
    bash /home/ammon/Documents/Scripts/FishTrack/src/send_mail.sh "**Warning** Compy is at $percentage %"
fi

