import numpy as np
from matplotlib import pyplot as plt
import argparse

## This code will integrate two (possibly) conflicting tracks from a single individual. 

## This assumes they're already merged to a single 1 X T track, with np.nan gaps

def build_parse():
    parser = argparse.ArgumentParser(description='Required and additional inputs')
    parser.add_argument('--sleap_track','-a',required=True,help='Path to .npy, generated from output from SLEAP')
    parser.add_argument('--br_track','-b',required=True,help='Path to second .npy file, output from br-detection')
    parser.add_argument('--out_file','-o',required=False,help='Path to .npy output, if not specified, just uses existing filename')
    parser.add_argument('--center_list','-x',required=False,help='Optional center_dict to define central point')
    parser.add_argument('--id','-c',required=False,help='Camera id, required if using the defined center points')
    parser.add_argument('--n_fish','-n',required=False,help='Number of fish, defaults to 4')
    parser.add_argument('--quadrants','-q',required=False,help='List of quadrants (left to right, top down) where fish are, i.e. [0,1,3]')
    parser.add_argument('--visualize','-v',action='store_true',help='Visualize plot, defaults to False')
    parser.add_argument('--dump','-d',action='store_true',help='Debug option to prevent saving output')
    return parser.parse_args()



def distance_cost(X,Y,axis=None):
    return np.linalg.norm(X-Y,axis=axis)**2 / 1000

# This could probably be optimized further, let's see how quick it is though. 
def viterbi(track_A,track_B,distance_cost=distance_cost):
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
        if t >= 14500:
            pass
            #print(track_A[t],track_B[t])
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

    s_final = np.argmin(cost_matrix[-1]) ## get best state
    best_state = np.empty(T).astype(int)
    best_cost = np.zeros(T)
    consensus_track = np.full([T,2],np.nan)
    best_state[-1] = s_final
    best_cost[-1] = cost_matrix[-1,s_final]
    consensus_track[-1] = tracks[s_final][-1]
## Work backwards, starting from the lowest end state, and 
#    following the best path backwards
    #import pdb;pdb.set_trace()
    for t_ in range(T-1)[::-1]:
        best_state[t_] = path_matrix[t_+1,best_state[t_+1]]
        consensus_track[t_] = tracks[best_state[t_]][t_]
        best_cost[t_] = cost_matrix[t_,best_state[t_]]
    cost_diff = np.diff(best_cost,prepend=0)
    return consensus_track,best_state,cost_diff

if __name__ == '__main__':
    args = build_parse()

    if args.out_file is None:
        outfile = args.sleap_track.replace('.npy','.combined.npy')
    else:
        outfile = args.out_file
    #track_A = np.load('testA.npy')
    #track_B = np.load('testB.npy')
    #track_A = np.load('../src/flat_detections_baby.npy')
    #track_B = np.load('../working_dir/pi13.2023.10.11.06.00.squished.npy')
    track_A = np.load(args.sleap_track)
    track_B = np.load(args.br_track)

    if np.shape(track_A) != np.shape(track_B):
        print('tracks do not match, this will likely cause problems')

    track_C = np.empty_like(track_A)
    print('Building conensus tracks')
    for n in range(4):
        consensus_track,best_path,cost_diff = viterbi(track_A[n],track_B[n])
        track_C[n] = consensus_track

    if not args.dump:
        print('Saving conensus at:',outfile)
        np.save(outfile,track_C)
    
    if args.visualize:
        fig,ax = plt.subplots()
        ax.plot(track_A[3,:,1],alpha=0.5,color='green',label='BR-detection')
        ax.plot(track_B[3,:,1],alpha=0.5,color='blue',label='sleap')
        #ax.plot(cost_diff,color='gray',label='cost')
        ax.plot(consensus_track[:,1],alpha=1,color='black',linestyle=':',label='consensus')

        ax.legend()
        plt.show()

