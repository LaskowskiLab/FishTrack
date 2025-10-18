import h5py
import sys
import numpy as np
import pandas as pd
import cv2
from scipy.signal import savgol_filter

from tqdm import tqdm 
import argparse
import parse_sleap

from matplotlib import pyplot as plt

#CENTER = [349,425]
CENTER = [440,515]
#CENTER = [400,450]

## Code which takes .h5 files (output from SLEAP) and processes it to usable data

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
    parser.add_argument('--project_csv','-p',required=False,help='Path to a project csv where all the summary statistics will be written')
    return parser.parse_args()

## Input: Takes a track (1 fish, all nodes, all frames)
## Output: returns smooth velocity for that fish.
def get_velocity(track,win=25,poly=3):
    clean_track = track[~np.isnan(track[:,0])]
    if len(clean_track) < 25:
        return 0
    node_loc_vel = np.zeros_like(clean_track)
    simple_diff = np.diff(track,axis=0)
## Get velocities for each dimension
    simple_vel = np.linalg.norm(simple_diff,axis=1)
    return simple_vel

## Read through all the frames in a track and allocate them to correct quadrants
def correct_track(locations,track_occupancy,instance_scores,t,center_point=CENTER):
    frames = track_occupancy[t] == 1
    n_frames,n_nodes,_,n_tracks = locations.shape

    track = np.nanmedian(locations[:,:,:,t],axis=1)
    med_point = np.nanmedian(track,axis=0)
    primary_loc = get_quadrant(med_point,center_point)
    new_occupancy = np.zeros([4,n_frames])
    new_scores = np.full([n_frames,4],np.nan)

    new_quads = np.full_like(new_occupancy,np.nan)

    new_locations = np.full([n_frames,n_nodes,2,4],np.nan)
    for f_ in np.argwhere(frames)[:,0]:
        f_loc = get_quadrant(track[f_,:],center_point)
        if f_loc != primary_loc:
            new_quads[f_loc,f_] = f_loc
            new_occupancy[f_loc,f_] = 1
            new_scores[f_,f_loc] = instance_scores[f_,t]
            new_locations[f_,:,:,f_loc] = locations[f_,:,:,t]

            locations[f_,:,:,t] = np.nan
            track_occupancy[t,f_] = 0
            instance_scores[f_,t] = np.nan
    not_0 = np.sum(new_occupancy,axis=1) != 0
    new_locations = new_locations[:,:,:,not_0]
    new_occupancy = new_occupancy[not_0,:]
    new_scores = new_scores[:,not_0]
    new_quads = new_quads[not_0,:]
    return new_locations,new_occupancy,new_scores,primary_loc,new_quads


## This assigns tracks to a unique quadrant. If possibe
###  If tracks are split across 2-4 quads, it divides them and adds new tracks
def track_to_quad(locations,track_occupancy,instance_scores,center_point = CENTER):
    n_tracks = np.shape(locations)[3]
    n_frames = np.shape(locations)[0]
    track_quad = []
    all_quads = []
    quad_array = np.full(np.shape(track_occupancy),np.nan)
    all_quad_arrays = np.empty([0,n_frames])

## I make these because I'm going to be editing them in a function later
    all_locations = np.array(locations)
    all_occupancy = np.array(track_occupancy)
    all_instance_scores = np.array(instance_scores)
    for t in range(n_tracks):
        frames = track_occupancy[t] == 1 ## Needs to do the bool here.
        track = locations[frames,:,:,t]
         
        med_track = np.nanmedian(track,axis=1)
        max_points = np.nanmax(med_track,0) ## get x,y mead of tracklet 
        min_points = np.nanmin(med_track,0)

        loc_min = get_quadrant(min_points,center_point)
        loc_max = get_quadrant(max_points,center_point)

        if loc_min == loc_max:
            f_loc = loc_min
        else:
            # this track is in two places, that's trouble. 

