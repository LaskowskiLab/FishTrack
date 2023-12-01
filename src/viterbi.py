import numpy as np
from matplotlib import pyplot as plt

## This code will integrate two (possibly) conflicting tracks from a single individual. 

## This assumes they're already merged to a single 1 X T track, with np.nan gaps


def distance_cost(X,Y,axis=None):
    return np.linalg.norm(X-Y,axis=axis)**2 / 1000

# This could probably be optimized further, let's see how quick it is though. 
def viterbi(track_,track_B,distance_cost=distance_cost):
    track_0 = np.full_like(track_A,np.nan)

    T = len(track_A) 

    tracks = [track_A,track_B,track_0]
## Define transition probability
# eventually this will be done on a per-frame basis
    cost_matrix = np.zeros([T,3])
    path_matrix = np.zeros([T,3])
    initial_prob = np.ones([3]) / 3
    transit_cost = np.zeros([3,3])
    transit_cost[0] = [0,10,50]
    transit_cost[1] = [10,0,50]
    transit_cost[2] = [0,0,1]

    emit_cost = np.zeros(3) ## this definitely has to be calculated per frame

    transit_matrix = np.zeros([3,3,T-1]) ## This shoudl be faster
    #import pdb;pdb.set_trace()
    transit_matrix[0,1] = distance_cost(track_A[:-1],track_B[1:],axis=1)
    transit_matrix[1,0] = distance_cost(track_B[:-1],track_A[1:],axis=1)
    transit_matrix[0,0] = distance_cost(track_A[:-1],track_A[1:],axis=1)
    transit_matrix[1,1] = distance_cost(track_B[:-1],track_B[1:],axis=1)
    transit_matrix[0,2] = 50
    transit_matrix[1,2] = 50
    transit_matrix[2,2] = 1

    track_distance = distance_cost(track_A,track_B,axis=1)

    for t in range(1,T):
## Need to calculate transition cost matrix too
        if t >= 3360:
            pass
            #import pdb;pdb.set_trace()
        if False:
            transit_cost_ = np.ones([3,3]) * 50
            transit_cost_[0,1] = dist_cost(track_A[t-1],track_B[t])
            transit_cost_[1,0] = dist_cost(track_B[t-1],track_A[t])
            transit_cost_[0,0] = dist_cost(track_A[t-1],track_A[t])
            transit_cost_[1,1] = dist_cost(track_B[t-1],track_B[t])
            transit_cost_[2] = 0
            transit_cost_[2,2] = 100
        else:
            transit_cost_ = transit_matrix[:,:,t-1]

        if np.isnan(track_A[t,0]): ## if A is missing
            if np.isnan(track_B[t,0]): ## and B is missing
                emit_cost = [1000,1000,0]
            else: ## or if B is there, but A is still missing
                emit_cost = [1000,0,100]
        elif np.isnan(track_B[t,0]): ## or is only A is there
            emit_cost = [0,1000,100]
        else: ## If both tracks exist here
            emit_cost[0] = track_distance[t]
            emit_cost[1] = track_distance[t]
            emit_cost[2] = 50
## Calculate the cost of possible paths and pick best
        for s in range(3):
            prev = cost_matrix[t-1]
            possible_paths = prev + transit_cost_[:,s] + emit_cost[s]
            min_path = np.nanargmin(possible_paths) 
            min_cost = possible_paths[min_path] 
            if np.isnan(min_cost):
                import pdb;pdb.set_trace()
            path_matrix[t,s] = min_path
            cost_matrix[t,s] = min_cost

    p = np.argmin(cost_matrix[-1]) ## get best path
    best_path = np.empty(T).astype(int)
    consensus_path = np.full([T,2],np.nan)
    best_path[-1] = p

## Work backwards, starting from the lowest end state, and 
#    following the best path backwards
    #import pdb;pdb.set_trace()
    for t_ in range(T-1)[::-1]:
        best_path[t_] = path_matrix[t_,best_path[t_+1]]
        consensus_path[t_] = tracks[best_path[t_]][t_]

    print(best_path[:100])
    return consensus_path,best_path

if __name__ == '__main__':

    track_A = np.load('testA.npy')
    track_B = np.load('testB.npy')
    if len(track_B) != len(track_A):
        if len(track_A) > len(track_B):
            track_A = track_A[:len(track_B)]
        else:
            track_B = track_B[:len(track_A)]

    track_A = np.nanmean(track_A,1)
    track_B = np.nanmean(track_B,1)
    consensus_path,best_path = viterbi(track_A,track_B)
    #np.save('testC.npy',consensus_path)
    
    fig,ax = plt.subplots()
    ax.plot(track_A[:,1],alpha=0.5,color='green')
    ax.plot(track_B[:,1],alpha=0.5,color='blue')
    ax.plot(consensus_path[:,1],alpha=1,color='black',linestyle=':')

    plt.show()

