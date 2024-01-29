

import sys
import pandas as pd
from datetime import datetime, timedelta
import subprocess

#_,piID,start_date,end_date,current_str,target_str = sys.argv

infile = sys.argv[1]
file_df = pd.read_csv(infile)

## I had ChatGPT try this, it did ok,still had to add some stuff
def get_date_range(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, '%Y.%m.%d')
    end_date = datetime.strptime(end_date_str, '%Y.%m.%d')

    current_date = start_date
    date_list = []
    while current_date <= end_date:
        date_list.append(current_date.strftime('%Y.%m.%d'))
        current_date += timedelta(days=1)
    return date_list 

def make_files(pi,date_range,suffix):
    files = []
    for d in date_range:
        files.append(pi + '/' + d + '.' + suffix)
    return files

def rename_files(files,current_str,target_str):
    for f in files:
        print(f)
        new_file = f.replace(current_str,target_str)
        #print('rclone move aperkes:pivideos/' + f,'aperkes:pivideos/' + new_file,'--dry-run')
        print(f,new_file)
        command = 'rclone move aperkes:/pivideos/' + f + ' aperkes:/pivideos/' + new_file #+ ' --dry-run'
        subprocess.call(command,shell=True)

for index,row in file_df.iterrows():
    if row.EndDate == 'NOT DONE RECORDING':
        continue
    date_range = get_date_range(row.StartDate,row.EndDate)
    piID = row.Pi
    current_str = row.CurrentSuffix
    target_str = row.DesiredSuffix
    files = make_files(piID,date_range,current_str)
    rename_files(files,current_str,target_str)

