import parse_sleap
import numpy as np
from matplotlib import pyplot as plt
import cv2
import subprocess
import sys
import h5py

#file_object = np.load('/home/ammon/Videos/data/pi13.2022.10.30.batch.trex.crop_3_fish0.npz')
#vid_name = '/home/ammon/Videos/babies/singles/pi13.2022.10.30.batch.trex.crop_3.mp4'

vid_name = sys.argv[1]
h5_name = vid_name.replace('.mp4','.analysis.h5')
#npz_name = npz_name.replace('/babies/singles','/data')
#file_object = np.load(h5_name)
#out_file = '/home/ammon/Videos/babies/singles/pi13.2022.10.30.batch.trex.crop_3.tracked.mp4'
out_file = vid_name.replace('.mp4','.tracked.mp4')
VIDEO = True
PLOT = False
FULL = False

with h5py.File(h5_name, 'r') as f:
    dset_names = list(f.keys())
    locations = f['tracks'][:].T
    node_names = [n.decode() for n in f["node_names"][:]]
    track_occupancy = f['track_occupancy'][:].T

a = locations[:,3,:,0]
print(a.shape)
#import pdb;pdb.set_trace()
#a[:,1] = 1080 - a[:,1]

#a = np.flipud(a)
## there's a bad double detection out of the pool
a[a[:,0] < 50] = [np.nan,np.nan]

## There's a predator detection
a[371:386] = [np.nan,np.nan]

clean_xs = parse_sleap.clear_lone_points(a[:,0])
clean_ys = parse_sleap.clear_lone_points(a[:,1])
b = np.empty_like(a)
b[:,0] = clean_xs
b[:,1] = clean_ys
b = parse_sleap.clear_teleports(b)

smooth_a = np.empty_like(b)
smooth_a[:,0] = parse_sleap.interp_track(b[:,0])
smooth_a[:,1] = parse_sleap.interp_track(b[:,1])

smooth_xs = smooth_a[:,0]
smooth_ys = smooth_a[:,1]

cm_per_pixel = 1
a = smooth_a * (1/cm_per_pixel)
a = a.astype(int)

#import pdb;pdb.set_trace()
if False:
    xs = a[:,1]
    fig,ax=plt.subplots()

    ax.scatter(np.arange(len(xs)),xs,color='black',marker='.',alpha=0.5)
    ax.plot(clean_ys,color='black')
    ax.plot(smooth_ys,alpha=0.5,color='red')

    plt.show()

## Plot heatmap overlay
if False:
# get colormap
    from matplotlib.colors import LinearSegmentedColormap

    ncolors = 256
    ntrans = 100
    color_array = plt.get_cmap('viridis')(range(ncolors))

# change alpha values
    color_array[:ntrans,-1] = np.linspace(0.0,1.0,ntrans)
    #color_array[0,-1] = 0

# create a colormap object
    map_object = LinearSegmentedColormap.from_list(name='viridis_alpha',colors=color_array)

# register this new colormap with matplotlib
    plt.register_cmap(cmap=map_object)

    
    fig,ax =plt.subplots()

    x,y = a[:,0],a[:,1]
    heatmap, xedges, yedges = np.histogram2d(x, y, bins=50,range=[[0,1600],[0,1200]])
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

    #ax.scatter(a[:,0],a[:,1],color='black',alpha=0.01)
    br_image = plt.imread('/home/ammon/Documents/Scripts/FishTrack/working_dir/sleap_test/Labels.002.image.png')
    ax.imshow(br_image)
    ax.imshow(heatmap.T, extent=extent, origin='lower',cmap='viridis_alpha',vmax=200,interpolation='catrom')
    plt.gca().invert_yaxis()
    plt.xticks([]) 
    plt.yticks([]) 

    #import pdb;pdb.set_trace()
    fig.savefig('/home/ammon/Desktop/smoothJon.png',dpi=300)
    plt.show()

