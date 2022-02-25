#! /usr/bin/env python

## Code for automatically cropping videos based on found tags
# Written by Ammon Perkes for use in the Laskowski Lab
# Contact perkes.ammon@gmail.com for questions


import sys
import cv2

import numpy as np
import subprocess 

## Read in video and grab the first frame: 

in_file = sys.argv[1]
cam_id = sys.argv[2]

crop_dict = {}
try:
    with open("crop_dict.tsv") as f:
        for line in f:
            k,vs = line.split()
            crop_dict[k] = [int(l) for l in vs.split(',')]
except:
    print('Loading crop dictionary failed, going to try my best')
#in_file = '/Users/Ammon/Downloads/IMG_5624.MOV'

## Things to handle; 
# 2. What if the start is black? 
#   = Make sure to make videos that aren't black.
if '.jpg' in in_file:
    frame = cv2.imread(in_file)
else:
    screen_cap = cv2.VideoCapture(in_file)
    ret, frame = screen_cap.read()

#frame = cv2.imread("/Users/Ammon/Downloads/0CD80CB1-ADCB-4465-8389-62F9DF335CB7.JPG")
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

## Find tags
aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_250)
parameters =  cv2.aruco.DetectorParameters_create()
corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
if MANUAL:
    x,y,out_w,out_h = crop_dict[cam_id]
elif len(corners) <= 2:
    if cam_id in crop_dict.keys():
        print('Warning: crop tags could not be identified, checking for hard coded crop')
        x,y,out_w,out_h = crop_dict[cam_id]
    else:
        raise Exception("Couldn't find tags or crops, check your camera and tag positioning")
else:
## Find parameters for ffmpeg crop
    xs,ys = [],[]
    for c in corners:
        x,y = np.mean(c,axis=1)[0].astype(int)
        xs.append(x)
        ys.append(y)


    xmin = np.min(xs)
    xmax = np.max(xs)
    ymin = np.min(ys)
    ymax = np.max(ys)


    out_w = xmax - xmin
    out_h = ymax - ymin

    x = xmin
    y = ymin

    X,Y,_ = frame.shape
    max_dim = max([X,Y])
    min_dim = min([X,Y])

    if len(corners) < 4 or len (corners > 4):
        print('Got a different number of corners than expected, going to do my best though.')

## Check if the shape is weird, this generally happens when one of the tags are missing
    if max_dim / min_dim > 4:
        print('Warning: proportion is a bit wonky, you should check this one')

    if '.MOV' in in_file: ## Note that open CV doesn't know anything about reference frame, but ffmpeg apparently does
        # So we may need to use ffmpeg to ensure rotational consistency. 
        out_w = ymax - ymin
        out_h = xmax - xmin
        x = ymin
        y = xmin

## Crop video
print(out_w,out_h,x,y)
out_file = in_file.replace('.','_crop.')
command = f'ffmpeg -i "{in_file}" -filter:v "crop={out_w}:{out_h}:{x}:{y}" "{out_file}"'
subprocess.call(command, shell=True)
