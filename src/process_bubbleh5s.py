import numpy as np
import pandas as pd

import parse_sleap
import process_h5
import argparse
from shapely.geometry import Point,Polygon,LineString
import json
from tqdm import tqdm
import cv2 

def build_parse():
    parser = argparse.ArgumentParser(description='Required and additional inputs')
    parser.add_argument('--bubbles','-b',required=True,help='Path to bubbles h5 file, output from SLEAP')
    parser.add_argument('--molly','-m',required=True,help='Path to molly h5 file, output from SLEAP')
    parser.add_argument('--annotations','-a',required=True,help='Path to annotation file for the cup and tank locations')
    parser.add_argument('--annotationsC','-a2',required=False,help='Path to annotation file for the cup and tank locations')
    parser.add_argument('--timestamps','-t',required=True,help='Path to annotation file for the experiment time stamps')
    parser.add_argument('--out_csv','-o',required=False,help='Path to csv output, if not specified, uses bubbles filename')
    parser.add_argument('--big_csv','-s',required=False,help='Path to dataset csv, if not specified, no summary is created')
    parser.add_argument('--out_vid','-vv',required=False,help='Path to out mp4, if not specified, no video output')
    parser.add_argument('--in_vid','-i',required=False,help='Path to input mp4, if not specified, no video output')
    parser.add_argument('--visualize','-v',action='store_true',help='option to visualize data')
    parser.add_argument('--start_seconds','-ss',required=False,help='frame on which to start the visualization')
    parser.add_argument('--scale','-k',action='store_true',help='option to convert pixels to cm')
    return parser.parse_args()

def parse_clean(h5_file,node_id=0,clean=True):
    locations,track_occupancy,instance_scores = parse_sleap.read_h5(h5_file)
    a = locations[:,node_id,:,0]
    a_nodes = locations[:,:,:,0]
    
    if clean:
        a_clean = parse_sleap.clear_lone_points(a)
        a_clean,clean_occupancy = parse_sleap.clear_teleports_(a_clean)
        a_clean = parse_sleap.clear_peaks(a_clean)
        a_nodes[np.isnan(a_clean[:,0])] = np.nan
    else:
        a_clean = a
    return a_clean,a_nodes

def get_vel(a):
    simple_vel = np.full(len(a),np.nan)
    simple_diff = np.diff(a,axis=0)
    simple_vel[1:] = np.linalg.norm(simple_diff,axis=1)
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
    a_seg = a_nodes[:,n1] - a_nodes[:,n0] 
    a_ang = calc_angle(a_seg.transpose())
    a_ang = np.abs(a_ang)
    return a_seg,a_ang

def point_angle(f_seg,f_node,t_node):
    inter_line = f_node - t_node 
    inter_angle = calc_angle(f_seg.transpose(),inter_line.transpose())
    return inter_angle
   
def get_anns(ann_file,ann_file2=None):
    with open(ann_file) as f:
        data = json.load(f)

    polygons = {'Cup':[],
                'Tank':[],
                'TankCorners':[]}

    for o in range(len(data['objects'])):
        obj = data['objects'][o]
        title = obj['classTitle']
        obj_type = obj['geometryType']
        if obj_type == 'bitmap':
            continue
        points = obj['points']['exterior']
        polygon = build_poly(points)
        polygons[title].append(polygon)
        if title == 'Tank':
            polygon_ = square_poly(polygon)
            polygons['TankCorners'].append(polygon_)
    if ann_file2 is not None:
        with open(ann_file2) as f2:
            data2 = json.load(f2)
        
        obj = data2['objects'][0]
        points = obj['points']['exterior']
        polygon = build_poly(points)
        polygons['Tank'] = [polygon]
        polygon_ = square_poly(polygon)
        polygons['TankCorners'] = [polygon_]

    return polygons

## Takes a json string, returns a shapely polygon
## This used to be more complex
def build_poly(points):
    polygon = Polygon(points)
    return polygon

## Takes a polygon with more than 6 corners and drops down to 4
def square_poly(polygon):
    p_dists = [[] for p in polygon.exterior.coords]
    all_points = list(polygon.exterior.coords)
    if len(all_points) > 5:
        p_count = 0
        for p in all_points:
            for q in all_points:
                p_dists[p_count].append(Point(p).distance(Point(q)))
            p_count += 1
        p_dists = np.array(p_dists)
        point_ranks = np.argsort(np.mean(p_dists,axis=0))[::-1]
        corners_ = point_ranks[:4]
        good_points = [all_points[c] for c in corners_]
        good_polygon = Polygon(good_points)
        return good_polygon
    else:
        return polygon

