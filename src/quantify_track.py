import numpy as np
import sys
import argparse
from datetime import datetime 
import pandas as pd 
from parse_sleap import interp_track

def count_open(track,center_point):
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
    parser.add_argument('--png','-s',action='store_true',help='If included, saves a png scatter plot')
    parser.add_argument('--dump','-d',action='store_true',help='Debug option to prevent saving output')
    parser.add_argument('--project_csv','-p',required=False,help='Path to a project csv where all the summary statistics will be written')
    parser.add_argument('--video_key','-k',required=False,help='Path to tsv containing the identity of the fish')
    return parser.parse_args()

def build_dict(input_tsv):
    data_dict = {}
    data_df = pd.read_table(input_tsv)
    pis = data_df.pi.unique()
    for p in pis:
        sub_dict = {}
        sub_dict['start'] = list(data_df[data_df.pi == p].start)
        sub_dict['end'] = list(data_df[data_df.pi == p].end)

        raw_cells = list(data_df[data_df.pi == p].OccupiedCells)
        raw_IDs = list(data_df[data_df.pi == p].IDs)
        if "Treatments" in data_df.columns:
            raw_Treats = list(data_df[data_df.pi == p].Treatments)
        else:
            raw_Treats = [str([np.nan for i in range(4)]) for i in raw_IDs]
        cells = []
        for c in raw_cells:
            clean_c = c.strip("[]")
            cells.append(clean_c.split(','))
        IDs = []
        for i in raw_IDs: ## sort of clunky way to deal with where strings start
            clean_i = i.strip("[]")
            IDs.append(clean_i.split(','))

        Treats = []
        #import pdb;pdb.set_trace()
        for i in raw_Treats: ## sort of clunky way to deal with where strings start
            clean_i = i.strip("[]")
            Treats.append(clean_i.split(','))


        sub_dict['OccupiedCells'] = cells 
        sub_dict['IDs'] = IDs
        sub_dict['Treatments'] = Treats
        data_dict[p] = sub_dict

    return data_dict


if __name__ == "__main__":
    args = build_parse()
    track_file = args.in_file

    track = np.load(track_file)
## We have the option of interpolation, but it's rarely good in tracking tanks.
    """
    track_interpolated = np.empty_like(track)
    for n in range(4):
        track_interpolated[n,:,0] = interp_track(track[n,:,0])
        track_interpolated[n,:,1] = interp_track(track[n,:,1])
    np.save('test_interp.npy',track_interpolated)
    """
    
    #CENTER = [375,486]
    CENTER = [440,515]
    if args.center_list == None:
        print('no center dict given..')
        print('using default:',CENTER)
        center_point = CENTER
    else:
        print('center dict found, checking for key')
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

    visibility_array = np.full([n_fish,n_bins],np.nan)
    mean_velocity_array = np.full([n_fish,n_bins],np.nan)
    median_velocity_array = np.full([n_fish,n_bins],np.nan)
    mean_active_velocity_array = np.full([n_fish,n_bins],np.nan)
    median_active_velocity_array = np.full([n_fish,n_bins],np.nan)
    std_active_velocity_array = np.full([n_fish,n_bins],np.nan)
    std_velocity_array = np.full([n_fish,n_bins],np.nan)
    activity_array = np.full([n_fish,n_bins],np.nan)
    corner_array = np.full([n_fish,n_bins],np.nan)
    hiding_array = np.full([n_fish,n_bins],np.nan)

    medianVels = [np.nan for f in range(n_fish)]
    stdVels = [np.nan for f in range(n_fish)]
    
    medianActiveVels = [np.nan for f in range(n_fish)]
    stdActiveVels = [np.nan for f in range(n_fish)]
