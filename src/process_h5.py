import h5py
import sys
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

from tqdm import tqdm 
import argparse

from matplotlib import pyplot as plt

CENTER = [175,203]

def get_quadrant(xy_point,center_point = CENTER):
    x,y = xy_point
    x0,y0 = center_point
    if x <= x0:
        if y <= y0:
            f_loc = 0
        else:
            f_loc = 2
    else:
        if y <= y0:
            f_loc = 1
        else:
            f_loc = 3
    return f_loc

def build_parse():
    parser = argparse.ArgumentParser(description='Required and additional inputs')
    parser.add_argument('--in_file','-i',required=True,help='Path to input .h5 file, output from SLEAP')
    parser.add_argument('--out_file','-o',required=False,help='Path to csv output, if not specified, just uses existing filename')
    parser.add_argument('--center_list','-x',required=False,help='Optional center_dict to define central point')
    parser.add_argument('--id','-c',required=False,help='Camera id, required if using the defined center points')
    parser.add_argument('--n_fish','-n',required=False,help='Number of fish, defaults to 4')
    parser.add_argument('--quadrants','-q',required=False,help='List of quadrants (left to right, top down) where fish are, i.e. [0,1,3]')
    parser.add_argument('--visualize','-v',action='store_true',help='Visualize plot, defaults to False')
    parser.add_argument('--dump','-d',action='store_true',help='Debug option to prevent saving output')
    return parser.parse_args()

## Input: Takes a track (1 fish, all nodes, all frames)
## Output: returns smooth velocity for that fish.
def smooth_diff(track,win=25,poly=3):
    clean_track = track[~np.isnan(track[:,0])]
    if len(clean_track) < 25:
        return 0
    node_loc_vel = np.zeros_like(clean_track)
    simple_diff = np.diff(track,axis=0)
## Get velocities for each dimension
    for c in range(track.shape[-1]):
        node_loc_vel[:,c] = savgol_filter(clean_track[:,c],win,poly,deriv=1)
# Get normal velocity using all nodes

    node_vel = np.linalg.norm(node_loc_vel,axis=1) 
## This simple velocity should probably be smoothed still, I don't love the way this works...
    simple_vel = np.linalg.norm(simple_diff,axis=1)
    return simple_vel

args = build_parse()

if args.out_file is None:
    out_file = args.in_file.replace('.h5','.csv')
else:
    out_file = args.out_file
with h5py.File(args.in_file, 'r') as f:
    dset_names = list(f.keys())
    locations = f['tracks'][:].T
    node_names = [n.decode() for n in f["node_names"][:]]
    track_occupancy = f['track_occupancy'][:].T


if args.n_fish == None:
    n_fish = 4
else:
    n_fish = args.n_fish

center_point = None
if args.center_list == None or args.id == None:
    print('no center point given, using default:',CENTER)
    center_point = CENTER
else:
    crop_dict = {}
    with open(args.center_list) as f:
        for line in f:
            k,cs = line.split()
            if k == args.id:
                center_point = [int(c) for c in cs.split(',')]
                break
if center_point is None:
    print('could not find center point, using default')
    center_point = CENTER

print('using center point:',center_point)
n_frames = len(locations)
n_tracks = np.shape(locations)[3]
n_nodes = len(node_names)

## Create an stacked array for all the tracks
## This can't be this big, it breaks.

cleaned_tracks = np.full([n_fish,n_frames,n_nodes,2],np.nan)

