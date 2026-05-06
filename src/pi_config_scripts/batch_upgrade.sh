for i in $(cat $1); do

    echo $i
    ssh -t $i "echo ***PASSWORDGOESHERE*** | sudo -S apt update && sudo apt -y upgrade"

done
