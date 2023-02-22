import pandas as pd
import sys
import subprocess

infile = sys.argv[1]
test = pd.read_csv(infile)

working_dir = '/home/ammon/Videos/babies/'
for index, row in test.iterrows():
    print(row.x0,row.y1,row.w,row.h)
    if row.Pi == 19:
        continue
    if row.Empty == 1:
        continue
    in_file = row.video
    print(str(row.video))
    fish_suffix = '_' + str(row.Tank) + '.mp4'
    print(fish_suffix)
    out_file = str(row.video).replace('.mp4',fish_suffix)
    out_w = row.w
    out_h = row.h
    x = row.x0
    y = row.y0
    #command = f'ffmpeg -i "{working_dir}{in_file}" -filter:v "crop={out_w}:{out_h}:{x}:{y}" -c:v libx264 -crf 13 "{working_dir}singles/{out_file}" -y'
    command1 = f'ffmpeg -i "{working_dir}{in_file}" -map 0:v -c:v copy -bsf:v h264_mp4toannexb "{working_dir}raw.h264" -y'
    subprocess.call(command1,shell=True)
    
    command2 = f'ffmpeg -i "{working_dir}raw.h264" -r 1 -filter:v "crop={out_w}:{out_h}:{x}:{y},setpts=25*PTS" -c:v libx264 "{working_dir}singles/{out_file}" -y'
    subprocess.call(command2,shell=True)
    print(command1,command2)
    #break