## Note, I am deleting the overlap within the function
            new_locations,new_occupancy,new_instance_scores,f_loc,new_quad_array = correct_track(locations,track_occupancy,instance_scores,t,center_point)
            all_locations = np.concatenate([all_locations,new_locations],axis=3)
            all_occupancy = np.concatenate([all_occupancy,new_occupancy],axis=0).astype(bool)
            all_instance_scores = np.concatenate([all_instance_scores,new_instance_scores],axis=1)

            all_quad_arrays = np.concatenate([all_quad_arrays,new_quad_array],axis=0)
            all_quads.extend(np.nanmin(new_quad_array,1).astype(int))
        #f_loc = get_quadrant(np.nanmean(track,axis=(0,1)),center_point)
            #import pdb;pdb.set_trace() 

        quad_array[t,track_occupancy[t]] = f_loc
        track_quad.append(f_loc)
    track_quad.extend(all_quads)
    #import pdb;pdb.set_trace()
    return track_quad, quad_array,[all_locations,all_occupancy,all_instance_scores]

def simple_quadrants(locations,track_occupancy,instance_scores,center = CENTER):
    locations = np.array(locations)
    if len(locations.shape) == 4:
        locations = np.nanmean(locations,1)

    n_frames,_,n_tracks = locations.shape

    locations_ = np.moveaxis(locations,[2],[1])

    quad_locations = np.full([4,n_frames,n_tracks,2],np.nan)
    quad_occupancy = np.full([4,n_tracks,n_frames],np.nan) ## These are different, it sucks.
    quad_scores = np.full([4,n_frames,n_tracks],np.nan)

    quad_0 = np.argwhere((locations_[:,:,0] <= center[0]) & (locations_[:,:,1] <= center[1]))
    quad_1 = np.argwhere((locations_[:,:,0] >  center[0]) & (locations_[:,:,1] <= center[1]))
    quad_2 = np.argwhere((locations_[:,:,0] <= center[0]) & (locations_[:,:,1] >  center[1]))
    quad_3 = np.argwhere((locations_[:,:,0] >  center[0]) & (locations_[:,:,1] >  center[1]))
    q_indices = [quad_0,quad_1,quad_2,quad_3]
## This is a bit tricky, argwhere returns a list of index tuples, this takes all of them along the proper axes
    for q in range(4):
        indices = q_indices[q]
        quad_locations[q,indices[:,0],indices[:,1]] = locations_[indices[:,0],indices[:,1]]
        quad_occupancy[q,indices[:,1],indices[:,0]] = track_occupancy[indices[:,1],indices[:,0]]
        quad_scores[q,indices[:,0],indices[:,1]] = instance_scores[indices[:,0],indices[:,1]]

    quad_locations = np.moveaxis(quad_locations,[3],[2])
    return quad_locations,quad_occupancy,quad_scores

def quadle_neck(locations,track_occupancy,instance_scores,center_point = CENTER):
    track_quad,quad_array,cleaned_data = track_to_quad(locations,track_occupancy,instance_scores,center_point) 
    locations,track_occupancy,instance_scores = cleaned_data
    n_tracks = np.shape(locations)[3]
    #import pdb;pdb.set_trace()
    for t in range(n_tracks): 
        frames = track_occupancy[t] == 1
        overlap_array = quad_array[:,frames] == track_quad[t]
        competing_ts = np.nansum(overlap_array,axis = 0)
        #print(competing_ts)
        if len(competing_ts) == 0: ## This can happen if it was deleted in a prior loop
            continue

        if np.nanmax(competing_ts) > 1:
            for f in np.argwhere(competing_ts > 1)[:,0]:
                t_score = instance_scores[f,t]
                competitors = np.argwhere(overlap_array[:,f])[:,0]
                for c_ in competitors:
                    if c_ == t:
                        continue
                    c_score = np.nanmean(instance_scores[:,c_])
                    if t_score > c_score:
                        track_occupancy[c_,f] = 0 ## or nan?
                        #track_occupancy[t_,frames] = 0 ## or nan?
                    elif t_score < c_score: ## if that track is better, delete this I guess? 
                        track_occupancy[t,f] = 0
                        #track_occupancy[t_,frames] = 0 ## or nan?
    return locations,track_occupancy,instance_scores