def med_radius(polygon):
    centroid = polygon.centroid
    verts = polygon.exterior.coords

    distances = [LineString([centroid,v]).length for v in verts]
    med_dist = np.median(distances)
    return med_dist

def get_pix_scale(polygon,poly_size=10):
    med_dist = med_radius(polygon)*2

    return poly_size / med_dist ## returns cm / pix

## Takes a list, returns a shapely point
def build_point(point):
    pt = Point(point)
    return pt

def edge_dist(point,polygon):
    int_distance = polygon.distance(point) ## if 0, it's inside
    edge_distance = polygon.exterior.distance(point)
    return int_distance,edge_distance

def corner_dist(point,polygon):
    dists = []
    for p in polygon.exterior.coords:
        dists.append(Point(p).distance(point))
    return min(dists)

def get_timestamps(timestamps,vid_name,fps=30):
    vid_line = timestamps[timestamps.goodName == vid_name]
    ts_molly = (int(vid_line['molly_added_minute']) * 60 + int(vid_line['molly_added_second']))*fps
    ts_bubbles = (int(vid_line['bubbles_added_minute']) * 60 + int(vid_line['bubbles_added_second']))*fps
    ts_divider = (int(vid_line['divider_removed_minute']) * 60 + int(vid_line['divider_removed_second']))*fps
    return ts_molly,ts_bubbles,ts_divider

def visualize(vid_file,data_arrays,polygons,dump=True,viz=True,start_seconds=None,out_vid=None):
    cap = cv2.VideoCapture(vid_file)
    if not dump:
        print('writing video...')
        if out_vid is None:
            out_vid = vid_file.replace('mp4','overlay.mp4')
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(out_vid,fourcc,fps,(frame_width,frame_height),isColor=True) 
    tail_length = 100

    t = 0
    if start_seconds is not None:
        frame_number = int(args.start_seconds)
        cap.set(cv2.CAP_PROP_POS_FRAMES,frame_number)
        t = frame_number
    rad=10

    m_track = data_arrays[-2] 
    b_track = data_arrays[-1]
    m_track[np.isnan(m_track)] = 0
    b_track[np.isnan(b_track)] = 0
    m_track = m_track.astype(int)
    b_track = b_track.astype(int)
    tank_corners = list(polygons['TankCorners'][0].exterior.coords)
    cups = [list(c.exterior.coords) for c in polygons['Cup']]
    corner_color = [255,0,0]
    cup_color = [255,150,0]
    inside_array = data_arrays[-4]
    corner_dist = data_arrays[3]

    while(cap.isOpened()):
        ret, frame = cap.read()
        if not ret:
            break
        molly_color = (0,0,255)
        bubbles_color = (0,0,0)
        if inside_array[t] == 1:
            molly_color = cup_color
        if corner_dist[t] < 150 * scale:

            molly_color = corner_color
## Add text
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 1
        fontColor = (255,255,255)
        fontThickness = 2
        for a in range(len(data_arrays)-2):
            
            data_name = base_stats[a] 
            data_txt = str(np.round(data_arrays[a][t],1))
            cv2.putText(frame, ': '.join([data_name,data_txt]),(10,50*(a+1)),font,fontScale,fontColor,fontThickness)
### Add cups
        for c in range(2):
            cup = cups[c]
            cup_pts = np.array(cup).astype(int)
            cup_pts = cup_pts.reshape((-1,1,2))
            cv2.polylines(frame, [cup_pts],isClosed=False,color=cup_color,thickness=5)
## Add Corners
        for c in range(len(tank_corners) - 1):
            #import pdb;pdb.set_trace()
            corner = tank_corners[c]
            cv2.circle(frame,(int(corner[0]),int(corner[1])),radius=150,color=corner_color,thickness=5)
## Add fish
        cv2.circle(frame,(m_track[t,0],m_track[t,1]),radius=rad,color=molly_color,thickness=-1)
        cv2.circle(frame,(b_track[t,0],b_track[t,1]),radius=rad,color=bubbles_color,thickness=-1)
        