## A smarter person would have made these columns exactly match the variables in the code...
    columns = ['Video','FishID','Quadrant','Bin','Date','ExpDay','YearDay',
                'MeanVisibility','MeanActivity','MeanBoldness','MeanVel','StdVel','MedianVel',
                'MeanVisibility_','MeanActivity_','MeanBoldness_',
                'MeanVel_','StdVel_','MedianVel_',
                'Treatments','PropHiding','PropHiding_',
                'MeanActiveVel','StdActiveVel','MedianActiveVel','MeanActiveVel_','StdActiveVel_','MedianActiveVel_']

    fish_ids = [None for f in range(4)]
    delta = np.inf
    fish_deltas = [np.nan for f in range(4)]
    date_str = np.nan
    year_day = np.nan
    vid_name = args.in_file
    basename = args.in_file.split('/')[-1]
    piID = basename.split('.')[0]
    date = basename.split('.')[1:4]
    vid_name = '.'.join([piID] + date)
    fish_treatments = [np.nan for n in range(4)]
    if args.video_key is not None:
        data_dict = build_dict(args.video_key)
        if piID in data_dict.keys():
            fish_deltas = [np.nan for n in range(4)]
            fish_treatments = [np.nan for n in range(4)]


            YYYY,MM,DD = date
            date_str = '/'.join([YYYY,MM,DD])
            file_date = datetime.strptime(date_str, '%Y/%m/%d')
            pi_dict = data_dict[piID]
            n_possible_vids = len(pi_dict['start'])
            year_day = file_date.timetuple().tm_yday
            delta_days = 500 
            for m in range(n_possible_vids):
                start_date = datetime.strptime(pi_dict['start'][m], '%m/%d/%y')
                end_date = datetime.strptime(pi_dict['end'][m], '%m/%d/%y')
                
                if file_date < start_date:
                    continue
                delta_m = file_date - start_date
                delta = delta_days
                #fish_ids = pi_dict['IDs'][m]
                occupied_cells = pi_dict['OccupiedCells'][m]
                occupied_cells = [int(o) for o in occupied_cells]
## There are some cases where the video has different aged fish in different cells
                for o in range(4):
