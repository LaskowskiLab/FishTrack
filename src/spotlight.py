import cv2,sys
import time

# Create a VideoCapture object and read from input file
# If the input is the camera, pass 0 instead of the video file name
#output_video = ('./test_spots.mp4')

def make_spots(input_video,output_video):
    cap = cv2.VideoCapture(input_video)
    bg_subtractor = cv2.bgsegm.createBackgroundSubtractorMOG()

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (frame_width, frame_height), isColor=False)

# Check if camera opened successfully
    if (cap.isOpened()== False): 
        print("Error opening video stream or file")
     
    start = time.time()
    count = 0
# Read until video is completed
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

        #cv2.imshow('Black',black_background)
        #cv2.imshow('White',fg_mask)
        out.write(fg_mask)
# Press Q on keyboard to  exit
        #if cv2.waitKey(5) & 0xFF == ord('q'):
        #    break

     
# When everything done, release the video capture object
    cap.release()
     
# Closes all the frames
    cv2.destroyAllWindows()

if __name__ == "__main__":
    input_video_path = sys.argv[1]
    if len(sys.argv) >= 3:
        output_video_path = sys.argv[2]
    else:
        output_video_path = "./speedtest3.mp4"
    make_spots(input_video_path,output_video_path)
