import sys

with open('vid_inbox.txt') as f:
    VIDEOS = f.read().splitlines()

with open('inbox_paths.txt') as f:
    BOX_PATHS = f.read().splitlines()

print('Videos to process:', VIDEOS, file=sys.stderr)

with open('crop_dict.tsv') as crop_f:
    crop_dict = ## process_cropdict

with open('center_dict.tsv') as center_f:
    center_dict = ## process_centerdict

rule all:
    input:
        expand("aperkes:{box_path}",box_path=BOX_PATHS),
        expand("working_dir/videos/{video}.mp4",video=VIDEOS),
        expand("working_dir/crops/{video}.crop.mp4",video=VIDEOS),
        expand("working_dir/spots/{video}.spot.mp4",video=VIDEOS),
        expand("working_dir/sleaps/{video}.slp",video=VIDEOS),
        expand("working_dir/h5/{video}.h5",video=VIDEOS),
        expand("working_dir/csv/{video}.csv",video=VIDEOS),
        expand("working_dir/txt/{video}.txt",video=VIDEOS)

rule copy_video:
    output: temporary("working_dir/videos/{video}.mp4")
    input:
        remote = "aperkes:{box_path}"
    threads: 2
    run:
        shell("rclone copy {remote}{videos}.mp4 working_dir/videos/{videos}.mp4")

rule crop_video:
    output: temporary("working_dir/crops/{video}.crop.mp4")
    input: 
        infile = "working_dir/videos/{video}.mp4"
    threads: 4
    run:
        shell("python crop_by_dict -x current_dict")

rule upload_crop:
    input:  "working_dir/crops/{video}.crop.mp4"
    threads: 1
    run:
        shell("rclone copy {input} {remote}.crop.mp4")

rule spot_video:
    output: temporary("working_dir/spots/{video}.spot.mp4")
    threads: 4
    input:  "working_dir/crops/{video}.crop.mp4"
    run:
        shell("conda activate tracking")
        shell("python spotlight.py {input}")

rule upload_spot:
    input:  "working_dir/spots/{video}.spot.mp4"
    threads: 1
    run:
        shell("rclone copy {input} {remote}.spot.mp4")        

rule inference:
    output: temporary("working_dir/sleap/{video}.slp")
    input:  "working_dir/spots/{video}.spot.mp4"
    threads: 1
    run:
        shell("conda activate sleap")
        shell("sleap-track -i {input} ....")

rule convert_h5:
    output: temporary("working_dir/h5/{video}.h5")
    input:  "working_dir/sleap/{video}.slp"

    run:
        shell("conda activate sleap")
        shell("sleap-convert -i {input.slp} .... ")

rule upload_h5:
    input:  "working_dir/h5/{video}.h5"
    threads: 1
    run:
        shell("rclone copy {input} {remote}:{path}{video}.h5")

rule process_h5:
    output: 
        "results/csv/{video}.csv"
        "results/txt/{video}.csv"
    input:  "working_dir/h5/{video}.h5"
    run:
        shell("python process_h5.py -i {input.h5}")
