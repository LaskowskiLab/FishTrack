import h5py
import numpy as np
import parse_trex

from tqdm import tqdm

#in_file = '/home/ammon/Downloads/TEST_Labels.002_Pool2Test2.analysis.h5' 
in_file = '/home/ammon/Documents/Scripts/FishTrack/sleap/kirsten_demo.trackattempt.h5'
with h5py.File(in_file, 'r') as f:
    dset_names = list(f.keys())
    locations = f['tracks'][:].T
    node_names = [n.decode() for n in f["node_names"][:]]
    track_occupancy = f['track_occupancy'][:].T
"""
print(locations.shape)
print(node_names)
print(track_occupancy.shape)
print(np.unique(track_occupancy))
print(track_occupancy[0,:50])

print(locations[:50,3,:,0])
"""
track_array = locations[:,3,:,0]

n_fish = 5
n_frames = locations.shape[0]
n_tracklets = locations.shape[3]

matched_tracks = np.empty([n_fish,n_frames,2])
matched_tracks.fill(np.nan)

trailing_points = np.empty([n_fish,2])
trailing_frames = np.empty(n_fish)

trailing_points.fill(np.nan)
trailing_frames.fill(np.nan)
## Greedy and naive approach
for t_ in range(n_tracklets):
    #good_frames = ~np.isnan(track_occupancy[t_])
    good_frames = track_occupancy[t_]
    #good_locations = locations[good_frames,:,:,t_]
    tracklet_x = np.nanmean(locations[good_frames==1,:,0,t_],axis=1) 
    tracklet_y = np.nanmean(locations[good_frames==1,:,1,t_],axis=1)
    tracklet = np.array([tracklet_x,tracklet_y])

    f0 = np.argmax(good_frames)
    fmax = f0 + len(tracklet_x)
    x0,y0 = tracklet_x[0],tracklet_y[0]
    open_lanes = np.isnan(matched_tracks[:,f0,0])
    #print('working on track #',t_)
    #print('open lanes:',open_lanes)
    #print('trailing frames:',trailing_frames)
    #print('railing_points:',trailing_points)
    if np.sum(open_lanes) == 0:
        print('No space??')
        import pdb;pdb.set_trace()
    elif np.sum(open_lanes) == 1:
        lane = np.argmax(open_lanes)
        #print('Only one spot, adding')
        matched_tracks[lane,f0:fmax,0] = tracklet_x
        matched_tracks[lane,f0:fmax,1] = tracklet_y
        trailing_points[lane] = tracklet_x[-1],tracklet_y[-1]
    elif np.sum(open_lanes) > 0:
        #print('More than one, choosing best lane')
        distances = np.array([np.linalg.norm(tracklet[:,0] - l) for l in trailing_points])
        vels = distances / (f0 - trailing_frames)

        distances[open_lanes == False] = np.inf
        vels[open_lanes == False] = np.inf

        #print(distances)
        #print(vels)

        best_lane = np.argmin(vels) ##conveniently, nan is lower than 0
        #best_lane = np.argmin(distances) # Not sure which is better...

        jump = distances[best_lane]
        vel = vels[best_lane]

        #import pdb;pdb.set_trace()
        #print(f0,fmax)
        matched_tracks[best_lane,f0:fmax,0] = tracklet_x
        matched_tracks[best_lane,f0:fmax,1] = tracklet_y
        trailing_frames[best_lane] = fmax
        trailing_points[best_lane] = [tracklet_x[-1],tracklet_y[-1]]
        #print(best_lane,jump,vel)
    

np.save('matched_tracks.npy',matched_tracks)
#import pdb;pdb.set_trace()

print('done?')
