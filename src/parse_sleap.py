#! /usr/bin/env python

## Code to process the .npz readouts from Trex
## written by Ammon for use in the Laskowski Lab, for questions contact perkes.ammon@gmail.com

import h5py
import numpy as np
import argparse
from matplotlib import pyplot as plt
import parse_sleap

## Build argument parser
def build_parse():
    parser = argparse.ArgumentParser(description='Required and additional inputs')
    parser.add_argument('--input_file','-i',required=True,help='Path to the input file, a .npz')
    parser.add_argument('--output_file','-o',required=False,default=None,help='Path to output, if not specified, goes to the same place as input')
    parser.add_argument('--verbose','-v',required=False,action='store_true',help='use for printing information')
    parser.add_argument('--head','-m',required=False,action='store_true',help='Include header string of meta data')
    parser.add_argument('--showplot','-p',required=False,action='store_true',help='Optionally visualize the plot')
    parser.add_argument('--saveplot','-s',required=False,action='store_true',help='Optionally save the plot')
    return parser.parse_args()

def read_h5(h5_file):
    with h5py.File(h5_file,'r') as f:
        locations = f['tracks'][:].T
        track_occupancy = f['track_occupancy'][:].T
        video_path = str(f['video_path'][()])[2:-1]
        instance_scores = f['instance_scores'][:].T
    return locations,track_occupancy,instance_scores

## Parse the file string to get relevent info. Requires string to be parsed correctly
def get_meta(input_path):
    file_name = input_path.split('/')[-1]
    file_name = file_name.replace('.npz','')
    split_name = file_name.split('.')
    meta_dict = {}
    meta_dict['date'] = str('-'.join(split_name[3:6]))
    meta_dict['tank'] = split_name[0]
    ext_name = split_name[-1]
    meta_dict['fish'] = ext_name.split('_')[-1]

    return meta_dict

## Calculate the stats we want
def get_stats(file_object):
    stat_dict = {}

## Have to remove infinite values (not sure why these exist...)
    speed = file_object['SPEED']
    speed[speed == np.inf] = np.nan
    speed[speed == -np.inf] = np.nan
    stat_dict['mean_speed'] = np.nanmean(speed)
## The rest should be good
    stat_dict['droppped_frames'] = np.sum(file_object['missing'])
    stat_dict['total_frames'] = len(file_object['missing'])
    return stat_dict
    
def plot_array(pos_array):    
    fig,ax = plt.subplots()
    #pos_array[2] = np.nanmax(pos_array[2]) - np.array(pos_array[2])
    ax.scatter(pos_array[1],pos_array[2],alpha=.01,marker='.')
    plt.gca().invert_yaxis()
    return fig,ax

def read_clean_h5(in_file):
    locations,track_occupancy,instance_scores = read_h5(in_file)
    return clean_track(locations,track_occupancy,instance_scores)

## Take a full, raw list of tracks, convert it to cleaned, single track
## This assumes a single fish in a large tank
def clean_track(locations,track_occupancy = None,instance_scores=None,stds=3,min_track=2,max_speed = 200):
    all_tracks = np.array(locations)
    if len(np.shape(all_tracks)) == 4:
        all_tracks = np.nanmean(all_tracks,axis=1) ## compress along nodes if needed
    else:
        all_tracks = np.array(all_tracks)

    if track_occupancy is None:
        track_occupancy = (1- np.isnan(all_tracks[:,0]).T).astype(bool)
    else:
        track_occupancy = np.array(track_occupancy)

    trimmed_tracks,track_occupancy_trim = clear_peaks_all(all_tracks,track_occupancy,plot_me=False,stds=3)

    single_track,single_occupancy = overlay_tracks(trimmed_tracks,track_occupancy_trim,instance_scores,min_track=2)

    slowed_track = clear_superspeed(single_track,max_speed=200)

    clean_track,clean_occupancy = clear_teleports_(slowed_track,max_distance = 300,min_track=2)

    full_track = np.empty_like(clean_track)
    full_track[:,0] = interp_track(clean_track[:,0])
    full_track[:,1] = interp_track(clean_track[:,1])
    return full_track,clean_occupancy

