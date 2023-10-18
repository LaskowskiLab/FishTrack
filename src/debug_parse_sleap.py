
import numpy as np
import parse_sleap

#in_file = '/home/ammon/Downloads/Jon01.2023.02.17.13.23.mp4.predictions.slp.h5' 
#in_file = './JON02.2022.10.14.11.20.mp4.predictions.slp.h5' 
in_file = './jon_test.h5'

locations,track_occupancy,instance_scores = parse_sleap.read_h5(in_file)
a = np.nanmean(locations,1)

a_trim,track_occupancy_trim = parse_sleap.clear_peaks_all(a,track_occupancy)

b,single_occupancy = parse_sleap.overlay_tracks(a_trim,track_occupancy_trim,instance_scores,min_track=1)

c,clean_occupancy = parse_sleap.clear_teleports_(b,single_occupancy,max_distance = 300,min_track=2)

import pdb;pdb.set_trace()
c_ = parse_sleap.clear_peaks(c)

d = np.empty_like(c_)
d[:,0] = parse_sleap.interp_track(c[:,0])
d[:,1] = parse_sleap.interp_track(c[:,1])

#print(b.shape,single_occupancy.shape)

from matplotlib import pyplot as plt
fig,ax = plt.subplots()

#ax.plot(np.sum(single_occupancy,axis=0))
#ax.plot(np.sum(track_occupancy,axis=0)+3)

simple_a = np.nanmedian(a[:,0],axis=1)
ax.plot(b[:,0],alpha=0.5,color='tab:blue')
#ax.plot(simple_a,alpha=0.5)
ax.plot(c[:,0],alpha=0.5,color='red')
ax.plot(d[:,0],alpha=0.5,color='black',linestyle=':')
#plt.show()

np.save('test_b.npy',b)
np.save('test_c.npy',c)
np.save('test_d.npy',d)
