

## Use run_vid to parse line

## add this last line
line="* * * * * /path/to/command"
(crontab -u $(whoami) -l; echo "$line" ) | crontab -u $(whoami) -