## need to get this right for every fish...
                    if np.isnan(fish_deltas[o]) or delta_m.days < fish_deltas[o]:
                        fish_treatments[o] = pi_dict['Treatments'][m][o]
                        fish_deltas[o] = delta_m.days
                        fish_ids[o] = pi_dict['IDs'][m][o]
                        if fish_ids[0] == 'n/a':
                            fish_ids[0] = None 
                    else:
                        continue
    if args.out_file is None:
        outfile = args.in_file.replace('.npy','.csv')
    else:
        outfile = args.out_file

    if args.png:
        fig,ax = plt.subplots()
        for f in n_fish:
            ax.scatter(track[f])
        fig.save_fig(outfile.replace('.csv','.png'),dpi=300)


    for f in range(4): ## defined above
        sub_track = track[f]
        sub_diff = np.diff(sub_track,axis=0,prepend=0)
        velocity = np.linalg.norm(sub_diff,axis=1)
        
        active_velocity = np.array(velocity)
        active_velocity[active_velocity < 5] = np.nan

        medianVels[f] = np.nanmedian(velocity)
        stdVels[f] = np.nanstd(velocity)

        medianActiveVels[f] = np.nanmedian(active_velocity)
        stdActiveVels[f] = np.nanstd(active_velocity)

        visibility = ~np.isnan(sub_track[:,0])

        for i in range(n_bins):
            i0 = i * bin_size
            i1 = (i+1) * bin_size
            track_bin = sub_track[i0:i1]
            sub_velocity = velocity[i0:i1]

            median_velocity_array[f,i] = np.nanmedian(sub_velocity)
            mean_velocity_array[f,i] = np.nanmean(sub_velocity)
            std_velocity_array[f,i] = np.nanstd(sub_velocity)
            sub_vis = np.sum(visibility[i0:i1]) / bin_size

            sub_vel = np.nanmedian(sub_velocity)
            clean_velocity = sub_velocity[~np.isnan(sub_velocity)]
            sub_active = np.sum(clean_velocity > 5) / len(clean_velocity)

            sub_velocity_active = active_velocity[i0:i1] ## Active velocity is defined up above, everywhere vel > 5

            courage_count,courage_ratio = count_open(track_bin,center_point)
            visibility_array[f,i] = sub_vis
            median_velocity_array[f,i] = sub_vel
            mean_velocity_array[f,i] = np.nanmean(sub_velocity)
            std_velocity_array[f,i] = np.nanstd(sub_velocity)

            mean_active_velocity_array[f,i] = np.nanmean(sub_velocity_active)
            median_active_velocity_array[f,i] = np.nanmedian(sub_velocity_active)
            std_active_velocity_array[f,i] = np.nanstd(sub_velocity_active)

            hiding_array[f,i] = courage_count / bin_size + sub_vis
            corner_array[f,i] = courage_ratio
            activity_array[f,i] = sub_active

    if args.project_csv is not None:
        project_f = open(args.project_csv,'a')
        if np.sum(~np.isnan(fish_deltas)) == 0:
            orphan_path = args.project_csv.replace('.csv','.orphaned.csv')
            with open(orphan_path,'a') as orphan_f:
                orphan_f.write(args.in_file + '\n')

    if args.dump:
        f_mode = 'a'
    else:
        f_mode = 'w'
    with open(outfile,f_mode) as out_f:
        delim = ','
        header = delim.join(columns)
        if not args.dump:
            out_f.write(header + '\n')
        for f in range(4):
            fish_id = fish_ids[f]
            meanVis = str(np.round(np.nanmean(visibility_array[f]),3))
            stdVis = str(np.round(np.nanstd(visibility_array[f]),3))

            medianVel = str(np.round(medianVels[f],3))
            meanVel = str(np.round(np.nanmean(mean_velocity_array[f]),3))
            stdVel = str(np.round(stdVels[f],3))

            medianActiveVel = str(np.round(medianActiveVels[f],3))
            stdActiveVel = str(np.round(stdActiveVels[f],3))
            meanActiveVel = str(np.round(np.nanmean(mean_active_velocity_array[f]),3))

            meanAct = str(np.round(np.nanmean(activity_array[f]),3))
            stdAct = str(np.round(np.nanstd(activity_array[f]),3))

            meanBold = str(np.round(np.nanmean(corner_array[f]),3))
            stdBold = str(np.round(np.nanstd(corner_array[f]),3))

            treatment = str(fish_treatments[f])
            propHiding = str(np.round(np.nanmean(hiding_array[f]),3))
            for i in range(n_bins):
                meanVis_ = str(np.round(visibility_array[f,i],3))

                meanVel_ = str(np.round(mean_velocity_array[f,i],3))
                stdVel_ = str(np.round(std_velocity_array[f,i],3))
                medianVel_ = str(np.round(median_velocity_array[f,i],3))

                meanActiveVel_ = str(np.round(mean_active_velocity_array[f,i],3))
                stdActiveVel_ = str(np.round(std_active_velocity_array[f,i],3))
                medianActiveVel_ = str(np.round(median_active_velocity_array[f,i],3))

                meanAct_ = str(np.round(activity_array[f,i],3))
                meanBold_ = str(np.round(corner_array[f,i],3))

                propHiding_ = str(np.round(hiding_array[f,i],3))

                f_line = delim.join([vid_name,str(fish_id),str(f),str(i),str(date_str),str(fish_deltas[f]),str(year_day),
                            meanVis,meanAct,meanBold,meanVel,stdVel,medianVel,
                            meanVis_,meanAct_,meanBold_,meanVel_,stdVel_,medianVel_,
                            treatment,propHiding,propHiding_,
                            meanActiveVel,stdActiveVel,medianActiveVel,meanActiveVel_,stdActiveVel_,medianActiveVel_])
                """ # Reminder:
                columns = ['Video','FishID','Quadrant','Bin','Date','ExpDay','YearDay',
                            'MeanVisibility','MeanActivity','MeanBoldness','MeanVel','StdVel','MedianVel',
                            'MeanVisibility_','MeanActivity_','MeanBoldness_',
                            'MeanVel_','StdVel_','MedianVel_',
                            'Treatments','PropHiding','PropHiding_',
                            'MeanActiveVel','StdActiveVel','MedianActiveVel','MeanActiveVel_','StdActiveVel_','MedianActiveVel_']
                """

                if not args.dump:
                    out_f.write(f_line + '\n')
                else:
                    print(list(zip(columns,f_line.split(','))))
                if args.project_csv is not None and not args.dump:
                    project_f.write(f_line + '\n')

    if args.project_csv is not None and not args.dump:
        project_f.close()
