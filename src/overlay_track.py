import parse_sleap
import numpy as np
from matplotlib import pyplot as plt
import cv2
import subprocess
import sys
import h5py
import argparse

#file_object = np.load('/home/ammon/Videos/data/pi13.2022.10.30.batch.trex.crop_3_fish0.npz')
#vid_name = '/home/ammon/Videos/babies/singles/pi13.2022.10.30.batch.trex.crop_3.mp4'

def build_parse():
    parser = argparse.ArgumentParser(description='Required and optional inputs')
    parser.add_argument('--vid_file','-i',required=True,help='Path to input .mp4 video')
    parser.add_argument('--tracks','-t',required=True,help='Path to track, either .h5 or .npy')
    parser.add_argument('--visualize','-v',action='store_true',help='Show video?')
    parser.add_argument('--dump','-d',action='store_true',help='Trash output?')
    parser.add_argument('--output','-o',required=False,help='Path to output video')
    parser.add_argument('--other_track','-b',required=False,help='Second array of tracks to plot, very niche')
    parser.add_argument('--third_track','-c',required=False,help='Third array of tracks to plot, even more niche')
    return parser.parse_args()

## Take an array and clean out single points, then interpolate
def clean_track(a):

    a = parse_sleap.clear_peaks(a)
    clean_xs = parse_sleap.clear_lone_points(a[:,0])
    clean_ys = parse_sleap.clear_lone_points(a[:,1])
    b = np.empty_like(a)
    b[:,0] = clean_xs
    b[:,1] = clean_ys
    b = parse_sleap.clear_teleports(b)

    smooth_b = np.empty_like(b)
    smooth_b[:,0] = parse_sleap.interp_track(b[:,0])
    smooth_b[:,1] = parse_sleap.interp_track(b[:,1])

    smooth_xs = smooth_b[:,0]
    smooth_ys = smooth_b[:,1]

    return smooth_b


#npz_name = npz_name.replace('/babies/singles','/data')
#file_object = np.load(h5_name)
#out_file = '/home/ammon/Videos/babies/singles/pi13.2022.10.30.batch.trex.crop_3.tracked.mp4'

args = build_parse()

if args.output is None:
    args.output = args.vid_file.replace('.mp4','tracked.mp4')

out_file = args.output
#out_file = vid_name.replace('.mp4','.tracked.mp4')

if '.h5' in args.vid_file:
    with h5py.File(args.tracks, 'r') as f:
        dset_names = list(f.keys())
        locations = f['tracks'][:].T
        node_names = [n.decode() for n in f["node_names"][:]]
        track_occupancy = f['track_occupancy'][:].T
    a = locations ## Really not sure if that works...

elif '.npy' in args.tracks:
    a = np.load(args.tracks)

print(a.shape)

if args.other_track is not None:
    b = np.load(args.other_track)
else:
    b = None

if args.third_track is not None:
    c = np.load(args.third_track)
else:
    c = None
## Clean up and interpolate tracks

## Probably need a c here too
if b is not None:
    b[np.isnan(b)] = 0

    if len(b.shape) == 2:
        b = b.reshape([1,len(b),2])
    b = b.astype(int)

if c is not None:
    c[np.isnan(c)] = 0

    if len(c.shape) == 2:
        c = c.reshape([1,len(c),2])
    c = c.astype(int)

if len(a.shape) == 2:
    n_fish = 1
    a = a.reshape([1,len(a),2])
else:
    n_fish = np.shape(a)[0]
    a = np.nanmean(a,axis=2)

if n_fish > 1:
    for f in range(n_fish):
        #a[f] = clean_track(a[f])
        pass

a = a.astype(int)
## Make video:
cap = cv2.VideoCapture(args.vid_file)
fps = int(cap.get(cv2.CAP_PROP_FPS))
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')

a = np.clip(a,0,max(frame_width,frame_height))

if not args.dump:
    out = cv2.VideoWriter(args.output,fourcc,fps, (frame_width,frame_height),isColor=True)

fish_colors = [(0,0,255),(255,255,0),(0,255,255),(255,0,255)]
tail_length = 10

t=0
print('Working on it...')

print(a.shape,b.shape,c.shape)
while(cap.isOpened()):
    ret, frame = cap.read()
    rad = 5
    if not ret:
        break
    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

    for f in range(n_fish):
        if np.isnan(a[f,t,0]) or np.isnan(a[f,t,0]):
            continue
        cor = fish_colors[f]
        cv2.circle(frame,(a[f,t,0],a[f,t,1]),radius=rad,color=cor,thickness=-1)

        for l in range(0,min(t,tail_length)):
            r = max(2,rad-l)
            cv2.circle(frame,(a[f,t-l,0],a[f,t-l,1]),radius=r,color=cor,thickness=-1)
        if b is not None:
            cv2.circle(frame,(b[f,t,0],b[f,t,1]),radius=rad-1,color=[0,255,0],thickness=-1)
        if c is not None:
            cv2.circle(frame,(c[f,t,0],c[f,t,1]),radius=rad-1,color=[255,0,0],thickness=-1)
    if args.visualize:
        cv2.imshow('Overlay',frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            args.visualize = False

    if not args.dump:
        out.write(frame)

    t += 1

if not args.dump:
    out.release()

cap.release()
cv2.destroyAllWindows

print('All done! Check out:',args.output)
