import numpy as np

import parse_sleap
import process_h5
import argparse
from shapely import wkt
import json
from tqdm import tqdm

def build_parse():
    parser = argparse.ArgumentParser(description='Required and additional inputs')
    parser.add_argument('--bubbles','-b',required=True,help='Path to bubbles h5 file, output from SLEAP')
    parser.add_argument('--molly','-m',required=True,help='Path to molly h5 file, output from SLEAP')
    parser.add_argument('--annotations','-a',required=True,help='Path to annotation file for the cup and tank locations')
    parser.add_argument('--out_file','-o',required=False,help='Path to csv output, if not specified, uses bubbles filename')
    return parser.parse_args()

def parse_clean(h5_file,node_id=0):
    locations,track_occupancy,instance_scores = parse_sleap.read_h5(h5_file)
    a = locations[:,node_id,:,0]
    a_nodes = locations[:,:,:,0]
    
    a_clean = parse_sleap.clear_lone_points(a)
    a_clean,clean_occupancy = parse_sleap.clear_teleports_(a_clean)
    a_clean = parse_sleap.clear_peaks(a_clean)
    a_nodes[np.isnan(a_clean[:,0])] = np.nan
    return a_clean,a_nodes

def get_vel(a):
    simple_diff = np.diff(a,axis=0)
    simple_vel = np.linalg.norm(simple_diff,axis=1)
    return simple_vel,simple_diff

def calc_angle(X,Y=None,deg=True):
    ang1 = np.arctan2(*X)
    if Y is not None:
        ang2 = np.arctan2(*Y)
        ang = (ang1 - ang2) % (2 * np.pi)
    else:
        ang = ang1
    if deg:
        return np.rad2deg(ang)
    else:
        return ang

def get_heading(a_nodes,n0=0,n1=1):
    a_seg = a_nodes[:,n0] - a_nodes[:,n1] 
    a_ang = calc_angle(a_seg.reshape([2,-1]))
    return a_seg,a_ang

def point_angle(f_seg,f_node,t_node):
    inter_line = f_node - t_node 
    inter_angle = calc_angle(f_seg.reshape([2,-1]),inter_line.reshape([2,-1]))
    return inter_angle
   
def get_anns(ann_file):
    with open(ann_file) as f:
        data = json.load(f)

    polygons = {'Cup':[],
                'Tank':[]}

    for o in range(len(data['objects'])):
        obj = data['objects'][o]
        title = obj['classTitle']
        obj_type = obj['geometryType']
        if obj_type == 'bitmap':
            continue
        points = obj['points']['exterior']
        polygon = build_poly(points)
        polygons[title].append(polygon)
    return polygons

## Takes a json string, returns a shapely polygon
def build_poly(points):
## Lots of silly string parsing
    points_str = str(points)
    points_str = points_str.replace('[','')[:-2]
    points_str = points_str.replace(',','')
    points_str = points_str.replace(']',',')
    points_str = points_str + ', ' + points_str.split(',')[0]
    polygon_str = ''.join(['POLYGON((',points_str,'))'])
    polygon = wkt.loads(polygon_str)
    return polygon

## Takes a list, returns a shapely point
def build_point(point):
    x,y = point.astype(int)
    x,y = str(x),str(y)
    pt = wkt.loads(''.join(['POINT(',x,' ',y,')']))
    return pt

def edge_dist(point,polygon):
    int_distance = polygon.distance(point) ## if 0, it's inside
    edge_distance = polygon.exterior.distance(point)
    return int_distance,edge_distance

if __name__ == '__main__':

    args = build_parse()
    b_track,b_nodes = parse_clean(args.bubbles,node_id=4)
    m_track,m_nodes = parse_clean(args.molly,node_id=0)


## Calculate distance from molly to bubbles (both mouth and center)
    dist_center = np.linalg.norm(b_track - m_track,axis=1)
    dist_mouth = np.linalg.norm(b_nodes[:,0] - m_track,axis=1)
    
