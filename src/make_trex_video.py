import parse_trex
import numpy as np
from matplotlib import pyplot as plt
import cv2
import subprocess
import sys

#file_object = np.load('/home/ammon/Videos/data/pi13.2022.10.30.batch.trex.crop_3_fish0.npz')
#vid_name = '/home/ammon/Videos/babies/singles/pi13.2022.10.30.batch.trex.crop_3.mp4'

vid_name = sys.argv[1]
npz_name = vid_name.replace('.mp4','_fish0.npz')
npz_name = npz_name.replace('/babies/singles','/data')
file_object = np.load(npz_name)
#out_file = '/home/ammon/Videos/babies/singles/pi13.2022.10.30.batch.trex.crop_3.tracked.mp4'
out_file = vid_name.replace('.mp4','.tracked.mp4')

#cm_per_pixel =  0.083799 ## pi13
if False:
    cm_per_pixel = 0.086207 ##pi15 crop_0
    x_win,y_win = [0,160],[0,157] ## Crop_0
    base_cor = [0,0,255]
elif False:
    cm_per_pixel = 0.086705 ##pi15 crop_1
    x_win,y_win = [198,1000],[0,165] ## Crop_1
    base_cor = [255,255,0] ## Yellow
elif False:
    cm_per_pixel = 0.087209 ##pi15 crop_2
    x_win,y_win = [0,154],[274,1000] ## Crop_2
    base_cor = [0,255,0] ## Green
elif True:
    cm_per_pixel = 0.087209 ##pi15 crop_3
    x_win,y_win = [198,1000],[267,1000] ## Crop_3
    base_cor = [0,165,255] ## Orange

VIDEO = True
PLOT = False

xs = file_object['X']
ys = file_object['Y']
#a = np.array([xs,ys])
a = np.empty([len(xs),2])
a[:,0] = parse_trex.clear_lone_points(xs)
a[:,1] = parse_trex.clear_lone_points(ys)
clean_xs = a[:,0]
#clean_xs = parse_trex.clear_lone_points(xs)
#print(a[0,:10])
#print(clean_xs[0,:10])
#import pdb;pdb.set_trace()
smooth_a = np.empty_like(a)
smooth_a[:,0] = parse_trex.interp_track(a[:,0])
smooth_a[:,1] = parse_trex.interp_track(a[:,1])
smooth_xs = smooth_a[:,0]
#smooth_a = smooth_a.astype(int)
a = smooth_a * (1/cm_per_pixel)
a = a.astype(int)

def get_stats(a,x_win=[198,1000],y_win=[267,1000]):
    #x_pipe,y_pipe = 198,267
    x_hiding = (a[:,0] > x_win[0]) & (a[:,0] < x_win[1])
    y_hiding = (a[:,1] > y_win[0]) & (a[:,1] < y_win[1])
    hiding_time = x_hiding & y_hiding
    #hiding_time = (a[:,0] > 209) & (a[:,1] > 286)

    prop_hiding = np.sum(hiding_time) / len(hiding_time)
    dx = np.diff(a[:,0])
    dy = np.diff(a[:,1])
    steps = np.sqrt(dx**2 + dy**2)
    vel = steps * cm_per_pixel
    distance = np.sum(steps)
    mean_speed = np.mean(vel)
    vel = np.round(vel,2)
    #import pdb;pdb.set_trace()
    return hiding_time,prop_hiding,vel,mean_speed
  
if True:
    """
    x_pipe,y_pipe = 198,267
    hiding_time = (a[:,0] > 209) & (a[:,1] > 286)
    prop_hiding = np.sum(hiding_time) / len(hiding_time)
    dx = np.diff(a[:,0])
    dy = np.diff(a[:,1])
    steps = np.sqrt(dx**2 + dy**2)
    vel = steps * cm_per_pixel
    distance = np.sum(steps)
    mean_speed = np.mean(vel)
    vel = np.round(vel,2)
    """
    hiding_time,prop_hiding,vel,mean_speed = get_stats(a,x_win,y_win)
    print('prop hiding,mean speed')
    print(prop_hiding,mean_speed)
## Sub sample to get variance:
    speed_list = np.zeros(10)
    hide_list = np.zeros(10)
    window = len(a) // 10
    for b in range(10):

        b0 = window * b
        b1 = b0 + window
        _1,sub_hiding,_2,sub_mean = get_stats(a[b0:b1],x_win,y_win)
        speed_list[b] = sub_mean
        hide_list[b] = sub_hiding
    print(np.mean(speed_list),np.std(speed_list),np.mean(hide_list),np.std(hide_list))

if False:
    fig,ax=plt.subplots()

    ax.scatter(np.arange(len(xs)),xs,color='black',marker='.',alpha=0.5)
    ax.plot(clean_xs,color='black')
    ax.plot(smooth_xs,alpha=0.5,color='red')

    plt.show()

path = '/home/ammon/Documents/Scripts/FishTrack/working_dir/tmp/'
if VIDEO:
    print('making imgs...')
    tail_length = 20 
    cap = cv2.VideoCapture(vid_name)

#fig,ax = plt.subplots()
    t = 0
    rad = 5
    while(cap.isOpened()):
        ret,frame = cap.read()
        if ret == True:
            #print(t,(a[t,0],a[t,1]))
            #detection = cv2.circle(frame,(a[t,0],a[t,1]),radius=rad,color=(255,0,0), thickness=-1)
            for l in range(0,min(t,tail_length)):
                r = max(2,rad-l)
                if hiding_time[t]:
                    cor = (255,0,0)
                else:
                    cor = base_cor
                cv2.circle(frame,(a[t-l,0],a[t-l,1]),radius=r,color=cor, thickness=-1)
                speed = str(vel[t]) + ' cm/s'
                cv2.putText(frame,speed,(25,25),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,0),2)
            num = f'{t:05d}'
            img_name = path + 'Frame_'+ num + '.png'
            #print(img_name)
            cv2.imwrite(img_name,frame)
            t += 1

            if PLOT:
                cv2.imshow('Frame',frame)
                key = cv2.waitKey(20)
                if key == ord('q'):
                    break
            if t > 3600:
                break
        else:
            break

    cap.release()
    cv2.destroyAllWindows()

    if not PLOT:
        command = f'ffmpeg -r 60 -f image2 -i /home/ammon/Documents/Scripts/FishTrack/working_dir/tmp/Frame_%05d.png -vcodec libx264 -crf 20 -pix_fmt yuv420p {out_file} -y'

        subprocess.call(command,shell=True)

    print('Deleting imgs')
    command2 = f'rm /home/ammon/Documents/Scripts/FishTrack/working_dir/tmp/*.png'
    subprocess.call(command2,shell=True)

### Reminder, for a gif, use something like this: ffmpeg -i '/home/ammon/Downloads/baby_tracking_demo4.mp4' -filter_complex "[0:v] palettegen" ~/Downloads/baby_palette.png; ffmpeg -i '/home/ammon/Downloads/baby_tracking_demo4.mp4' -r 6 -i ~/Downloads/baby_palette.png -filter_complex "[0:v] fps=10,scale=480:-1 [new];[new][1:v] paletteuse" ~/Downloads/babies_r6f10.gif

print('Done-zo!')
