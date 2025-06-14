import cv2,sys
import time
import numpy as np
import parse_sleap

# Create a VideoCapture object and read from input file
# If the input is the camera, pass 0 instead of the video file name
#output_video = ('./test_spots.mp4')

def make_spots(input_video,output_video,write_video=True):
    cap = cv2.VideoCapture(input_video)
    try:
        bg_subtractor = cv2.bgsegm.createBackgroundSubtractorMOG()
    except:
        bg_subtractor = cv2.createBackgroundSubtractorMOG2()
        
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
    while(cap.isOpened()):
        # Capture frame-by-frame
        #if count % 100 == 0:
        #    #print('frame:',count)
        #    #print(time.time() - start)
        count += 1
        ret, frame = cap.read()
        if not ret:
            break 
# Display the resulting frame
        cv2.imshow('Frame',frame)

        gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        small = cv2.pyrDown(gray)
        fg_mask = bg_subtractor.apply(small)


        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10,10))
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=1)
        fg_mask = cv2.erode(fg_mask, kernel, iterations=1)

        fg_mask = cv2.pyrUp(fg_mask)


        black_background = cv2.bitwise_and(gray,gray,mask=fg_mask)
        cv2.imshow('Mask',black_background)

        key = cv2.waitKey(10)
        if key == 27:
            cv2.destroyAllWindows()
            break
        contours, hierarchy = cv2.findContours(fg_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) > 0:
            frame_detections = [np.mean(c[:,0],0) for c in contours]
            frame_detections = frame_detections[:MAX_DETECTIONS]
            n_detections = len(frame_detections)
            detections[count-1,:n_detections] = np.array(frame_detections)

        cv2.drawContours(frame,contours,-1,(255,0,0),3)

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

    return detections

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
    detections = make_spots(input_video_path,output_video_path,write_video=True)
    #detections = np.load('./example_detections_baby.npy')
    #flat_detections = clean_detections(detections)
    #np.save('./example_detections_baby.npy',detections)
    #np.save('./flat_detections_baby.npy',flat_detections)

