# FishTrack

Lots of code to handle the acquisition and processing of fish videos for the Laskowski Lab

Code is under active development. Check with Ammon for questions 

## For recording: 
Recording on the pis is scheduled by a cron job and run in a bash script. Both the script and the template for the crontab can be found in the recording directory. 
Be sure to change the crontab and run_cam.sh to reflect the correct pi name
This will capture images and upload it to the Box each day at 7pm

## For processing
Images are downloaded from the box, combined into videos, and processed using trex (along with some helper scripts in python). See relevent installation and use instructions on Box. 