## Get velocity of molly and bubbles
    b_vel,b_diff = get_vel(b_track)
    m_vel,m_diff = get_vel(m_track)

## Get heading of each fish, and the molly orientation in relation to bubbles (m/c)
    b_seg,b_heading = get_heading(b_nodes,n0=0,n1=4)
    m_seg,m_heading = get_heading(b_nodes,n0=0,n1=1)

    m_to_mouth = (m_seg,m_nodes[0],b_nodes[0])
    m_to_body = (m_seg,m_nodes[0],b_nodes[4])

    polygons = get_anns(args.annotations)
    inside_array = np.full(len(m_track),np.nan)
    ext_dist_array = np.full(len(m_track),np.nan)
    int_dist_array = np.full(len(m_track),np.nan)
    for i in tqdm(range(len(m_track))):
        if np.isnan(m_track[i,0]):
            continue
        point = build_point(m_track[i])
        
        int_dist,ext_dist = edge_dist(point,polygons['Cup'][0])
        if int_dist == 0:
            inside = 1
        else:
            inside = 0
        ext_dist_array[i] = ext_dist
        int_dist_array[i] = int_dist
        inside_array[i] = inside
    import pdb;pdb.set_trace()

### Get molly distance to cups

    
if False:
    tracks_copy = np.array(locations)
    trimmed_tracks,track_occupancy_trim = parse_sleap.clear_peaks_all(tracks_copy,track_occupancy,stds=3)

    single_track,single_occupancy = parse_sleap.overlay_tracks(trimmed_tracks,track_occupancy_trim,instance_scores,min_track=2)
    slowed_track = parse_sleap.clear_superspeed(single_track,max_speed=200)
    clean_track,clean_occupancy = parse_sleap.clear_teleports_(slowed_track,max_distance = 300,min_track = 2)
    interpolated_track = np.empty_like(clean_track)
    interpolated_track[:,0] = parse_sleap.interp_track(clean_track[:,0])
    interpolated_track[:,1] = parse_sleap.interp_track(clean_track[:,1])

    velocity = process_h5.smooth_diff(clean_track)
    median_velocity = np.round(np.nanmedian(velocity),3)

    prop_active = np.round(np.nansum(velocity > 10) / np.sum(~np.isnan(velocity)),3)
    prop_visible = np.round(np.sum(~np.isnan(clean_track)) / len(clean_track),3)

    visible_track = clean_track[~np.isnan(clean_track[:,0])]

    corner_size = [200,200]
    img_size = [500,500]

    file_name = h5_file.split('/')[-1]
    file_parts = file_name.split('.')
    base_name = '.'.join(file_parts[:6])

#import pdb;pdb.set_trace()
## This depends on if there's a crop or not...
    quadrant = file_parts[7]
    substrate = file_parts[8]

    quadrant_ = int(quadrant)
    if quadrant_ == 0:
        corner_xs = visible_track[:,0] < corner_size[0]
        corner_ys = visible_track[:,1] < corner_size[1]
    elif quadrant_ == 1:
        corner_xs = visible_track[:,0] > (img_size[0] - corner_size[0])
        corner_ys = visible_track[:,1] < corner_size[1]
    elif quadrant_ == 2:
        corner_xs = visible_track[:,0] < corner_size[0]
        corner_ys = visible_track[:,1] > (img_size[1] - corner_size[1])
    elif quadrant_ == 3:
        corner_xs = visible_track[:,0] > (img_size[0] - corner_size[0])
        corner_ys = visible_track[:,1] > (img_size[1] - corner_size[1])

#import pdb;pdb.set_trace()
    corner_count = np.sum(np.logical_and(corner_xs,corner_ys))
    corner_ratio = np.round(corner_count / len(visible_track),3)

    with open(csv_file,'a') as f:
        f_line = ','.join([base_name,quadrant,str(prop_visible),str(median_velocity),str(prop_active),str(corner_ratio),substrate])
        f.write(f_line + '\n') 

    print(f_line)