def simply_flatten(locations,track_occupancy = None,instance_scores=None,stds=3,min_track=2):
    all_tracks = np.array(locations)
    track_occupancy = np.array(track_occupancy)
    if len(np.shape(all_tracks)) == 4:
        all_tracks = np.nanmean(all_tracks,axis=1) ## compress along nodes if needed
    else:
        all_tracks = np.array(all_tracks)

    if track_occupancy is None:
        track_occupancy = (1- np.isnan(all_tracks[:,0]).T).astype(bool)
    else:
        track_occupancy = np.array(track_occupancy)

    trimmed_tracks,track_occupancy_trim = clear_peaks_all(all_tracks,track_occupancy,plot_me=False,stds=stds)

    single_track,single_occupancy = overlay_tracks(trimmed_tracks,track_occupancy_trim,instance_scores,min_track=min_track)

    return single_track,single_occupancy 

def clear_lone_points(a):
    a = np.array(a)
    y = np.array(a[1:-1])
    real_points = ~np.isnan(a)
    real_points = real_points.astype(int)
    lone_points = real_points[1:-1] + real_points[:-2] + real_points[2:] == 1
    y[lone_points == 1] = np.nan 
    #import pdb;pdb.set_trace()
    a[1:-1] = y
    return a

## Takes Frames x XY track
def clear_superspeed(a,max_speed = 500):
    a = np.array(a)
    dx = np.abs(np.diff(a[:,0],prepend=0))
    dy = np.abs(np.diff(a[:,1],prepend=0))
    #import pdb;pdb.set_trace()
    a[dx > max_speed] = [np.nan,np.nan]
    a[dy > max_speed] = [np.nan,np.nan]
    return a

## Takes Frames x XY
## This ideally occurs after getting best score, before interp
def clear_teleports_(a,track_occupancy=None,instance_scores=None,max_distance = 300,min_track=2):
    a = np.array(a)
    n_frames = len(a)
    if track_occupancy is None:
        track_occupancy = (1- np.isnan(a[:,0]).T).astype(bool)
    elif len(np.shape(track_occupancy)) > 1:
        track_occupancy = np.max(track_occupancy,axis=0)
    else:
        track_occupancy = np.array(track_occupancy)
    if len(np.shape(a)) > 2:
        a = overlay_tracks(a,track_occupancy,instance_scores)
        track_occupancy = (1- np.isnan(a[:,0]).T).astype(bool)

    #gaps = np.argwhere(track_occupancy == False)[:,0]
    
    start_ = np.argmax(track_occupancy)  ## get's start of first detection
    stop_ = np.argmax(track_occupancy[start_:] == False) + start_ ## Stop of first detection
    next_ = np.argmax(track_occupancy[stop_:] == True) + stop_ ## Get next detection (start of 2nd)
    last_ = stop_ - 1
    
    while start_ < n_frames:
## Lots of opportunities for indexing errors here...
        start_ = next_
        stop_ = np.argmax(track_occupancy[start_:] == False) + start_
        next_ = np.argmax(track_occupancy[stop_:] == True) + stop_
        #print(last_,start_,stop_,next_)
        if stop_ == start_ or stop_ == next_:
            break
        if stop_ - start_ < min_track:
            a[start_:stop_] = np.nan
        last_points = a[last_]
        start_points = a[start_]
        stop_points = a[stop_ - 1]
        next_points = a[next_]
        last_shift = np.linalg.norm(start_points - last_points)
        next_shift = np.linalg.norm(next_points - stop_points)

        #print(start_,':')
        #print(start_points,last_points,last_shift)
        #print(last_shift,next_shift)
        #print('\n')
        if last_shift < max_distance or next_shift < max_distance: ## Could be more clever here...
## If at least one shift is reasonble, keep going
            #print('this one looks good')
            last_ = stop_-1
            #start_ = next_ ## this is already handled
        else: 
## Delete this section
            track_occupancy[start_:stop_] = False
            a[start_:stop_] = np.nan
## Move the pointers
            next_ = np.argmax(track_occupancy[last_+1:] == True) + last_+1
        #import pdb;pdb.set_trace()
# You probably still have the tracks...
    return a,track_occupancy 

## Just another name for overlay tracks, because flatten tracks makes more sense. 
def flatten_tracks(a,track_occupancy=None,instance_scores = None,min_track = 2):
    return overlay_tracks(a,track_occupancy,instance_scores,min_track)

