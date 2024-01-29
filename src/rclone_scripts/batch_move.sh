## WARNING!!! This code will ruin your life

# ok, that's a bit dramatic, but it can delete files, 
# so you had better be absolutely sure you know what you're doing, and best use --dry-run the first time

## this take 4 command line arguments, all are requried

# $1: the target substring (e.g., rogue)
# $2: the new parent (e.g., pivideos.wastebin)

target_str=$1
dest=$2

for i in $(rclone lsf aperkes:/pivideos --max-depth 2 | grep $target_str); do

    echo pivideos/$i to $dest/$i
    rclone move aperkes:pivideos/$i aperkes:$dest/$i --delete-empty-src-dirs
done
