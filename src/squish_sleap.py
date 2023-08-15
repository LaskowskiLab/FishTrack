import sleap
import numpy as np
from rich.progress import track as track_progress
import matplotlib.pyplot as plt
import sys

## Code to trim .slp predictions down to a manageable number to prevent memory overflow
# Adapted from code from Talmo Pereira (https://gist.github.com/talmo/a5415218c194536092cda10f897f8cad) 

#session = "220914_095059_18159211_rig1_1"

in_file = sys.argv[1]
labels = sleap.load_file(in_file)

max_instances = 200

ref_tracks = set()
track_map = {}
track_ends = {}

for lf in track_progress(labels):
    if len(ref_tracks) < max_instances:
        for inst in lf:
            if inst.track not in ref_tracks:
                ref_tracks.add(inst.track)
                track_ends[inst.track] = inst

    matched_ref_tracks = set()
    unmatched_insts = []
    for inst in lf:
        if inst.n_visible_points == 0:
            lf.instances.remove(inst)
            continue

        if inst.track in track_map:
# Extra track can be mapped to a reference track.
            inst.track = track_map[inst.track]
            matched_ref_tracks.add(inst.track)

        elif inst.track not in ref_tracks:
# Extra track needs to be matched to a reference track.
            unmatched_insts.append(inst)

    if len(unmatched_insts) > 0:
# Find reference tracks that have not been assigned yet.
        available_ref_tracks = list(ref_tracks - matched_ref_tracks)

# Build matching cost matrix.
        cost_matrix = np.full((len(available_ref_tracks), len(unmatched_insts)), np.nan)
        for i, ref_track in enumerate(available_ref_tracks):
            ref_inst = track_ends[ref_track]
            for j, unmatched_inst in enumerate(unmatched_insts):
                cost_matrix[i, j] = sleap.nn.evals.compute_oks(
                    np.expand_dims(ref_inst.numpy(), axis=0),
                    np.expand_dims(unmatched_inst.numpy(), axis=0),
                )

# Match and assign tracks.
        available_inds, unmatched_inds = sleap.nn.utils.linear_sum_assignment(cost_matrix, maximize=True)

        for i, j in zip(available_inds, unmatched_inds):
            matched_track = available_ref_tracks[i]
            track_map[unmatched_insts[j].track] = matched_track
            unmatched_insts[j].track = matched_track
# Update track ends.
        for inst in lf:
            track_ends[inst.track] = inst

labels.tracks = list(ref_tracks)

out_file = in_file.replace('.slp','.squished.slp')
labels.save(out_file)
