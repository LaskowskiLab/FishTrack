import h5py
import sys
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

from tqdm import tqdm 
import argparse

from matplotlib import pyplot as plt

## Code which takes .h5 files (output from SLEAP) and processes it to usable data
## This code assumes you have ONE TANK and ONE FISH
## If you have more than that, you should be using a different script.

def build_parse():
    parser = argparse.ArgumentParser(description='Required and additional inputs')
    parser.add_argument('--in_file','-i',required=True,help='Path to input .h5 file, output from SLEAP')
    parser.add_argument('--out_file','-o',required=False,help='Path to csv output, if not specified, just uses existing filename')
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


n_fish = 1

n_frames = len(locations)
n_tracks = np.shape(locations)[3] ## Ideally this would be one
n_nodes = len(node_names)

## Create an stacked array for all the tracks
## This can't be this big, it breaks.

cleaned_tracks = np.full([n_frames,n_nodes,2],np.nan)

error_count = 0
#for t in tqdm(range(n_tracks)):
for t in range(n_tracks):
    split_track = False
    frames = track_occupancy[t] == 1 ## Needs to do the bool here.
    track = locations[frames,:,:,t]
    cleaned_tracks[frames] = track
## Average all overlapping tracks (there shouldn't be many)
## This should get it by fish
#print('averaging tracks')
#print('this could take a minute:',cleaned_tracks.shape)
#averaged_tracks = np.nanmean(cleaned_tracks,axis=4)

#print(averaged_tracks.shape)

fig,ax = plt.subplots()

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
