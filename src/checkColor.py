import cv2
import numpy as np

tag_ranges = [
    [[55,70,163],[79,255,255]], ## Green
    [[0,0,90],[31,255,255]]     ## Orange
    ]
tag_ranges = np.array(tag_ranges)
def score_img(img_path,tag_ranges = tag_ranges):
    img = cv2.imread(img_path)
    hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)

    scores = []
    for r_ in range(len(tag_ranges)):
        r = tag_ranges[r_]
        #print(r,r[0],r[1])
        colorMask = cv2.inRange(hsv,r[0],r[1])
        score = np.sum(colorMask) / 255
        scores.append(score)
    return scores

if __name__ == "__main__":
    import sys,os
    crops = os.listdir(sys.argv[1])
    #img_path = sys.argv[1]
    count,success = 0,0
    greens = 0 
    for crop in crops:
        img_path = '/'.join([sys.argv[1],crop])
        #print(img_path)
        score = score_img(img_path)
        if score[0] > score[1]:
            success += 1
        if score[0] > 10:
            greens += 1
        count += 1
    print(success,greens,count)
