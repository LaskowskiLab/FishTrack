import numpy as np
import sys

track_file = sys.argv[1]

track = np.load(track_file)

center_point = [375,486]

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

columns = ['Video','Fish','Bin',
            'MeanVisibility','MeanActivity','MeanBoldness','MeanVel','StdVel','MedianVel',
            'MeanVisibility_bin','MeanActivity_bin','MeanBoldness_bin',
                                                'MeanVel_bin','StdVel_Bin','MedianVel_bin']

def count_open(track,center_point):
    #import pdb;pdb.set_trace()
    clean_track = track[~np.isnan(track[:,0])]
    xs = np.abs(clean_track[:,0] - center_point[0]) > 100
    ys = np.abs(clean_track[:,1] - center_point[1]) > 200
    courage_count = np.sum(np.logical_and(xs,ys))
    courage_ratio = courage_count / len(clean_track)
    return courage_count,courage_ratio

for f in range(n_fish):
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

with open('test.csv','w') as out_f:
    delim = ','
    header = delim.join(columns)
    out_f.write(header + '\n')
    for f in range(n_fish):
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

            f_line = delim.join([track_file.replace('.npy',''),str(f),str(i),
                        meanVis,meanAct,meanBold,meanVel,stdVel,medianVel,
                        meanVis_,meanAct_,meanBold_,meanVel_,stdVel_,medianVel_])
            out_f.write(f_line + '\n')

