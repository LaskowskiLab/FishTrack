
yesterday=$(date -d "yesterday 13:00" '+%Y.%m.%d')
ymd=${1-"$yesterday"}
echo $ymd
#ymd="2024.06.01"

working_dir="/home/ammon/Documents/Scripts/FishTrack/working_dir/"
img_dir=$working_dir"todaysShots/"

echo $ymd
dir_list=$(rclone lsf aperkes:/pivideos/ --max-depth 2 | grep $ymd | grep pi | sort)

echo $dir_list
for d in $dir_list; do
    pi=${d%%/202*}
    vid_name="$pi.$ymd.06.00.h264"
    vid30fps="$pi.$ymd.06.00.30fps.mp4"
    vid_1min="$pi.$ymd.06.00.60s.mp4"
    vid_shot="$pi.$ymd.screenshot.png"
    rclone copy aperkes:/pivideos/$d$vid_name $working_dir -P
    ffmpeg -fflags +genpts -r 30 -i $working_dir$vid_name -c:v copy $working_dir$vid30fps -hide_banner -loglevel error
## Add a check for original fps, shift the ss so that it's recording at the same time.
    f_size=$(du -b $working_dir$vid_name)
    f_size=${f_size%%[[:space:]]*}
    echo File size: $f_size
    if [ $f_size -gt "5000000000" ]; then
        fps=30
    else
        fps=1
    fi  
    echo Using $fps fps
    ffmpeg -ss $((720 * $fps)) -i $working_dir$vid30fps -t 180 $working_dir$vid_1min -hide_banner -loglevel error
    ffmpeg -i $working_dir$vid_1min -update true -frames:v 1 $working_dir$vid_shot -y -hide_banner -loglevel error

    cp $working_dir$vid_shot $img_dir
    rclone move $working_dir$vid_shot aperkes:/pivideos/1Shots/$pi/
    rclone move $working_dir$vid_1min aperkes:/pivideos/1Clips/$pi/
    rclone move $working_dir$vid30fps aperkes:/pivideos/$d
    rm $working_dir$vid_name
done

for i in $(seq -f "%02g" "1" "24"); do
    f_name="pi$i.$ymd.screenshot.png"
    if [[ ! -f "$img_dir$f_name" ]]; then
        ffmpeg -f lavfi -i color=size=1080x1080:color=black -update true -frames:v 1 -y "$img_dir$f_name" -hide_banner -loglevel error
    fi
done

#ffmpeg -framerate 1 -i $img_dir"pi%02d.$ymd.screenshot.png" -update true -frames:v 1 -filter_complex "tile=6x4" $working_dir$ymd".mosaic.png"

## Tiling them in the order of the pie required a lot of hard coding. This seemed simplest
cd $img_dir
#mv pi02.$ymd.screenshot.png 01.png
ffmpeg -i pi02.$ymd.screenshot.png -vf rotate=PI,drawtext="fontcolor=red:text='Pi02':fontsize=64" 01.png -hide_banner -loglevel error
#mv pi04.$ymd.screenshot.png 02.png
ffmpeg -i pi04.$ymd.screenshot.png -vf rotate=PI,drawtext="fontcolor=red:text='Pi04':fontsize=64" 02.png -hide_banner -loglevel error
#mv pi06.$ymd.screenshot.png 03.png
ffmpeg -i pi06.$ymd.screenshot.png -vf rotate=PI,drawtext="fontcolor=red:text='Pi06':fontsize=64" 03.png -hide_banner -loglevel error
#mv pi08.$ymd.screenshot.png 04.png
ffmpeg -i pi08.$ymd.screenshot.png -vf rotate=PI,drawtext="fontcolor=red:text='Pi08':fontsize=64" 04.png -hide_banner -loglevel error
#mv pi10.$ymd.screenshot.png 05.png
ffmpeg -i pi10.$ymd.screenshot.png -vf rotate=PI,drawtext="fontcolor=red:text='Pi10':fontsize=64" 05.png -hide_banner -loglevel error
#mv pi12.$ymd.screenshot.png 06.png
ffmpeg -i pi12.$ymd.screenshot.png -vf rotate=PI,drawtext="fontcolor=red:text='Pi12':fontsize=64" 06.png -hide_banner -loglevel error