if __name__ == "__main__":
    args = build_parse()

    if args.out_file is None:
        out_file = args.in_file.replace('.h5','.npy')
    else:
        out_file = args.out_file
    with h5py.File(args.in_file, 'r') as f:
        dset_names = list(f.keys())
        locations = f['tracks'][:].T
        node_names = [n.decode() for n in f["node_names"][:]]
        track_occupancy = f['track_occupancy'][:].T
        video_path = str(f['video_path'][()])[2:-1]
        instance_scores = f['instance_scores'][:].T

    if args.n_fish == None:
        n_fish = 4
    else:
        n_fish = args.n_fish

    center_point = None
    if args.center_list == None:
        print('no center dict given..')
        try:
            print('trying to check from h5 source video:')
            cap = cv2.VideoCapture(video_path)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            cap.release()
            center_point = [width //2, height//2]
            center_point = CENTER
        except:
            print('Nevermind, using default:',CENTER)
            center_point = CENTER
    else:
        print('crop dict found, checking for key')
        crop_dict = {}
        with open(args.center_list) as f:
            for line in f:
                k,cs = line.split()
                if k == args.id or k in args.in_file:
                    center_point = [int(c) for c in cs.split(',')]
                    break
                else:
                    center_point = CENTER   
    CENTER = center_point

    print('using center point:',center_point)

## Create an stacked array for all the tracks

    #import pdb;pdb.set_trace()
## This actually reshapes locations and track_occupancy
    #locations_1,track_occupancy_1,instance_scores_1 = quadle_neck(np.array(locations),np.array(track_occupancy,dtype=bool),instance_scores,center_point)


    if True:
        quad_locations,quad_occupancy,quad_scores = simple_quadrants(np.array(locations),np.array(track_occupancy,dtype=bool),instance_scores,center_point)

        n_frames = len(locations)

        clean_quad_tracks = np.full([4,n_frames,2],np.nan)
        for f in range(n_fish):
            clean_quad_tracks[f],_ = parse_sleap.simply_flatten(quad_locations[f], quad_occupancy[f],quad_scores[f])

    else:
        locations_0,track_occupancy_0,instance_scores_0 = locations,track_occupancy,instance_scores

        locations,track_occupancy,instance_scores = locations_1,track_occupancy_1,instance_scores_1

        error_count = 0

        n_frames = len(locations)
        n_tracks = np.shape(locations)[3]
        n_nodes = len(node_names)

        cleaned_tracks = np.full([n_fish,n_frames,n_nodes,2],np.nan)
#for t in tqdm(range(n_tracks)):
        print('dividing tracks into quadrants')
        print('center point:',center_point)

        for t in range(n_tracks):
            split_track = False
            frames = track_occupancy[t] == 1 ## Needs to do the bool here.
            if np.sum(frames) == 0: ## this occurs when it's been cleaned by above process
                continue
            track = locations[frames,:,:,t]

            med_track = np.nanmedian(track,axis=1)
            max_points = np.nanmax(med_track,0) ## get x,y mead of tracklet 
            min_points = np.nanmin(med_track,0)

            loc_min = get_quadrant(min_points,center_point)
            loc_max = get_quadrant(max_points,center_point)

            #print(min_points,max_points)
            #print(loc_min,loc_max)

            if loc_min == loc_max:
                f_loc = loc_min
                cleaned_tracks[f_loc,frames,:,:] = locations[frames,:,:,t]
            else: ## if the track enteres two different quadrants, it's probably two different fish
                error_count += 1
## This approach is ok, but it will just keep whichever track comes second
                #continue
                for f in np.arange(n_frames)[frames]:
                    f_loc = get_quadrant(np.nanmean(locations[f,:,:,t],axis=0),center_point)
                    cleaned_tracks[f_loc,f,:,:] = locations[f,:,:,t]

        clean_quad_tracks = np.full([4,n_frames,2],np.nan)

        print('clearing peaks, and flattening to 4 tracks')
        for f in range(n_fish):
            clean_quad_tracks[f] = parse_sleap.simply_flatten(cleaned_tracks[f], track_occupancy,instance_scores)

    print('Writing output: ',np.shape(clean_quad_tracks))

    if not args.dump:
        np.save(out_file,clean_quad_tracks)

    if args.visualize:
        fig,ax = plt.subplots()
        for f in range(n_fish):
            ax.scatter(clean_quad_tracks[f,:,0],clean_quad_tracks[f,:,1],alpha=0.01)
        plt.show()

