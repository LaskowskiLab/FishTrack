import cv2,sys
import time
import numpy as np

# Create a VideoCapture object and read from input file
# If the input is the camera, pass 0 instead of the video file name
#output_video = ('./test_spots.mp4')

def make_spots(input_video,output_video):
    cap = cv2.VideoCapture(input_video)
    bg_subtractor = cv2.bgsegm.createBackgroundSubtractorMOG()
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
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
        #cv2.imshow('Frame',frame)

        gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        small = cv2.pyrDown(gray)
        fg_mask = bg_subtractor.apply(small)


        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10,10))
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=1)

        fg_mask = cv2.pyrUp(fg_mask)
        black_background = cv2.bitwise_and(gray,gray,mask=fg_mask)

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
        out.write(frame)
# Press Q on keyboard to  exit
        #if cv2.waitKey(5) & 0xFF == ord('q'):
        #    break
     
# When everything done, release the video capture object
    cap.release()
     
# Closes all the frames
    cv2.destroyAllWindows()

    return detections

if __name__ == "__main__":
    input_video_path = sys.argv[1]
    if len(sys.argv) >= 3:
        output_video_path = sys.argv[2]
    else:
        output_video_path = "./speedtest3.mp4"
    detections = make_spots(input_video_path,output_video_path)
    np.save('./example_detections.npy',detections)
