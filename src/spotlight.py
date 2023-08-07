import cv2
import sys

## Code to run background subtraction on fish. First pass was ChatGPT, so probably just stolen from stack exchange somewhere.

def perform_background_subtraction(input_video, output_video):
    # Create a background subtraction object
    bg_subtractor = cv2.bgsegm.createBackgroundSubtractorMOG()

    MOG = True
    VIZ = False
    if not MOG:
        bg_subtractor = cv2.bgsegm.createBackgroundSubtractorGMG()
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))

    # Open the input video file
    video_capture = cv2.VideoCapture(input_video)
    fps = int(video_capture.get(cv2.CAP_PROP_FPS))
    frame_width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Define the codec and create VideoWriter object for output video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (frame_width, frame_height), isColor=True)

    count = 0
    print('working on it, expect it to take around 15 min')
    #import time
    #start = time.time()
    while True:
        #if count % 100 == 0:
        #    print('frame:',count)
        #    print(time.time() - start)
        #count += 1
        ret, frame = video_capture.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #gray = cv2.pyrDown(gray) ## this reduces quality but dramatically increases speeds (3x) 
        # Apply background subtraction
        fg_mask = bg_subtractor.apply(gray)

        #if not MOG:
        #    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (100,100))
        #kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (50,50))
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=1)

        # Invert the foreground mask (black is foreground, white is background)
        
        # Set the foreground to black and the background to white
        #fg_mask = cv2.pyrUp(fg_mask)
        black_background = cv2.bitwise_and(frame,frame,mask= fg_mask)

        # Write the frame to the output video
        out.write(black_background)

        #out.write(frame)
        # Display the original video and the background-subtracted video (for debugging)
        #if VIZ:
        #    cv2.imshow("Original Video", frame)
        #    cv2.imshow("Foreground Mask", fg_mask)
        #    cv2.imshow("Black Background", black_background)

    # Release video capture and writer objects
    video_capture.release()
    out.release()

    # Destroy all OpenCV windows
    cv2.destroyAllWindows()

if __name__ == "__main__":
    input_video_path = sys.argv[1]
    if len(sys.argv) >= 3:
        output_video_path = sys.argv[2]
    else:
        output_video_path = "./speedtest2.mp4"
    perform_background_subtraction(input_video_path, output_video_path)