## Takes Frames x XY x Tracks
## Outputs Frames x XY to give you one best track
## The only "smart" thing this does is settles conflicts based on prediction score

def overlay_tracks(a,track_occupancy=None,instance_scores = None,min_track = 2):
    if track_occupancy is None:
        track_occupancy = (1- np.isnan(a[:,0]).T).astype(bool)
    else:
        track_occupancy = np.array(track_occupancy)

    if len(np.shape(a)) == 4:
        a = np.nanmean(a,axis=1) ## compress along nodes if needed
    else:
        a = np.array(a)

    n_tracks = a.shape[2]
    n_frames = a.shape[0]
    single_track = np.empty([n_frames,2])
    single_track.fill(np.nan)
    sum_occupancy = np.sum(track_occupancy,0)
    max_occupancy = np.max(track_occupancy,0)
    for t in range(n_tracks):
        frames = track_occupancy[t] == True
        if len(frames) == 0:
            continue ## this happens when the track is deleted earlier
        if len(frames) < min_track:
            track_occupancy[t,frames] = False
        track = a[frames,:,t] 
        overlapping_frames = sum_occupancy[frames] > 1
        #import pdb; pdb.set_trace()
        if True in overlapping_frames and instance_scores is not None:
            ## We can pick the best frames: 
            frames_to_check = np.argwhere((sum_occupancy > 1) & (frames == 1))[:,0]
            for f in frames_to_check:
                t_score = instance_scores[f,t]
                competitors = np.argwhere(track_occupancy[:,f])[:,0]
                for c_ in competitors:
                    if c_ == t:
                        continue
                    #c_score = np.nanmean(instance_scores[:,c_]) ## mean of entire track
                    c_score = instance_scores[f,c_] ## score at point
                    if t_score > c_score:
                        track_occupancy[c_,f] = False
                    elif t_score < c_score:
                        track_occupancy[t,f] = False
    for t in range(n_tracks):
        frames = track_occupancy[t] == 1
        if len(frames) == 0:
            continue
        else:
            track = a[frames,:,t]
            single_track[frames] = track
    single_occupancy = np.max(track_occupancy,0)
    return single_track,single_occupancy

## Same thing, but for a tank divided in quadrants
def overlay_tracks_quad(a,track_occupancy,instance_scores,center_point):
    print('This does not work yet')
    return 0

def nan_helper(y):
    return np.isnan(y), lambda z: z.nonzero()[0]

def interp_track(a):
    y = np.array(a)
    nans,x = nan_helper(a)
    y[nans]=np.interp(x(nans),x(~nans),y[~nans])
    return y

## Finds and deletes peaks from entire set
def clear_peaks_all(a,track_occupancy,bins=50,stds=1,plot_me=False):
    track_occupancy = np.array(track_occupancy)
    if len(a.shape) == 4: ## In case you pass all the nodes
        a = np.nanmean(a,axis=1)
    a = np.array(a)
    #a_clean = np.nan_to_num(a)
## rearrange this to have a long array of x,y pairs
    a_num = np.moveaxis(a,[1],[2])
    #a_num = np.nan_to_num(a_num)
    a_num_2d = np.reshape(a_num,[-1,2])

## will need these in a bit
    a_x,a_y = a_num[:,:,0],a_num[:,:,1]
    flat_x,flat_y = a_num_2d[:,0],a_num_2d[:,1]

    MAX_COUNT = 4000
    good_points = ~np.isnan(flat_x) & ~np.isnan(flat_y)
    b = a_num_2d[good_points]
    counts,xedges,yedges = np.histogram2d(b[:,0],b[:,1],bins=bins)
    #import pdb;pdb.set_trace()
    sub_counts = counts[counts < MAX_COUNT]
    peaks = np.argwhere(counts > sub_counts.mean() + sub_counts.std() * stds) 
## Set a hard threshold
    hard_peaks = np.argwhere(counts >= MAX_COUNT)
    all_peaks = np.vstack([peaks,hard_peaks])
    #all_peaks = hard_peaks
