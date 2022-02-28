#!/bin/bash

## Very simple script to run a message (defined by quotes, e.g. bash ./send_mail.sh 'this is a test'
## The URL there had to be configured via the app, talk to Ammon for questions if it's not working

message='{"text":"'$1'"}'
curl -X POST -H 'Content-type: application/json' --data "$message" <<YOUR WEBHOOK HERE>>
