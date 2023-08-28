import cv2
import sys
from matplotlib import pyplot as plt
import numpy as np


in_file = sys.argv[1]
cap = cv2.VideoCapture(in_file)

while True:
    ret, frame = cap.read()
    if ret == True:
        cv2.imshow('Frame',frame)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()

gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

fig,ax = plt.subplots()
#gray = np.flipud(gray)

ax.imshow(gray)

plt.show()
print('Done!')
