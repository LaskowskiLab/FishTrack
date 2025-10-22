### MobileSrc code for running raspberry pi Cameras
Written for the Laskowski Lab
For questions contact Ammon Perkes (perkes.ammon@gmail.com) 

## Installation
First, it's important to note that this code is written first and foremost for our lab. If you're applying this, you will need to make some changes before you just plug and play, especially anywhere that rclone is called.

# Setting up a pi
This assumes you have already configured your rclone token.

Make a folder called recording in the home directory, and copy the repo into recording using box 
```
rclone copy AmazonBox:mobileSrc ~/recording/mobileSrc 
```

Note that if you download this code using github, it will not include the webhook required to send slack messages (send_mail.sh)

on the pi, go to the mobileSrc repo (cd recording/mobileSrc)

run setup: 
```
bash setup.sh
```

Now you're ready to run the camera and/or schedule recordings

### Scheduling and recoridng video
This code was written with the idea that no one other than me should need to know how to program. As such, it's based around config files. The one we use most is called default.config, this records 1 fps, for 12 hours, starting at 6am. These files basicaly handle all the arguments that are going to be red into the rpicam-vid command. I also set up a bunch of aliases so that you can run the commands from any directory.

If you want to record a video right now with the default config, you can run 
```
start_recording
```

this will run the watch_mobile.sh script, which turns on the camera and checks every minute to make sure the file is still growing. If something fails, it will slack you and reset the pi. 

More often, we need to schedule recordings. The schedule is contained within the config file (for example, for default, the line "schedule=600" and "hours=12" sets the schedule). You can have multiple scheduled blocks, separated by spaces (e.g., schedule=600 800 1400). If these overlap, it will generally stop the previous video before starting the new one, but I don't recommend it.

if you want to schedule a recording manually, you can run 
```
schedule_config ~/recordings/mobileSrc/configs/your.config.file
```

You also will want to include a suffix, either within your config (as project_suffix=yourName.project) or by running 
```
set_suffix youName.project
```

### Automatic scheduling
Because we have multiple pi's and varying comfort with the command line, the pi's can schedule themselves automatically based on a file stored on box. You can find the file here: https://ucdavis.app.box.com/file/1740466105936 (you will need access)

In order to set the pi up for updating based off the online file, run 
```
reset_sync
```
This will set the crontab to base_cron.txt (found in the crontabs folder) while includes a daily call for sync_Schedule.sh. Now you can go to the box file I linked above and set the suffix and config for your video. The config should either be "on", "off" or the name of a specific config file in the configs folder

If you want to stop the pi from syncing its schedule with box, run 
```
reset_static
```

That's all you should need to know to set up and run a pi. There are more detailed explanations of configuring the pi's, interacting with videos, debugging, etc, which you can find in the MasterPiGuide on Box.

Happy tracking!
