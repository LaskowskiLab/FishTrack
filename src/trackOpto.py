import cv2,sys
import time
import numpy as np
import parse_sleap
from scipy import ndimage

# Create a VideoCapture object and read from input file
# If the input is the camera, pass 0 instead of the video file name
#output_video = ('./test_spots.mp4')

CENTER = np.array([960,540]) 
MIN_VEL = 0.005
## Reads in array of xy coordints (frames,2)
## spirts out array of polar coordints (frames,2)
def xy_to_polar(a,center=CENTER):
    a_polar = np.full(a.shape,np.nan)
    dx = a[:,0] - center[0]
    dy = a[:,1] - center[1]
    a_polar[:,0] = np.sqrt(dx**2 + dy**2)
    a_polar[:,1] = np.arctan2(dy,dx)
    return a_polar

## Takes an array of xy coordinates (frames,2) 
## Returns an vector of distances of length (frames - 1)
def get_distance(a):
    a0 = a[:-1]
    a1 = a[1:]
    dist = np.linalg.norm(a1-a0,axis=1)
    return dist

def plot_spots(input_video,coords,polar_vel=None):
    cap = cv2.VideoCapture(input_video)
    count = -1
    fontFace = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 1
    color = (0,0,255)
    thickness = 2
    lineType = cv2.LINE_AA
    while(cap.isOpened()):
        count += 1
        ret, frame = cap.read()
        if not ret:
            break 

        if polar_vel is not None:
            cor = [0,0,0]
            if polar_vel[count] < 0:
                cor = [255,0,0]
            elif polar_vel[count] > 0:
                cor = [0,0,255]
            if abs(polar_vel[count]) < MIN_VEL:
                cor = [0,0,0]
        cv2.circle(frame,coords[count].astype(int),10,cor,thickness=-1)
        cv2.putText(frame,"AngVel: " + str(np.round(polar_vel[count],3)),(50,50),fontFace,fontScale,cor,thickness,lineType)
        cv2.imshow('frame',frame)
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()
    cap.release()

# Display the resulting frame




def make_spots(input_video,output_video,write_video=True,viz=False):
    cap = cv2.VideoCapture(input_video)
    try:
        bg_subtractor = cv2.bgsegm.createBackgroundSubtractorMOG()
        print('using MOG')
    except:
        print('using MOG2')
        bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=False)
        
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    if write_video:
        out = cv2.VideoWriter(output_video, fourcc, fps, (frame_width, frame_height), isColor=True)

# Check if camera opened successfully
    if (cap.isOpened()== False): 
        print("Error opening video stream or file")
     
    start = time.time()
    count = 0
# Read until video is completed
    MAX_DETECTIONS = 50
    detections = np.full([n_frames,MAX_DETECTIONS,2],np.nan)
    centered_centroids = np.full([n_frames,2],np.nan)
    while(cap.isOpened()):
        # Capture frame-by-frame
        #if count % 100 == 0:
        #    #print('frame:',count)
        #    #print(time.time() - start)
        count += 1
        if count % 1000 == 0:
            print('frame:',count)
        ret, frame = cap.read()
        if not ret:
            break 
