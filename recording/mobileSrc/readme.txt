Welcome to the pi! 

You can read the full documentation online, but here are some helpful shortcuts:

To start recording right now: 
  start_recording

for custom parameters, include a config file, e.g., 
  start_recording ~/recording/mobileSrc/configs/default.config

to update source code (including configs) from box:
  sync_code

to upload videos to Box:
  upload_vids

To schedule recordings using config, use:
  schedule_config ~/recording/mobileSrc/configs/multi.config
To schedule a tracking system pi to start recording (starting tomorrow):
  schedule_ON your.suffix

To clear all future cron scheduled recordings
  reset_schedule : clears cron schedule (crontab-recording.txt) but does not change the suffix
  schedule_OFF   : resets the crontab (crontab-pause.txt) and changes suffix to PAUSE

To check if the camera is currently doing something
  pgrep rpicam

To stop the camera (assuming it's not zombified) 
  pkill rpicam

To restart pi
  sudo reboot
 

