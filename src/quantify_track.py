import numpy as np
import sys
import argparse
from datetime import datetime 
import pandas as pd 

def count_open(track,center_point):
    #import pdb;pdb.set_trace()
    clean_track = track[~np.isnan(track[:,0])]
    xs = np.abs(clean_track[:,0] - center_point[0]) > 100
    ys = np.abs(clean_track[:,1] - center_point[1]) > 200
    courage_count = np.sum(np.logical_and(xs,ys))
    courage_ratio = courage_count / len(clean_track)
    return courage_count,courage_ratio

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
    parser.add_argument('--video_key','-k',required=False,help='Path to csv containing the identity of the fish')
    return parser.parse_args()

def build_dict(input_csv):
    data_dict = {}
    data_df = pd.read_csv(input_csv)
    pis = data_df.pi.unique()
    for p in pis:
        sub_dict = {}
        sub_dict['start'] = list(data_df[data_df.pi == p].start)
        sub_dict['start'] = list(data_df[data_df.pi == p].start)
        sub_dict['end'] = list(data_df[data_df.pi == p].end)

        raw_cells = list(data_df[data_df.pi == p].occupiedCells)
        raw_IDs = list(data_df[data_df.pi == p].IDs)

        cells = []
        for c in raw_cells:
            clean_c = c.strip("[]")
            cells.append(clean_c.split(','))
        IDs = []
        for i in raw_IDs: ## sort of clunky way to deal with where strings start
            clean_i = i.strip("[]")
            IDs.append(clean_i.split(','))

        sub_dict['OccupiedCells'] = cells 
        sub_dict['IDs'] = IDs
        sub_dict['start']
        data_dict[p] = sub_dict
    return data_dict


if __name__ == "__main__":
    args = build_parse()
    track_file = args.in_file

    track = np.load(track_file)

    CENTER = [375,486]
    if args.center_list == None:
        print('no center dict given..')
        print('using default:',CENTER)
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

    print(track.shape) ## This should either be 4xFramesx2, or Frames x 2

    if len(track.shape) == 3:
        n_fish = track.shape[0]
        n_frames = track.shape[1]
    elif len(track.shape) == 2:
        n_fish = 1
        n_frames = track.shape[0]
        track = np.reshape(track,[1,n_frames,2])

    else:
        print('Something went terribly wrong')

    bin_size = 3600 ## this means 1 hour
    n_bins = n_frames // bin_size

    n_bins = max(1,n_bins)

    visibility_array = np.zeros([n_fish,n_bins])
    mean_velocity_array = np.zeros([n_fish,n_bins])
    median_velocity_array = np.zeros([n_fish,n_bins])
    std_velocity_array = np.zeros([n_fish,n_bins])
    activity_array = np.zeros([n_fish,n_bins])
    corner_array = np.zeros([n_fish,n_bins])
    medianVels = [0 for f in range(n_fish)]
    stdVels = [0 for f in range(n_fish)]

    columns = ['Video','FishID','Quadrant','Bin','Date','ExpDay','YearDay',
                'MeanVisibility','MeanActivity','MeanBoldness','MeanVel','StdVel','MedianVel',
                'MeanVisibility_bin','MeanActivity_bin','MeanBoldness_bin',
                                                    'MeanVel_bin','StdVel_Bin','MedianVel_bin']

    fish_ids = [None for f in range(4)]
    delta = np.inf
    delta_days = np.nan
    date_str = np.nan
    year_day = np.nan
    if args.video_key is not None:
        data_dict = build_dict(args.video_key)

        basename = args.in_file.split('/')[-1]
        piID = basename.split('.')[0]
        date = basename.split('.')[1:4]
        YYYY,MM,DD = date
        date_str = '/'.join([YYYY,MM,DD])
        file_date = datetime.strptime(date_str, '%Y/%m/%d')
        pi_dict = data_dict[piID]
        n_possible_vids = len(pi_dict['start'])
        for m in range(n_possible_vids):
            start_date = datetime.strptime(pi_dict['start'][m], '%m/%d/%y')
            end_date = datetime.strptime(pi_dict['end'][m], '%m/%d/%y')
            
            if file_date >= start_date and file_date <= end_date:
                delta_m = file_date - start_date
                if delta_m.days < delta: ## this allows us to deal with multiple possible start times and pick the right one
                    delta_days = delta_m.days
                    delta = delta_days
                    year_day = file_date.timetuple().tm_yday
                    fish_ids = pi_dict['IDs'][m]
                    occupied_cells = pi_dict['OccupiedCells'][m]
    if args.out_file is None:
        outfile = args.in_file.replace('.npy','.csv')
    else:
        outfile = args.out_file

    for f in range(4): ## defined above
        sub_track = track[f]
        sub_diff = np.diff(sub_track,axis=0,prepend=0)
        velocity = np.linalg.norm(sub_diff,axis=1)

        medianVels[f] = np.nanmedian(velocity)
        stdVels[f] = np.nanstd(velocity)

        visibility = ~np.isnan(sub_track[:,0])

        for i in range(n_bins):
            i0 = i * bin_size
            i1 = (i+1) * bin_size
            track_bin = sub_track[i0:i1]
            sub_velocity = velocity[i0:i1]
            sub_vel = np.nanmedian(sub_velocity)
            sub_vis = np.sum(visibility[i0:i1]) / bin_size
            clean_velocity = sub_velocity[~np.isnan(sub_velocity)]
            sub_active = np.sum(clean_velocity > 5) / len(clean_velocity)

            courage_count,courage_ratio = count_open(track_bin,center_point)
            visibility_array[f,i] = sub_vis
            median_velocity_array[f,i] = sub_vel
            mean_velocity_array[f,i] = np.nanmean(sub_velocity)
            std_velocity_array[f,i] = np.nanstd(sub_velocity)

            corner_array[f,i] = courage_ratio
            activity_array[f,i] = sub_active

    if args.project_csv is not None:
        project_f = open(args.project_csv,'a')

    with open(outfile,'w') as out_f:
        delim = ','
        header = delim.join(columns)
        out_f.write(header + '\n')
        for f in range(4):
            fish_id = fish_ids[f]
            meanVis = str(np.round(np.nanmean(visibility_array[f]),3))

            medianVel = str(np.round(medianVels[f],3))
            meanVel = str(np.round(np.nanmean(mean_velocity_array[f]),3))
            stdVel = str(np.round(stdVels[f],3))

            meanAct = str(np.round(np.nanmean(activity_array[f]),3))
            meanBold = str(np.round(np.nanmean(corner_array[f]),3))

            for i in range(n_bins):
                meanVis_ = str(np.round(visibility_array[f,i],3))

                meanVel_ = str(np.round(mean_velocity_array[f,i],3))
                stdVel_ = str(np.round(std_velocity_array[f,i],3))
                medianVel_ = str(np.round(median_velocity_array[f,i],3))

                meanAct_ = str(np.round(activity_array[f,i],3))
                meanBold_ = str(np.round(corner_array[f,i],3))

                f_line = delim.join([track_file.replace('.npy',''),str(fish_id),str(f),str(i),str(date_str),str(delta_days),str(year_day),
                            meanVis,meanAct,meanBold,meanVel,stdVel,medianVel,
                            meanVis_,meanAct_,meanBold_,meanVel_,stdVel_,medianVel_])
                out_f.write(f_line + '\n')
                if args.project_csv is not None:
                    project_f.write(f_line + '\n')

    if args.project_csv is not None:
        project_f.close()