#mv pi01.$ymd.screenshot.png 07.png
ffmpeg -i pi01.$ymd.screenshot.png -vf drawtext="fontcolor=red:text='Pi01':fontsize=64" 07.png -hide_banner -loglevel error
#mv pi03.$ymd.screenshot.png 08.png
ffmpeg -i pi03.$ymd.screenshot.png -vf drawtext="fontcolor=red:text='Pi03':fontsize=64" 08.png -hide_banner -loglevel error
#mv pi05.$ymd.screenshot.png 09.png
ffmpeg -i pi05.$ymd.screenshot.png -vf drawtext="fontcolor=red:text='Pi05':fontsize=64" 09.png -hide_banner -loglevel error
#mv pi07.$ymd.screenshot.png 10.png
ffmpeg -i pi07.$ymd.screenshot.png -vf drawtext="fontcolor=red:text='Pi07':fontsize=64" 10.png -hide_banner -loglevel error
#mv pi09.$ymd.screenshot.png 11.png
ffmpeg -i pi09.$ymd.screenshot.png -vf drawtext="fontcolor=red:text='Pi09':fontsize=64" 11.png -hide_banner -loglevel error
#mv pi11.$ymd.screenshot.png 12.png
ffmpeg -i pi11.$ymd.screenshot.png -vf drawtext="fontcolor=red:text='Pi11':fontsize=64" 12.png -hide_banner -loglevel error

#mv pi14.$ymd.screenshot.png 13.png
ffmpeg -i pi14.$ymd.screenshot.png -vf rotate=PI,drawtext="fontcolor=red:text='Pi14':fontsize=64" 13.png -hide_banner -loglevel error
#mv pi16.$ymd.screenshot.png 14.png
ffmpeg -i pi16.$ymd.screenshot.png -vf rotate=PI,drawtext="fontcolor=red:text='Pi16':fontsize=64" 14.png -hide_banner -loglevel error
#mv pi18.$ymd.screenshot.png 15.png
ffmpeg -i pi18.$ymd.screenshot.png -vf rotate=PI,drawtext="fontcolor=red:text='Pi18':fontsize=64" 15.png -hide_banner -loglevel error
#mv pi20.$ymd.screenshot.png 16.png
ffmpeg -i pi20.$ymd.screenshot.png -vf rotate=PI,drawtext="fontcolor=red:text='Pi20':fontsize=64" 16.png  -hide_banner -loglevel error
#mv pi22.$ymd.screenshot.png 17.png
ffmpeg -i pi22.$ymd.screenshot.png -vf rotate=PI,drawtext="fontcolor=red:text='Pi22':fontsize=64" 17.png  -hide_banner -loglevel error
#mv pi24.$ymd.screenshot.png 18.png
ffmpeg -i pi24.$ymd.screenshot.png -vf rotate=PI,drawtext="fontcolor=red:text='Pi24':fontsize=64" 18.png -hide_banner -loglevel error 

#mv pi13.$ymd.screenshot.png 19.png
ffmpeg -i pi13.$ymd.screenshot.png -vf drawtext="fontcolor=red:text='Pi13':fontsize=64" 19.png -hide_banner -loglevel error 
#mv pi15.$ymd.screenshot.png 20.png
ffmpeg -i pi15.$ymd.screenshot.png -vf drawtext="fontcolor=red:text='Pi15':fontsize=64" 20.png -hide_banner -loglevel error 
#mv pi17.$ymd.screenshot.png 21.png
ffmpeg -i pi17.$ymd.screenshot.png -vf drawtext="fontcolor=red:text='Pi17':fontsize=64" 21.png -hide_banner -loglevel error 
#mv pi19.$ymd.screenshot.png 22.png
ffmpeg -i pi19.$ymd.screenshot.png -vf drawtext="fontcolor=red:text='Pi19':fontsize=64" 22.png -hide_banner -loglevel error 
#mv pi21.$ymd.screenshot.png 23.png
ffmpeg -i pi21.$ymd.screenshot.png -vf drawtext="fontcolor=red:text='Pi21':fontsize=64" 23.png  -hide_banner -loglevel error
#mv pi23.$ymd.screenshot.png 24.png
ffmpeg -i pi23.$ymd.screenshot.png -vf drawtext="fontcolor=red:text='Pi23':fontsize=64" 24.png  -hide_banner -loglevel error

ffmpeg -framerate 1 -i $img_dir"%02d.png" -update true -frames:v 1 -filter_complex "tile=6x4" $working_dir$ymd".mosaic.png" -hide_banner -loglevel error

if [ -z $1 ]; then
    rclone copyto $working_dir$ymd".mosaic.png" aperkes:/piManager/monitoring/yesterday.mosaic.png
fi
rclone move $working_dir$ymd".mosaic.png" aperkes:/pivideos/1Mosaics/
rm $img_dir*.png 
