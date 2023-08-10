#! /usr/bin/env python

## Code for automatically cropping videos based on found tags
# Written by Ammon Perkes for use in the Laskowski Lab
# Contact perkes.ammon@gmail.com for questions

## This code requires as input an image, or a video. 
## If video, it will work off the first frame, so if the first frame is black it will fail.


import sys
import cv2

import numpy as np
import subprocess 

import argparse

DEFAULT_CROP = '/home/ammon/Documents/Scripts/FishTrack/src/current_crop.tsv'

def build_parse():
    parser = argparse.ArgumentParser(description='Required and additional inputs')
    parser.add_argument('--in_file','-i',required=True,help='Path to input img or video')
    parser.add_argument('--out_file','-o',required=False,help='Path to output, if not specified, goes to in_file.crop.mp4')
    parser.add_argument('--crop_list','-x',default=DEFAULT_CROP,help='Optional crop dict to specify locations')
    parser.add_argument('--force_dict','-m',action='store_true',help='If included, it will only use the specified dictionary. Requires id and crop_dict')
    parser.add_argument('--id','-c',required=False,help='Camera id, required if using the crop dict')
    return parser.parse_args()


args = build_parse()
in_file = args.in_file

crop_dict = {}
import pdb;pdb.set_trace()

if args.force_dict:
    if args.crop_list == None:
        raise Exception('Using Force dict, but you no crop_dict included. Be sure to include the ID and the crop_dict')

## Read in video and grab the first frame: 

if args.crop_list is not None:
    #try:
    with open(args.crop_list) as f:
        for line in f:
            k,vs = line.split()
            crop_dict[k] = [int(l) for l in vs.split(',')]
    #except:
    #    print('Loading crop dictionary failed, going to try my best')

if args.id == None:
    for k in crop_dict.keys():
        if k in args.in_file:
            args.id = k

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
if args.force_dict:
    x,y,out_w,out_h = crop_dict[args.id]
elif len(corners) <= 2:
    print(crop_dict.keys())
    print(args.id)
    if args.id in crop_dict.keys():
        print('Warning: crop tags could not be identified, checking for hard coded crop')
        x,y,out_w,out_h = crop_dict[args.id]
    else:
        raise Exception("Couldn't find tags or crops, check your camera and tag positioning, or include a dict.tsv with crop instructions")
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

    if len(corners) < 4 or len(corners) > 4:
        print('Got a different number of corners than expected, going to do my best though.')

## Check if the shape is weird, this generally happens when one of the tags are missing
    if max_dim / min_dim > 4:
        print('Warning: proportion is a bit wonky, you should check this one')
        if args.id in crop_dict.keys():
            x,y,out_w,out_h = crop_dict[args.id]
        else:
            raise Exception("Tags failed and I couldn't find a dict, check your camera and tag positioning, or include a dict.tsv with crop instructions")
    if out_w < 500 or out_h < 500:
        print('Warning: Video too small, you should check this too')

        if args.id in crop_dict.keys():
            x,y,out_w,out_h = crop_dict[args.id]
        else:
            raise Exception("Tags failed and I couldn't find a dict, check your camera and tag positioning, or include a dict.tsv with crop instructions")
    if '.MOV' in in_file: ## Note that open CV doesn't know anything about reference frame, but ffmpeg apparently does
        # So we may need to use ffmpeg to ensure rotational consistency. 
        out_w = ymax - ymin
        out_h = xmax - xmin

        x = ymin
        y = xmin

## Crop video
print(out_w,out_h,x,y)
if args.out_file is not None:
    out_file = args.out_file
else:
    out_file = '.crop.'.join(in_file.rsplit('.',1)) ## sort of hacky line to replace .jpg with .crop.jpg without touching any preceding .'s 

command = f'ffmpeg -i "{in_file}" -filter:v "crop={out_w}:{out_h}:{x}:{y}" -c:v libx264 -crf 15 "{out_file}" -y'

subprocess.call(command, shell=True)
