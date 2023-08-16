import h5py
import sys
import numpy as np
import pandas as pd
import cv2
from scipy.signal import savgol_filter

from tqdm import tqdm 
import argparse

from matplotlib import pyplot as plt

CENTER = [349,425]
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
    parser.add_argument('--spots','-f',required=False,help='Path to mp4 of spotlighted video from spotlight.py')
    parser.add_argument('--project_csv','-p',required=False,help='Path to a project csv where all the summary statistics will be written')
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

## You know, like a quadrant bottle neck
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

## Only keep frames that overlap with background subtraction.
def spot_filter(locations,track_occupancy,spot_file):
    cap = cv2.VideoCapture(spot_file)

    n_tracks = np.shape(locations)[3]
    for t in range(n_tracks): 
        frames = track_occupancy[t] == 1
        f_start = np.argmax(frames) + 1
         
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_start-1)
        n_frames = sum(frames)
        score = np.zeros(n_frames)
        f_index = f_start
        count = 1
        while count < n_frames:
            ret,frame = cap.read() 
            if not ret:
                break
            if frames[f_index] == False:
                f_index += 1
                continue
            x,y = np.nanmedian(locations[f_index,:,:,t],axis=0).astype(int)
            if frame[y,x,0] == 0: 
                #print('found 0')
                if np.sum(frame[y-10:y+10,x-10:x+10,0]) == 0: ### Row column notation
                    #print('deleting:',t,f_index,frame[y,x])
                    track_occupancy[t,f_index] = 0 ## Just delete that frame
            f_index += 1
            count += 1
        #print(t,np.mean(score))
        #if np.mean(score) < 0.25:
        #    track_occupancy[t] = 0
    cap.release()
    return locations,track_occupancy

if __name__ == "__main__":
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
## This can't be this big, it breaks.

    print('clearing overlapping tracks')
## This actually reshapes locations and track_occupancy
    locations_1,track_occupancy_1,instance_scores_1 = quadle_neck(np.array(locations),np.array(track_occupancy,dtype=bool),instance_scores,center_point)
    locations_0,track_occupancy_0,instance_scores_0 = locations,track_occupancy,instance_scores
    locations,track_occupancy,instance_scores = locations_1,track_occupancy_1,instance_scores_1

    print('running spot filter')
    if args.spots is not None:
        locations_2,track_occupancy_2 = spot_filter(np.array(locations_1),np.array(track_occupancy_1),args.spots)
        locations,track_occupancy = locations_2,track_occupancy_2
    #import pdb;pdb.set_trace()

    error_count = 0

    n_frames = len(locations)
    n_tracks = np.shape(locations)[3]
    n_nodes = len(node_names)

    cleaned_tracks = np.full([n_fish,n_frames,n_nodes,2],np.nan)
#for t in tqdm(range(n_tracks)):
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
    activities = []
    corner_ratios = []
    y_max = np.nanmax(cleaned_tracks[:,:,:,1])
    ax.axvline(CENTER[0],color='black')
    ax.axhline(CENTER[1],color='black')
    cleaned_med = np.nanmedian(cleaned_tracks,axis=2)
    for f in range(n_fish):
        #ax.scatter(cleaned_tracks[f,:,4,0],y_max - cleaned_tracks[f,:,4,1],alpha=.05,marker='.')
        #ax.scatter(cleaned_med[f,:,0],y_max - cleaned_med[f,:,1],alpha=.05,marker='.')
        ax.scatter(cleaned_med[f,:,0],cleaned_med[f,:,1],alpha=.01,marker='.')
        n_vis = np.sum(~np.isnan(cleaned_tracks[f,:,0,0]))
        visible_frames[f] = n_vis
        proportion_visible[f] = n_vis / n_frames

        velocity = smooth_diff(cleaned_tracks[f,:,0])
        median_velocity = np.nanmedian(velocity)
        velocities.append(median_velocity)

        prop_active = np.nansum(velocity > 5) / np.sum(~np.isnan(velocity))
        activities.append(prop_active)
        visible_track = cleaned_tracks[f,:,4][~np.isnan(cleaned_tracks[f,:,4,0])]

        xs = np.abs(visible_track[:,0] - center_point[0]) > 100 #center_point[0]/2
        ys = np.abs(visible_track[:,1] - center_point[1]) > 200 #center_point[1]/2
        coward_count = np.sum(np.logical_and(xs,ys))
        coward_ratio = coward_count / len(visible_track)
        corner_ratios.append(coward_ratio)

    print(':: STATS ::')
    print('proportion visible:',proportion_visible)
    print('mean velocity:',velocities)
    print('proportion in corner:',corner_ratios)

    if args.visualize:
        fig.show()
        plt.gca().invert_yaxis()
        plt.show()

    if not args.dump:
        fig.savefig(out_file.replace('.csv','.png'),dpi=300)

        np.save(out_file.replace('.csv','.npy'),cleaned_tracks)

        with open(out_file.replace('csv','txt'),'w') as f:
            f.write(':: STATS ::')
            f.write('\nproportion visible: ' + str(np.round(proportion_visible,3)))
            f.write('\nmean velocity: ' + str(np.round(velocities,3)))
            f.write('\nproportion away from edge: ' + str(np.round(corner_ratios,3)))
        if args.project_csv is not None:
            #import pdb;pdb.set_trace()
            with open(args.project_csv,'a') as f:
                h5_name = args.in_file.split('/')[-1]
                base_name = h5_name.split('.')[0]
                delim = ','
                for f_ in range(n_fish):
                    quad = str(get_quadrant(np.nanmedian(cleaned_med[f_],axis=0),center_point))
                    prop_visible = str(round(proportion_visible[f_],3))
                    vel = str(round(velocities[f_],3))
                    activity = str(round(activities[f_],3))
                    boldness = str(round(1-corner_ratios[f_],3))
                    f_line = delim.join([base_name,quad,prop_visible,vel,activity,boldness])
                    f.write(f_line + '\n')
        columns = ['Frame','Fish','x','y']
        frame_list,fish_list,x_list,y_list = [],[],[],[]
        for f in range(n_fish):
            frame_list.extend(list(range(n_frames)))
            fish_list.extend([str(f)] * n_frames)
            x_list.extend(cleaned_tracks[f,:,4,0])
            y_list.extend(cleaned_tracks[f,:,4,1])
            
        df = pd.DataFrame(list(zip(frame_list,fish_list,x_list,y_list)),columns=columns)
        df.to_csv(out_file,index=False)
