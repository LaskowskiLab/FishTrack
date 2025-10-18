## First , read off the list of files

fishtrack_path='/home/ammon/Documents/Scripts/FishTrack/'
working_dir=$fishtrack_path"working_dir/"

#vid_file=$fishtrack_path'test_vid_list.txt'
#vid_file=$fishtrack_path'jaylist.clean.txt'
vid_file="/data/tracking/abby.ELS/abby.ELS.preds.txt"
merge_file=$fishtrack_path'abby.clip_list2.txt'

vid_list=$(cat $vid_file)

for f in $vid_list; do
    echo $f
    rclone copy aperkes:"/Laskowski Lab/Abby/Early Life Stress/Data/Model Predator Videos/Cropped Videos Redo/"$f $working_dir -P
    base_f=$(basename $f)
    video_path=$working_dir$base_f
    echo $video_path
    out_path=${video_path%.mp4}'.clip5s.mp4'

    #ffmpeg -i $video_path -vf "select='between(t,480,481) + between(t,500,501) + between(t,540,541) + between(t,600,601)',setpts=N/FRAME_RATE/TB" $out_path -y
    #ffmpeg -i $video_path -vf "select='between(t,480,482) + between(t,500,502) + between(t,530,532) + between(t,600,602)',setpts=N/FRAME_RATE/TB" $out_path -y
    ffmpeg -i $video_path -ss 480 -t 5 $out_path -y

    #ffmpeg -i $video_path -vf "select='between(t,220,221) + between(t,320,321) + between(t,420,421) + between(t,520,521) + between(t,620,621) + between(t,720,721) + between(t,820,821) + between(t,920,921) + between(t,1020,1021) + between(t,1120,1121) + between(t,1220,1221) + between(t,1320,1321) + between(t,1420,1421) + between(t,1520,1521) + between(t,1620,1621)', setpts=N/FRAME_RATE/TB" $out_path -n
    #ffmpeg -i $video_path -vf "select='between(t,799,801) + between(t,1399,1401) + between(t,1899,1901)', setpts=N/FRAME_RATE/TB" $out_path -n
    #ffmpeg -i $video_path -vf "select='between(t,1399,1401) + between(t,1599,1601) + between(t,1899,1901) + select='between(t,1999,2001)', setpts=N/FRAME_RATE/TB" $out_path -y

    
    echo file $out_path >> $merge_file 
    #rm $video_path
    #break
done

outfile=${vid_file%.txt}'.take2.mp4'

ffmpeg -f concat -safe 0 -i "$merge_file" $outfile -y