# Display the resulting frame

        gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        small = cv2.pyrDown(gray)
        fg_mask = bg_subtractor.apply(small)


        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10,10))
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)
        fg_mask = cv2.erode(fg_mask, kernel, iterations=2)

        fg_mask = cv2.pyrUp(fg_mask)


        black_background = cv2.bitwise_and(gray,gray,mask=fg_mask)
        contours, hierarchy = cv2.findContours(fg_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            frame_detections = [np.mean(c[:,0],0) for c in contours]
            frame_detections = frame_detections[:MAX_DETECTIONS]
            n_detections = len(frame_detections)
            detections[count-1,:n_detections] = np.array(frame_detections)

        if True:
            min_dist = np.inf
            c_close = np.nan
            close_countour = np.nan
            for c in contours:
                c_center = np.nanmean(c,axis=(0,1))
                c_dist = np.abs(np.linalg.norm(c_center - CENTER))
                if c_dist < min_dist:
                    min_dist = c_dist
                    c_close = c_center
                    close_contour = c
            centered_centroids[count-1] = c_close            

        if viz:
            cv2.drawContours(frame,contours,-1,(255,0,0),3)
            cv2.drawContours(frame,[close_contour],-1,(0,0,255),3)
            polar_coords = xy_to_polar(centered_centroids[count-2:count])
            vel = get_distance(centered_centroids[count-2:count])
            polar_vel = np.diff(polar_coords[:,1])
            fontFace = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 1
            color = (0,0,255)
            thickness = 2
            lineType = cv2.LINE_AA
            #import pdb;pdb.set_trace()
            cv2.putText(frame,str(np.round(vel,3)),(50,50),fontFace,fontScale,color,thickness,lineType)
            cv2.putText(frame,str(np.round(polar_vel,3)),(50,150),fontFace,fontScale,color,thickness,lineType)
            """
            MIN_VEL = 0.005
            clock_wise = polar_vel > MIN_VEL
            contrary_wise = polar_vel < -1 * MIN_VEL
            clock_array = np.full_like(polar_centroids,np.nan)
            contrary_array = np.full_like(polar_centroids,np.nan)
            sit_array = np.full_like(polar_centroids,np.nan)

            clock_array[polar_vel > MIN_VEL] = centered_centroids[polar_vel > MIN_VEL]
            contrary_array[polar_vel < -1 * MIN_VEL] = centered_centroids[polar_vel < -1 * MIN_VEL]
            sit_array[np.abs(polar_vel) < MIN_VEL] = centered_centroids[np.abs(polar_vel) < MIN_VEL]
            """

            cv2.imshow('Mask',black_background)
            cv2.imshow('Frame',frame)
            key = cv2.waitKey(10)
            if key == 27:
                cv2.destroyAllWindows()
                break
        #cv2.imshow('Black',black_background)
        #cv2.imshow('White',fg_mask)
        #out.write(fg_mask)
        if write_video:
            out.write(frame)
# Press Q on keyboard to  exit
        #if cv2.waitKey(5) & 0xFF == ord('q'):
        #    break
     
# When everything done, release the video capture object
    cap.release()
    if write_video:
        out.release() 
# Closes all the frames
    cv2.destroyAllWindows()

    return detections,centered_centroids

def strip_peaks(detections):
    a = np.moveaxis(detections,[1],[2])
    track_occupancy = (1- np.isnan(a[:,0]).T).astype(bool)
    good_detections,_ = parse_sleap.clear_peaks_all(a,track_occupancy)
    good_detections = np.moveaxis(good_detections,[1],[2])
    return good_detections

def split_by_quads(detections,center=None):
    if center is None:
        center = np.nanmax(detections,axis=(0,1)) / 2 
        center = center.astype(int)
    n_frames,n_tracks = detections.shape[:2]
    quad_detections = np.full([4,n_frames,n_tracks,2],np.nan)
    quad_0 = np.argwhere((detections[:,:,0] <= center[0]) & (detections[:,:,1] <= center[1]))
    quad_1 = np.argwhere((detections[:,:,0] >  center[0]) & (detections[:,:,1] <= center[1]))
    quad_2 = np.argwhere((detections[:,:,0] <= center[0]) & (detections[:,:,1] >  center[1]))
    quad_3 = np.argwhere((detections[:,:,0] >  center[0]) & (detections[:,:,1] >  center[1]))
    q_indices = [quad_0,quad_1,quad_2,quad_3]
## This is a bit tricky, argwhere returns a list of index tuples, this takes all of them along the proper axes
    for q in range(4):
        quad_detections[q,q_indices[q][:,0],q_indices[q][:,1]] = detections[q_indices[q][:,0],q_indices[q][:,1]]

    return quad_detections

def flatten_by_quads(quad_detections):
    n_frames = quad_detections.shape[1]
    quad_detections_flat = np.full([4,n_frames,2],np.nan)

    for q in range(4):
        quad_single_track = quad_detections_flat[q]
        track_occupancy = ~np.isnan(quad_detections[q,:,:,0])
        frame_occupancy = np.sum(track_occupancy,1)
        overlapping_frames = frame_occupancy > 1
        if frame_occupancy[0] == 0:
            quad_single_track[0] = [0,0]
        else:
            quad_single_track[0] = np.nanmean(quad_detections[0],0)
        last_detection = quad_single_track[0]
        for f in range(1,n_frames):
            if frame_occupancy[f] == 0:
                continue
            good_detections = quad_detections[q,f][~np.isnan(quad_detections[q,f,:,0])]
            if frame_occupancy[f] == 1:
                quad_single_track[f] = good_detections
            else:
                distances = np.linalg.norm(good_detections - last_detection)
                closest_t = np.argmin(distances)
                quad_single_track[f] = good_detections[closest_t]
        quad_detections_flat[q] = quad_single_track

    return quad_detections_flat

def clean_detections(detections):
    print(detections.shape)
    good_detections = strip_peaks(detections)
    print(good_detections.shape)
    quad_detections = split_by_quads(good_detections)
    print(quad_detections.shape)
    flat_detections = flatten_by_quads(quad_detections)
    print(flat_detections.shape)
    return flat_detections




if __name__ == "__main__":
    input_video_path = sys.argv[1]
    if len(sys.argv) >= 3:
        output_video_path = sys.argv[2]
    else:
        output_video_path = "./speedtest3.mp4"
    detections,centered_centroids = make_spots(input_video_path,output_video_path,write_video=False,viz=False)

    n_frames = len(detections)
    smoothed_centroids = np.empty_like(centered_centroids)
    smoothed_centroids[:,0] = ndimage.gaussian_filter1d(centered_centroids[:,0],30)
    smoothed_centroids[:,1] = ndimage.gaussian_filter1d(centered_centroids[:,1],30)


    polar_centroids = xy_to_polar(smoothed_centroids)
    polar_vel = np.zeros(len(polar_centroids))
    polar_vel[1:] = np.diff(polar_centroids[:,1])

    #plot_spots(input_video_path,smoothed_centroids,polar_vel)

    clock_wise = polar_vel > MIN_VEL
    contrary_wise = polar_vel < -1 * MIN_VEL
    clock_array = np.full_like(polar_centroids,np.nan)
    contrary_array = np.full_like(polar_centroids,np.nan)
    sit_array = np.full_like(polar_centroids,np.nan)

    clock_array[polar_vel > MIN_VEL] = smoothed_centroids[polar_vel > MIN_VEL]
    contrary_array[polar_vel < -1 * MIN_VEL] = smoothed_centroids[polar_vel < -1 * MIN_VEL]
    sit_array[np.abs(polar_vel) < MIN_VEL] = smoothed_centroids[np.abs(polar_vel) < MIN_VEL]

    from matplotlib import pyplot as plt
    fig,(ax,ax2) = plt.subplots(2,gridspec_kw={'height_ratios':[5,1]})
    #import pdb;pdb.set_trace()
    ax.plot(clock_array[:,0],clock_array[:,1],color='red',alpha=0.5)
    ax.plot(contrary_array[:,0],contrary_array[:,1],color='blue',alpha=0.5)
    ax.plot(sit_array[:,0],sit_array[:,1],color='black',alpha=0.5)
    print(np.sum(~np.isnan(clock_array[:,0])),np.sum(~np.isnan(contrary_array[:,0])),np.sum(~np.isnan(sit_array[:,0])))
    ax.set_xlim([0,CENTER[0]*2])
    ax.set_ylim([0,CENTER[1]*2])

    if False:
        ax2.scatter(np.arange(n_frames)[~np.isnan(clock_array[:,0])],[1]*np.sum(~np.isnan(clock_array[:,0])),color='red')
        ax2.scatter(np.arange(n_frames)[~np.isnan(contrary_array[:,0])],[2]*np.sum(~np.isnan(contrary_array[:,0])),color='blue')
        ax2.scatter(np.arange(n_frames)[~np.isnan(sit_array[:,0])],[3]*np.sum(~np.isnan(sit_array[:,0])),color='black')
    else:
        for l in np.arange(n_frames)[~np.isnan(clock_array[:,0])]:
            ax2.axvline(l,color='red',linewidth=1)
        for l in np.arange(n_frames)[~np.isnan(contrary_array[:,0])]:
            ax2.axvline(l,color='blue',linewidth=1)
        for l in np.arange(n_frames)[~np.isnan(sit_array[:,0])]:
            ax2.axvline(l,color='black',linewidth=1)
    plt.show()

    #detections = np.load('./example_detections_baby.npy')
    #flat_detections = clean_detections(detections)
    #np.save('./example_detections_baby.npy',detections)
    #np.save('./flat_detections_baby.npy',flat_detections)

