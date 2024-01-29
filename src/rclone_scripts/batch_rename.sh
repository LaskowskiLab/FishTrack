## WARNING!!! This code will ruin your life

# ok, that's a bit dramatic, but it can delete files, 
# so you had better be absolutely sure you know what you're doing, and best use --dry-run the first time

## this take 4 command line arguments, all are requried
# $1: first you need a list of files, you can get that using
# lsf rclone lsf aperkes:pivideos/pi13 --dirs-only | grep 
# although note that this will only give you the final dir, not the full path, so you will need to modify line 18 to have the pi

# $2: the pi to change (e.g., pi22)
# $3: the current substring (e.g., rogue) 
# $4: the new substring (e.g., jay.babytracking.T22-1)

pi=$2
target_str=$3
new_str=$4

for i in $(cat $1); do

    echo $i
    #echo "${i/"$target_str"/"$new_str"}"
    new_file="${i/"$target_str"/"$new_str"}"
    rclone move aperkes:pivideos/$2/$i aperkes:pivideos/$2/$new_file --dry-run

done
