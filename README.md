# FishTrack

Lots of code to handle the acquisition and processing of fish videos for the Laskowski Lab. 

Code is under active development. Check with Ammon for questions. In general, if there is conflict, trust the Box protocol.

## For recording: 
Recording on the pis is scheduled by a cron job and run in a bash script. Both the script and the template for the crontab can be found in the recording directory. 

This now uses raspivid, which seems to be more stable. 
The crontab-pi.txt has everything you need to make it work. Just type crontab ~/recording/src/crontab-pi.txt and it will activate it. 
This will capture video and then upload it to the box each evening. 

## For processing
Video is downloaded from the box, converted to mp4, and processed using sleap (along with some helper scripts in python). See relevent installation and use instructions on Box. 
