import cv2
import sys
from matplotlib import pyplot as plt
import numpy as np


in_file = sys.argv[1]
if ".jpg" in in_file:
    from PIL import Image
    img = Image.open(in_file)
    plt.imshow(img,cmap='gray')
    plt.show()
    
elif ".mp4" in in_file:
    cap = cv2.VideoCapture(in_file)

    while True:
        ret, frame = cap.read()
        if ret == True:
            #break
            cv2.imshow('Frame',frame)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    fig,ax = plt.subplots()
    #gray = np.flipud(gray)

    ax.imshow(gray,cmap='gray')

    plt.show()
    print('Done!')