## Add trails
        for l in range(0,min(t,tail_length)):
            r = max(2,rad-l)
            cv2.circle(frame,(m_track[t-l,0],m_track[t-l,1]),radius=r,color=molly_color,thickness=-1)
            cv2.circle(frame,(b_track[t-l,0],b_track[t-l,1]),radius=r,color=bubbles_color,thickness=-1)
        if viz:
            cv2.imshow('Overlay',frame)
            k = cv2.waitKey(1)
            if k  == ord('q'):
                viz = False
                if dump:
                    break
            elif k == ord('f'):
                new_frame = input('type int of new frame')
                try:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, int(new_frame))
                    t = int(new_frame-1)
                except:
                    print('invalid input, continuing playback')
            else:
                pass
        if not dump:
            out.write(frame)
        t += 1
        #if t >= len(inside_array):
    if not dump:
        out.release()
    cap.release()
    cv2.destroyAllWindows()
    return 0

if __name__ == '__main__':
    fps = 30
    args = build_parse()
    timestamps = pd.read_csv(args.timestamps,delimiter=',')
    good_stamps = []
    for f in timestamps.video_file_path:
        good_stamps.append(f.split('\\')[-1])
    timestamps['goodName'] = good_stamps
    vid_name = args.bubbles.split('/')[-1]
    vid_name = vid_name.replace('.bubbles.slp.h5','')
    if args.out_csv is None:
        args.out_csv = vid_name.replace('mp4','csv')

    molly_in,bubbles_in,divider_out = get_timestamps(timestamps,vid_name)

    b_track,b_nodes = parse_clean(args.bubbles,node_id=4,clean=False)
    m_track,m_nodes = parse_clean(args.molly,node_id=0,clean=False)

## Calculate distance from molly to bubbles (both mouth and center)
    dist_center = np.linalg.norm(b_track - m_track,axis=1)
    dist_mouth = np.linalg.norm(b_nodes[:,0] - m_track,axis=1)
    
## Get velocity of molly and bubbles
    b_vel,b_diff = get_vel(b_track)
    m_vel,m_diff = get_vel(m_track)

## Get heading of each fish, and the molly orientation in relation to bubbles (m/c)
    b_seg,b_heading = get_heading(b_nodes,n0=0,n1=4)
    m_seg,m_heading = get_heading(m_nodes,n0=0,n1=1)

    molly_mouth_heading = point_angle(m_seg,m_nodes[:,0],b_nodes[:,0])
    molly_mouth_heading = np.abs(molly_mouth_heading)
    molly_mouth_heading[molly_mouth_heading > 180] = 360 - molly_mouth_heading[molly_mouth_heading > 180]

    molly_body_heading = point_angle(m_seg,m_nodes[:,0],b_nodes[:,4])
    molly_body_heading = np.abs(molly_body_heading)
    molly_body_heading[molly_body_heading > 180] = 360 - molly_body_heading[molly_body_heading > 180]
    
    polygons = get_anns(args.annotations,args.annotationsC)
    scale1 = get_pix_scale(polygons['Cup'][0])
    scale2 = get_pix_scale(polygons['Cup'][1])
    scale = np.mean([scale1,scale2])

    inside_array = np.full(len(m_track),np.nan)
    ext_dist_array = np.full(len(m_track),np.nan)
    int_dist_array = np.full(len(m_track),np.nan)
    bubble_cup_dist_array = np.full(len(m_track),np.nan)
    box_dist_array = np.full(len(m_track),np.nan)
    corn_dist_array = np.full(len(m_track),np.nan)
    phase_array = np.zeros(len(m_track))


    buffer = fps * 10
    phase_array[molly_in+buffer:] = 1
    phase_array[bubbles_in:] = 2
    phase_array[divider_out:] = 3
    phase_array[bubbles_in-buffer:bubbles_in+buffer] = 0
    phase_array[divider_out-buffer:divider_out+buffer] = 0

    for i in tqdm(range(len(m_track))):
        if np.isnan(m_track[i,0]):
            continue
        point = build_point(m_track[i])
        bubble_point = build_point(b_track[i])
        
        int_dist1,ext_dist1 = edge_dist(point,polygons['Cup'][0])
        int_dist2,ext_dist2 = edge_dist(point,polygons['Cup'][1])
        int_dist = min([int_dist1,int_dist2])
        ext_dist = min([ext_dist1,ext_dist2])

        int_distB1,_ = edge_dist(bubble_point,polygons['Cup'][0])
        int_distB2,_ = edge_dist(bubble_point,polygons['Cup'][1])
        int_distB = min([int_distB1,int_distB2])

        _,box_dist = edge_dist(point,polygons['Tank'][0])
        corn_dist = corner_dist(point,polygons['TankCorners'][0])
        
        if int_dist == 0:
            inside = 1
        else:
            inside = 0
        ext_dist_array[i] = ext_dist
        int_dist_array[i] = int_dist
        inside_array[i] = inside
        box_dist_array[i] = box_dist
        corn_dist_array[i] = corn_dist
        
        if int_distB == np.inf:
            int_distB = np.nan

        bubble_cup_dist_array[i] = int_distB

