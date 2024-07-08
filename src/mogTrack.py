import cv2,sys
import time
import numpy as np
import parse_sleap
import math 

## This is a proper implementation of tracking
# I made it for kirsten's project, assumes adult fish with little noise

## cribbed from https://stackoverflow.com/a/62701632
fMIN,fMAX = 30,100
VIZ = True
SAVE = False

def draw_ellipse(ellipse,img):
    (xc,yc),(d1,d2),angle = ellipse
    #print(xc,yc,d1,d1,angle)

# draw ellipse in green
    result = img
    if img is not None:
        cv2.ellipse(result, ellipse, (0, 255, 0), 3)

# draw circle at center
    xc, yc = ellipse[0]
    if img is not None:
        cv2.circle(result, (int(xc),int(yc)), 10, (255, 255, 255), -1)

# draw major axis line in red
    rmajor = max(d1,d2)/2
    if angle > 90:
        angle = angle - 90
    else:
        angle = angle + 90
    #print(angle)
    x1 = xc + math.cos(math.radians(angle))*rmajor
    y1 = yc + math.sin(math.radians(angle))*rmajor
    x2 = xc + math.cos(math.radians(angle+180))*rmajor
    y2 = yc + math.sin(math.radians(angle+180))*rmajor
    if img is not None:
        cv2.line(result, (int(x1),int(y1)), (int(x2),int(y2)), (0, 0, 255), 3)
    major_axis = (int(x1),int(y1)),(int(x2),int(y2))

# draw minor axis line in blue
    rminor = min(d1,d2)/2
    if angle > 90:
        angle = angle - 90
    else:
        angle = angle + 90
    #print(angle)
    x1 = xc + math.cos(math.radians(angle))*rminor
    y1 = yc + math.sin(math.radians(angle))*rminor
    x2 = xc + math.cos(math.radians(angle+180))*rminor
    y2 = yc + math.sin(math.radians(angle+180))*rminor
    minor_axis = (int(x1),int(y1)),(int(x2),int(y2))

    if img is not None:
        cv2.line(result, (int(x1),int(y1)), (int(x2),int(y2)), (255, 0, 0), 3)

    return major_axis,minor_axis

## cribbed from https://stackoverflow.com/questions/28759253/how-to-crop-the-internal-area-of-a-contour
def crop_contours(frame,contours,idx=0):
    for c_ in range(len(contours)):
        c = contours[c_]
        mask = np.zeros_like(frame[:,:,0])
        cv2.drawContours(mask,[c],-1,255,-1)
        out = np.zeros_like(frame)
        out[mask == 255] = frame[mask == 255]
        (y,x) = np.where(mask == 255)
        (y,x) = np.where(mask == 255)
        (topy, topx) = (np.min(y), np.min(x))
        (bottomy, bottomx) = (np.max(y), np.max(x))
        out = out[topy:bottomy+1, topx:bottomx+1]
        if VIZ:
            cv2.imshow('Output',out)
            cv2.waitKey(1)
        if SAVE:
            f_name = './crops/crop.' + str(idx).zfill(7) + '.' + str(c_).zfill(3) + '.png'
            cv2.imwrite(f_name,out)
    return 0

def make_spots(input_video,output_video,write_video=True):
    cap = cv2.VideoCapture(input_video)
    #bg_subtractor = cv2.bgsegm.createBackgroundSubtractorMOG()
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
    idx = 0
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
        if VIZ:
            cv2.imshow('Frame',frame)

        gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        small = cv2.pyrDown(gray)
        fg_mask = bg_subtractor.apply(small)

        if VIZ:
            cv2.imshow('raw mask',fg_mask)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=1)
        fg_mask = cv2.erode(fg_mask, kernel, iterations=2)
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=1)

        fg_mask = cv2.pyrUp(fg_mask)

        contours, hierarchy = cv2.findContours(fg_mask,cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        fishes = []
        fcontours = []
        for c in contours:
            #import pdb;pdb.set_trace()
            if len(c) > 10:
                ellipse = cv2.fitEllipse(c)
                (xc,yc),(d1,d2),angle = ellipse
                if max(d1,d2) > fMIN and max(d1,d2) < fMAX:
                    fishes.append(ellipse)
                    fcontours.append(c)
                    #draw_ellipse(ellipse,gray)
                #cv2.ellipse(frame,ellipse,(0,0,255),3)
        crop_contours(frame,contours,idx)
        if VIZ:
            cv2.drawContours(frame,contours,-1,(255,0,0),3)

            black_background = cv2.bitwise_and(gray,gray,mask=fg_mask)
            cv2.imshow('Mask',fg_mask)
            cv2.imshow('Contours',frame)

            key = cv2.waitKey(1)
            if key == 27:
                cv2.destroyAllWindows()
                break
        
        if len(contours) > 0:
            frame_detections = [np.mean(c[:,0],0) for c in contours]
            frame_detections = frame_detections[:MAX_DETECTIONS]
            n_detections = len(frame_detections)
            detections[count-1,:n_detections] = np.array(frame_detections)

        #cv2.imshow('Black',black_background)
        #cv2.imshow('White',fg_mask)
        #out.write(fg_mask)
        idx = idx + 1
        if idx % 100 == 0:
            print('Frame:',idx)

        if idx > 2000:
            pass
            #break
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

def clean_detections(detections):
    print(detections.shape)
    good_detections = strip_peaks(detections)
    print(good_detections.shape)
    return good_detections

if __name__ == "__main__":
    input_video_path = sys.argv[1]
    if len(sys.argv) >= 3:
        output_video_path = sys.argv[2]
    else:
        output_video_path = "./speedtest3.mp4"
    detections = make_spots(input_video_path,output_video_path,write_video=False)
    #detections = np.load('./example_detections_baby.npy')
    #flat_detections = clean_detections(detections)
    #np.save('./example_detections_baby.npy',detections)
    #np.save('./flat_detections_baby.npy',flat_detections)