## Visualize the density, and which ones are clipped
    if plot_me:
        #print(counts.mean() + counts.std()*stds)
        fig,(ax1,ax2) = plt.subplots(2)
        ax1.imshow(counts,vmax=1000)
        ax1.scatter(peaks[:,1],peaks[:,0],color='pink',alpha=0.5,marker='.')
        ax1.scatter(hard_peaks[:,1],hard_peaks[:,0],color='red',alpha=0.5,marker=',')
        #ax1.set_xticklabels(xedges)
        #ax1.set_yticklabels(yedges)

    for p in all_peaks:
        x_,y_ = p
        x0,x1 = xedges[x_],xedges[x_ + 1]
        y0,y1 = yedges[y_],yedges[y_ + 1]
        
        #bad_xspots = np.argwhere((a_x >= x0) & (a_x <= x1))
        #bad_yspots = np.argwhere((a_y >= y0) & (a_y <= y1))
        bad_spots = np.argwhere((a_y >= y0) & (a_y <= y1) & (a_x >= x0) & (a_x <= x1))
        #print(bad_spots)
        #bad_spots = bad_xspots & bad_yspots
        a_num[bad_spots[:,0],bad_spots[:,1]] = np.nan
        track_occupancy[bad_spots[:,1],bad_spots[:,0]] = 0
    if plot_me:
        
        d = np.reshape(a_num,[-1,2])
        good_ds = ~np.isnan(d[:,0])
        d = d[good_ds]
        new_counts,xedges,yedges = np.histogram2d(d[:,0],d[:,1],bins=bins)
        ax2.imshow(new_counts)
        plt.show()

    a = np.moveaxis(a_num,[2],[1])
    #import pdb;pdb.set_trace()
    return a,track_occupancy

## Finds and deletes peaks
def clear_peaks(a,bins=50,stds=1):
    if len(a.shape) == 3: ## In case you pass all the nodes
        a = np.nanmean(a,axis=1)
    a = np.array(a)
    a_num = np.nan_to_num(a)
## will need these in a bit
    a_x,a_y = a_num[:,0],a_num[:,1]

    good_points = ~np.isnan(a[:,0]) & ~np.isnan(a[:,1])
    b = a[good_points]
    counts,xedges,yedges = np.histogram2d(b[:,0],b[:,1],bins=bins)
    peaks = np.argwhere(counts > counts.mean() + counts.std() * stds) 
    for p in peaks:
        x_,y_ = p
        x0,x1 = xedges[x_],xedges[x_ + 1]
        y0,y1 = yedges[y_],yedges[y_ + 1]
        
        bad_x = (a_x >= x0) & (a_x <= x1)
        bad_y = (a_y >= y0) & (a_y <= y1)
        bad_points = bad_x & bad_y
        a[bad_points] = np.nan
    return a

if __name__ == '__main__':
    args = build_parse()
    file_object = np.load(args.input_file)
    if args.verbose:
        print('loading file:',args.input_file)
        print('included data:',list(file_object.keys()))
    xs = file_object['X']
    ys = file_object['Y']
    ts = file_object['timestamp']
    drops = file_object['missing']
    vs = file_object['SPEED']

    out_table = np.array([ts,xs,ys,vs,drops])
    out_table = out_table.transpose()

    if args.output_file is not None:
        out_name = args.output_file
    else:
        out_name = args.input_file.replace('.npz','.csv')
    if args.head:
## Combine the meta and stats into a header line
        col_names = 'Time,X,Y,Velocity,dropped frame,Meta:,'
        if True:
            stat_dict = get_stats(file_object)
            meta_dict = get_meta(args.input_file)
            head_string = col_names + str(meta_dict)[1:-1] + ',' + str(stat_dict)[1:-1]
        else:
            print('Input name formatted incorrectly, using file path for header')
            head_string = 'Input path: ' + args.input_file
    else:
        head_string = ''

    np.set_printoptions(suppress=True)
    np.savetxt(out_name,out_table,delimiter=',',header=head_string,fmt=['%d','%1.3f','%1.3f','%1.3f','%d'])

    if args.showplot or args.saveplot:
        fig,ax = plot_array(np.array([ts,xs,ys]))
        if args.showplot:
            plt.show()
        if args.saveplot:
            plt.savefig(out_name + '.png',dpi=300)


