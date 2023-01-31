#! /usr/bin/env python

## Code to process the .npz readouts from Trex
## written by Ammon for use in the Laskowski Lab, for questions contact perkes.ammon@gmail.com

import numpy as np
import argparse
from matplotlib import pyplot as plt

## Build argument parser
def build_parse():
    parser = argparse.ArgumentParser(description='Required and additional inputs')
    parser.add_argument('--input_file','-i',required=True,help='Path to the input file, a .npz')
    parser.add_argument('--output_file','-o',required=False,default=None,help='Path to output, if not specified, goes to the same place as input')
    parser.add_argument('--verbose','-v',required=False,action='store_true',help='use for printing information')
    parser.add_argument('--head','-m',required=False,action='store_true',help='Include header string of meta data')
    parser.add_argument('--showplot','-p',required=False,action='store_true',help='Optionally visualize the plot')
    parser.add_argument('--saveplot','-s',required=False,action='store_true',help='Optionally save the plot')
    return parser.parse_args()

## Parse the file string to get relevent info. Requires string to be parsed correctly
def get_meta(input_path):
    file_name = input_path.split('/')[-1]
    file_name = file_name.replace('.npz','')
    split_name = file_name.split('.')
    meta_dict = {}
    meta_dict['date'] = str('-'.join(split_name[3:6]))
    meta_dict['tank'] = split_name[0]
    ext_name = split_name[-1]
    meta_dict['fish'] = ext_name.split('_')[-1]

    return meta_dict

## Calculate the stats we want
def get_stats(file_object):
    stat_dict = {}

## Have to remove infinite values (not sure why these exist...)
    speed = file_object['SPEED']
    speed[speed == np.inf] = np.nan
    speed[speed == -np.inf] = np.nan
    stat_dict['mean_speed'] = np.nanmean(speed)
## The rest should be good
    stat_dict['droppped_frames'] = np.sum(file_object['missing'])
    stat_dict['total_frames'] = len(file_object['missing'])
    return stat_dict
    
def plot_array(pos_array):    
    fig,ax = plt.subplots()
    ax.scatter(pos_array[1],pos_array[2],alpha=.01,marker='.')
    return fig,ax

if __name__ == '__main__':
    args = build_parse()
    file_object = np.load(args.input_file)
    if args.verbose:
        print('loading file:',args.input_file)
        print('included data:',list(file_object.keys()))
    xs = file_object['X']
    ys = file_object['Y']
    ts = file_object['timestamp']
    drops = file_object['missing']
    vs = file_object['SPEED']

    out_table = np.array([ts,xs,ys,vs,drops])
    out_table = out_table.transpose()

    if args.output_file is not None:
        out_name = args.output_file
    else:
        out_name = args.input_file.replace('.npz','.csv')
    if args.head:
## Combine the meta and stats into a header line
        col_names = 'Time,X,Y,Velocity,dropped frame,Meta:,'
        if True:
            stat_dict = get_stats(file_object)
            meta_dict = get_meta(args.input_file)
            head_string = col_names + str(meta_dict)[1:-1] + ',' + str(stat_dict)[1:-1]
        else:
            print('Input name formatted incorrectly, using file path for header')
            head_string = 'Input path: ' + args.input_file
    else:
        head_string = ''

    np.set_printoptions(suppress=True)
    np.savetxt(out_name,out_table,delimiter=',',header=head_string,fmt=['%d','%1.3f','%1.3f','%1.3f','%d'])

    if args.showplot or args.saveplot:
        fig,ax = plot_array(np.array([ts,xs,ys]))
        if args.showplot:
            plt.show()
        if args.saveplot:
            plt.savefig(out_name + '.png',dpi=300)
