import sys

with open('vid_inbox.txt') as f:
    VIDEOS = f.read().splitlines()

with open('inbox_paths.txt') as f:
    BOX_PATHS = f.read().splitlines()

print('Videos to process:', VIDEOS, file=sys.stderr)

rule all:
    input:
        #expand("aperkes:{box_path}",box_path=BOX_PATHS),
        expand("../working_dir/videos/{video}.mp4",video=VIDEOS),
        expand("../working_dir/crops/{video}.crop.mp4",video=VIDEOS),
        expand("../working_dir/spots/{video}.spot.mp4",video=VIDEOS),
        expand("../working_dir/sleap/{video}.slp",video=VIDEOS),
        expand("../working_dir/h5/{video}.h5",video=VIDEOS),
        expand("../results/csv/{video}.csv",video=VIDEOS),
        expand("../results/txt/{video}.txt",video=VIDEOS)

rule copy_video:
    output: temporary("../working_dir/videos/{video}.mp4")
    #input:  
    #    ["{box_path}".format(box_path=box_path) for box_path in BOX_PATHS]
    #    #expand("aperkes:{box_path}",box_path=BOX_PATHS)
    threads: 2
    run:
        #shell("rclone copy {input}{videos}.mp4 ../working_dir/videos/{videos}.mp4")
        shell("echo {wildcards.box_path}{video}.mp4 ../working_dir/videos/{videos}.mp4")
        shell("touch ../working_dir/videos/{video}.mp4")

rule crop_video:
    output: temporary("../working_dir/crops/{video}.crop.mp4")
    input:  "../working_dir/videos/{video}.mp4" 
    threads: 4
    run:
        #shell("python crop_by_dict.py -i {input}")
        shell("echo python crop_by_dict.py -i {input}")
        shell("touch ../working_dir/crops/{video}.crop.mp4")

rule upload_crop:
    input:  "../working_dir/crops/{video}.crop.mp4"
    threads: 1
    run:
        #shell("rclone copy {input} {remote}.crop.mp4")
        shell("echo rclone copy {input} {remote}.crop.mp4")

rule spot_video:
    output: temporary("../working_dir/spots/{video}.spot.mp4")
    threads: 4
    input:  "../working_dir/crops/{video}.crop.mp4"
    run:
        shell(". $HOME/.bashrc")
        shell("conda activate tracking")
        #shell("python spotlight.py {input}")
        shell("echo python spotlight.py {input}")
        shell("touch ../working_dir/spots/{video}.spot.mp4")

rule upload_spot:
    input:  "../working_dir/spots/{video}.spot.mp4"
    threads: 1
    run:
        #shell("rclone copy {input} {remote}.spot.mp4")        
        shell("echo rclone copy {input} {remote}.spot.mp4")        

rule inference:
    output: temporary("../working_dir/sleap/{video}.slp")
    input:  "../working_dir/spots/{video}.spot.mp4"
    threads: 1
    run:
        shell(". $HOME/.bashrc")
        shell("conda activate sleap")
        #shell("sleap-track -i {input} ....")
        shell("echo sleap-track -i {input} ....")
        shell("touch ../working_dir/sleap/{video}.slp")

rule convert_h5:
    output: temporary("../working_dir/h5/{video}.h5")
    input:  "../working_dir/sleap/{video}.slp"

    run:
        shell(". $HOME/.bashrc")
        shell("conda activate sleap")
        #shell("sleap-convert -i {input.slp} .... ")
        shell("echo sleap-convert -i {input.slp} .... ")
        shell("touch ../working_dir/h5/{video}.h5")

rule upload_h5:
    input:  "../working_dir/h5/{video}.h5"
    threads: 1
    run:
        #shell("rclone copy {input} {remote}:{path}{video}.h5")
        shell("echo rclone copy {input} {remote}:{path}{video}.h5")

rule process_h5:
    output: 
        "../results/csv/{video}.csv",
        "../results/txt/{video}.txt",
    input:  "../working_dir/h5/{video}.h5"
    run:
        #shell("python process_h5.py -i {input.h5}")
        shell("echo python process_h5.py -i {input.h5}")
        shell("touch ../results/csv/{video}.csv")
        shell("touch ../results/txt/{video}.txt")
