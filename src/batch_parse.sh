for i in $(cat $1); do

    echo $i
    python ~/Documents/Scripts/FishTrack/src/parse-trex.py -i $i -s
done