### Get averages to add to a new file
    molly_propActive = m_vel > 5
    bubbles_propActive = b_vel > 5
    molly_propCorner = corn_dist_array < 150
    molly_propCup = inside_array
## Base stats for which we'll get mean/std for each phase
## this means each one needs to have an array, so then I can just get _mean1,_std1
    base_stats = ['mollyVel','bubblesVel','molly:edgeDist','molly:cornerDist','molly:cupDist',
        'molly:bodyDist','molly:mouthDist','mbHeading_body','mbHeading_mouth',
        'mollyPropActive','bubblesPropActive','mollyPropCorner','mollyPropCup','bubbles:cupDist']
    base_arrays = [m_vel,b_vel,box_dist_array,corn_dist_array,int_dist_array,
        dist_center,dist_mouth,molly_body_heading,molly_mouth_heading,
        molly_propActive,bubbles_propActive,molly_propCorner,molly_propCup,bubble_cup_dist_array]

    for b in range(len(base_arrays)):
        if args.scale and b in [0,1,2,3,4,5,6,13]:
            base_arrays[b] = np.round(base_arrays[b].astype(float)*scale,4)
        else:
            base_arrays[b] = np.round(base_arrays[b].astype(float),3)

## Build single csv for video
    all_arrays = np.array(base_arrays).transpose()
    csv_df = pd.DataFrame(all_arrays,columns=base_stats)
    csv_df['frame'] = np.arange(len(m_vel))
    csv_df['molly_x'] = np.round(m_track[:,0],3)
    csv_df['molly_y'] = np.round(m_track[:,1],3)
    csv_df['bubbles_x'] = np.round(b_track[:,0],3)
    csv_df['bubbles_y'] = np.round(b_track[:,1],3)

    csv_df.to_csv(args.out_csv,index=False)

    if args.big_csv is not None:
## Append summary stats to entire data csv
        columns = ['video','mollyIn','bubblesIn','dividerOut']
## Now, for each array, get the mean and standard for each phase
## Also add that stat to the columns
        stat_suffix = ['_mean','_std']
        p_suffix = ['1','2','3']

        data_line = [vid_name,molly_in,bubbles_in,divider_out]
## Iterate through stats
        for b in range(len(base_stats)):
            arr = base_arrays[b]
            arr1 = arr[molly_in+buffer:]
            arr2 = arr[bubbles_in+buffer:divider_out-buffer]
            arr3 = arr[divider_out+buffer:]
            sub_arrays = [arr1,arr2,arr3]
            for p in range(3):
                for s in range(2):
                    suffix = ''.join([base_stats[b],stat_suffix[s],p_suffix[p]])
                    columns.append(suffix)
                sub_array = sub_arrays[p]
                sub_mean = np.round(np.nanmean(sub_array),3)
                sub_std = np.round(np.nanstd(sub_array),3)
                if np.isnan(sub_mean):
                    import pdb;pdb.set_trace()
                data_line.append(sub_mean)
                data_line.append(sub_std)
        data_line.append('\n')
        with open(args.big_csv,'a') as f:
            for d in data_line:
                f.write(str(d))
                f.write(',')

    if args.in_vid is not None:
        if args.visualize or args.out_vid is not None:
            base_arrays.append(m_track)
            base_arrays.append(b_track)

            if args.out_vid is not None:
                dump = False
            else:
                dump = True
            visualize(args.in_vid,base_arrays,polygons,dump,args.visualize,args.start_seconds,args.out_vid)

