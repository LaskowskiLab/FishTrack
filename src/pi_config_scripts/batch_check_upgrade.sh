for i in $(cat $1); do

    echo $i
    ssh -t $i "ls -la /var/cache/apt/"

done