def get_stats(a,x_win=[198,1000],y_win=[267,1000],cm_per_pixel = 1):
    x_hiding = (a[:,0] > x_win[0]) & (a[:,0] < x_win[1])
    y_hiding = (a[:,1] > y_win[0]) & (a[:,1] < y_win[1])
    hiding_time = x_hiding & y_hiding

    prop_hiding = np.sum(hiding_time) / len(hiding_time)
    dx = np.diff(a[:,0],prepend=0)
    dy = np.diff(a[:,1],prepend=0)
    steps = np.sqrt(dx**2 + dy**2)
    vel = steps * cm_per_pixel
    distance = np.sum(steps)
    mean_speed = np.mean(vel)
    vel = np.round(vel,2)
    return hiding_time,prop_hiding,vel,mean_speed

## This is for Jon
areas = {
    'left_cup':[[[198,400],[470,640]],(255,0,0)],
    'right_cup':[[[1290,1490],[350,530]],(255,255,0)],
    'predator':[[[660,1150],[895,1150]],(0,255,255)],
    'green':[[[310,1200],[0,340]],(0,255,0)]}
if True:
    #x_win,y_win = [198,400],[470,640]
    #hiding_time,prop_hiding,vel,mean_speed = get_stats(a,x_win,y_win)
    #print('prop hiding,mean speed')
    #print(prop_hiding,mean_speed)
## Sub sample to get variance:
    #speed_list = np.zeros(10)
    #hide_list = np.zeros(10)
    #window = len(a) // 10
    for z in areas.keys():
        x_win,y_win = areas[z][0] 
        hiding_time,prop_hiding,vel,mean_speed = get_stats(a,x_win,y_win)
        areas[z].append(hiding_time)
        print(z,':',prop_hiding)
    print('mean speed:',mean_speed)

    if False:
        for b in range(10):

            b0 = window * b
            b1 = b0 + window
            _1,sub_hiding,_2,sub_mean = get_stats(a[b0:b1],x_win,y_win)
            speed_list[b] = sub_mean
            hide_list[b] = sub_hiding
        print(np.mean(speed_list),np.std(speed_list),np.mean(hide_list),np.std(hide_list))

path = '/home/ammon/Documents/Scripts/FishTrack/working_dir/tmp/'
base_cor = (0,0,255)

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
            fish_color = (0,0,255)
            for z in areas.keys():
                x_win,y_win = areas[z][0]
                hiding_time = areas[z][2]
                box_color = np.array(areas[z][1]) // 2
                box_color = box_color.tolist()
                if hiding_time[t]:
                    fish_color = np.array(areas[z][1]).tolist()
                    box_color = fish_color
                #box_color = box_color.astype(int)
                cv2.rectangle(frame,(x_win[0],y_win[0]),(x_win[1],y_win[1]),color=box_color,thickness = 4)
            for l in range(0,min(t,tail_length)):
                r = max(2,rad-l)
                cv2.circle(frame,(a[t-l,0],a[t-l,1]),radius=r,color=fish_color, thickness=-1)
                speed = str(vel[t]) + ' cm/s'
                cv2.putText(frame,speed,(225,25),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)
            num = f'{t:05d}'
            img_name = path + 'Frame_'+ num + '.png'
            #print(img_name)
            if t % 20 == 0 or FULL:
                cv2.imwrite(img_name,frame)
            t += 1

            if PLOT:
                cv2.imshow('Frame',frame)
                key = cv2.waitKey(1)
                if key == ord('q'):
                    break
            if t > (20*60) and FULL:
                break
        else:
            break

    cap.release()
    cv2.destroyAllWindows()

    if not PLOT:
        if FULL:
            command = f'ffmpeg -r 60 -f image2 -i /home/ammon/Documents/Scripts/FishTrack/working_dir/tmp/Frame_%*.png -vcodec libx264 -crf 20 -pix_fmt yuv420p {out_file} -y'
        else:
            command = f'ffmpeg -r 20 -f image2 -i /home/ammon/Documents/Scripts/FishTrack/working_dir/tmp/Frame_%*.png -vcodec libx264 -crf 20 -pix_fmt yuv420p {out_file} -y'

        subprocess.call(command,shell=True)

    print('Deleting imgs')
    command2 = f'rm /home/ammon/Documents/Scripts/FishTrack/working_dir/tmp/*.png'
    subprocess.call(command2,shell=True)
print('Done-zo!')


