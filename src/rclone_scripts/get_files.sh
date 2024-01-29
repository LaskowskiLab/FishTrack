
## $1 is a list of paths, created with rclone lsf aperkes:/pivideos --max-depth 2 | grep your.suffix
# you also need to use vim to add /pivideos before all the lines
## $2 is the list of files you want

for i in $(cat $1); do
    rclone lsf aperkes:$i --include *h264 >> $2
done
