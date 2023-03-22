from matplotlib import pyplot as plt
import numpy as np


stat_array = np.zeros([4,4])
## mean speed, std(speed), mean(hide) std(hide)
stat_array[0] = [1.874,0.151,0.507,0.300] 
stat_array[1] = [1.441,0.724,0.233,0.337]
stat_array[2] = [1.620,0.329,0.280,0.230]
stat_array[3] = [1.520,0.273,0.193,0.123]

fish = ['Fish1','Fish2','Fish3','Fish4']
colors = ['red','cyan','green','orange']
fig,ax = plt.subplots()
ax.bar(range(4),stat_array[:,0],yerr = stat_array[:,1]/np.sqrt(10),color=colors)
ax.set_ylabel('Mean Speed')
ax.set_xticks(range(4))
ax.set_xticklabels(fish,rotation=0)

fig.savefig('/home/ammon/Desktop/mean_speed.png',dpi=300)
fig.savefig('/home/ammon/Desktop/mean_speed.svg')
fig1,ax1 = plt.subplots()
ax1.bar(range(4),stat_array[:,2],yerr = stat_array[:,3]/np.sqrt(10),color=colors)
ax1.set_ylabel('Proprtion hiding')
ax1.set_xticks(range(4))
ax1.set_xticklabels(fish,rotation=0)

fig1.savefig('/home/ammon/Desktop/prop_hiding.png',dpi=300)
fig1.savefig('/home/ammon/Desktop/prop_hiding.svg')
plt.show()

