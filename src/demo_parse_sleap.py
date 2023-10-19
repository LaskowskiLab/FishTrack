
import numpy as np
import parse_sleap

#in_file = '/home/ammon/Downloads/Jon01.2023.02.17.13.23.mp4.predictions.slp.h5' 
#in_file = './JON02.2022.10.14.11.20.mp4.predictions.slp.h5' 
in_file = './jon_test.h5'

locations,track_occupancy,instance_scores = parse_sleap.read_h5(in_file)
all_tracks = np.nanmean(locations,1)

#print(a.shape)
trimmed_tracks,track_occupancy_trim = parse_sleap.clear_peaks_all(all_tracks,track_occupancy,plot_me=True,stds=3)

single_track,single_occupancy = parse_sleap.overlay_tracks(trimmed_tracks,track_occupancy_trim,instance_scores,min_track=2)

slowed_track = parse_sleap.clear_superspeed(single_track,max_speed=200)

clean_track,clean_occupancy = parse_sleap.clear_teleports_(slowed_track,max_distance = 300,min_track=2)

#c_ = parse_sleap.clear_peaks(c)

full_track = np.empty_like(clean_track)
full_track[:,0] = parse_sleap.interp_track(clean_track[:,0])
full_track[:,1] = parse_sleap.interp_track(clean_track[:,1])

#print(b.shape,single_occupancy.shape)

from matplotlib import pyplot as plt
fig,ax = plt.subplots()

#ax.plot(np.sum(single_occupancy,axis=0))
#ax.plot(np.sum(track_occupancy,axis=0)+3)

simple_a = np.nanmedian(all_tracks[:,0],axis=1)
for t_ in range(np.shape(all_tracks)[2]):
    ax.plot(all_tracks[:,0,t_],color='black',alpha=0.3)
    ax.plot(trimmed_tracks[:,0,t_],color='blue',alpha=0.5)

ax.plot(single_track[:,0],alpha=0.5,color='tab:blue')
#ax.plot(simple_a,alpha=0.5)
c_copy = np.array(single_track)
dx = np.abs(np.diff(single_track[:,0],prepend=0))
dy = np.abs(np.diff(single_track[:,1],prepend=0))
ax.plot(dx,color='green')

ax.plot(single_track[:,0],alpha=0.8,color='red')
ax.plot(full_track[:,0],alpha=0.8,color='black',linestyle=':')
plt.show()

np.save('test_raw_track.npy',single_track)
np.save('test_clean_track.npy',clean_track)
np.save('test_full_track.npy',full_track)