error_count = 0
#for t in tqdm(range(n_tracks)):
for t in range(n_tracks):
    split_track = False
    frames = track_occupancy[t] == 1 ## Needs to do the bool here.
    track = locations[frames,:,:,t]
    max_points = np.nanmax(track,axis=(0,1)) ## get x,y mead of tracklet 
    min_points = np.nanmin(track,axis=(0,1))
    #print(mean_points)
    if min_points[0] <= center_point[0] and max_points[0] <= center_point[0]: ## on left side
        if min_points[1] <= center_point[1] and max_points[1] <= center_point[1]: ## on the top half
            f_loc = 0
        elif min_points[1] > center_point[1] and max_points[1] > center_point[1]: ## on the top half
            f_loc = 2
        else:
            #print('oops:',t,np.argmax(frames),min_points,max_points)
            error_count += 1
            split_track=True
    elif min_points[0] > center_point[0] and max_points[0] > center_point[0]: ## on left side
        if min_points[1] <= center_point[1] and max_points[1] <= center_point[1]: ## on the top half
            f_loc = 1
        elif min_points[1] > center_point[1] and max_points[1] > center_point[1]: ## on the top half
            f_loc = 3
        else:
            #print('oops:',t,np.argmax(frames),min_points,max_points)
            error_count += 1
            split_track=True
    else:
        #print('oops:',t,np.argmax(frames),min_points,max_points)
        error_count += 1
        split_track=True
    if split_track:
        #print('track split: manually assigning points')
        for f in np.arange(n_frames)[frames]:
            f_loc = get_quadrant(np.nanmean(locations[f,:,:,t],axis=0),center_point)
            cleaned_tracks[f_loc,f,:,:] = locations[f,:,:,t]
    else:
        cleaned_tracks[f_loc,frames,:,:] = locations[frames,:,:,t]
    #print(locations[frames,:,:,t])

## Average all overlapping tracks (there shouldn't be many)
## This should get it by fish
#print('averaging tracks')
#print('this could take a minute:',cleaned_tracks.shape)
#averaged_tracks = np.nanmean(cleaned_tracks,axis=4)

#print(averaged_tracks.shape)

fig,ax = plt.subplots()

print('error count:',error_count,'of',n_frames)
visible_frames = np.zeros(n_fish)
proportion_visible = np.zeros(n_fish)
velocities = []
center_ratio = []
for f in range(n_fish):
    ax.scatter(cleaned_tracks[f,:,4,0],400-cleaned_tracks[f,:,4,1],alpha=.05,marker='.')
    #ax.plot(cleaned_tracks[f,:,4,0],400-cleaned_tracks[f,:,4,1],alpha=.1)
    n_vis = np.sum(~np.isnan(cleaned_tracks[f,:,0,0]))
    visible_frames[f] = n_vis
    proportion_visible[f] = n_vis / n_frames
    velocity = smooth_diff(cleaned_tracks[f,:,0])
    median_velocity = np.nanmedian(velocity)
    velocities.append(median_velocity)

    visible_track = cleaned_tracks[f,:,4][~np.isnan(cleaned_tracks[f,:,4,0])]
    xs = np.abs(visible_track[:,0] - center_point[0]) < 30
    ys = np.abs(visible_track[:,1] - center_point[1]) < 30
    courage_count = np.sum(np.logical_or(xs,ys))
    courage_ratio = courage_count / len(visible_track)
    center_ratio.append(courage_ratio)

print(':: STATS ::')
print('proportion visible:',proportion_visible)
print('mean velocity:',velocities)
print('proportion away from edge:',center_ratio)

if args.visualize:
    fig.show()
    plt.show()

if not args.dump:
    fig.savefig(out_file.replace('.csv','.png'),dpi=300)

    np.save(out_file.replace('.csv','.npy'),cleaned_tracks)

    with open(out_file.replace('.csv','.txt'),'w') as f:
        f.write(':: STATS ::')
        f.write('\nproportion visible: ' + str(np.round(proportion_visible,3)))
        f.write('\nmean velocity: ' + str(np.round(velocities,3)))
        f.write('\nproportion away from edge: ' + str(np.round(center_ratio,3)))
    columns = ['Frame','Fish','x','y']
    frame_list,fish_list,x_list,y_list = [],[],[],[]
    for f in range(n_fish):
        frame_list.extend(list(range(n_frames)))
        fish_list.extend([str(f)] * n_frames)
        x_list.extend(cleaned_tracks[f,:,4,0])
        y_list.extend(cleaned_tracks[f,:,4,1])
        
    df = pd.DataFrame(list(zip(frame_list,fish_list,x_list,y_list)),columns=columns)
    df.to_csv(out_file,index=False)
