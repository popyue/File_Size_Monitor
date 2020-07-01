'''
Author : Leo Wu 
Compny: III-CSTI
Create TIME: 2020-04 
Test time range : 2020-04 ~ 2020-12
Using for read filesize and record it 
The scenario, for example, 
when you want to check some program which will recording is running normally,
try to read its filesize and analysis the change everyhour.

now this script is using on monitor fiewall collector, 
make sure the syslog collect is running normally.
'''
# Library Import
import time
from datetime import timedelta 
import datetime as dt
import csv
import os 
import matplotlib
import matplotlib.pyplot as plt # import matplotlib related lib
matplotlib.use('Agg')
import pandas as pd
import re
import glob

'''
# Initialize
'''
global logsize, timev, logname, logpath, csvname, PicName
'''
## Time Stamp 
'''
timev= time.strftime("%Y-%m-%d", time.localtime())
#timeformat2= time.strftime("%Y%m%d", time.localtime())
first_date = dt.date.today()
xticklist=[]
'''
Host declare (Dangerous)
(change the host declare method )

'''
host=[]

# Set Storage Path
StoragePath= ['/log/firewall_log', '/opt/ctrl/monitor_firewall/csv', '/var/log/suricata', '/opt/ctrl/monitor_firewall/csv/pic_month']

# csv file which date is last month
#csv_lastmonth = []

# Set File Name
flowname= 'flow.json'
logname= '{}-{}.log'.format(timev,host[0])
csvname= '{}-firewall.csv'.format(timev)
picname= 'Monitor-{}.png'.format(timev)
monthpicname= 'Monitor-{}.png'.format((first_date.month)-1)

# Set Full Path
files= [logname,csvname,picname,flowname, monthpicname]
csvpath= '{}/{}'.format(StoragePath[1],files[1])
log= '{}/{}'.format(StoragePath[0],files[0])
picpath='{}/{}'.format(StoragePath[1], files[2])
flow= '{}/{}'.format(StoragePath[2],files[3])
monthpicpath= '{}/{}'.format(StoragePath[3], files[4])
fullname= [log, csvpath, picpath, flow, monthpicpath]

def checkfile(filename):
    try:
        if os.path.exists(filename):
            return True
        else:
            return False
    except Exception as err:
        print("An exception happened1:" + str(err))


def getlogsize(filepath, filename):
    check = checkfile(filepath) # Check file exists in the filepath
    try:
        # Check File exist or not
        if check:
            print("{} exits".format(filename))
            logsize = os.path.getsize('{}'.format(filepath))
            return logsize
        else:
            print("{} not exist".format(filename))
            return False 
    except Exception as err:
        print("An exception happend2: " + str(err))


def create_csv(filename):
    print("Create CSV File: {}".format(filename))
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ID','FileName','CurrentSize'])
        writer.writerow(['0',logname,0])
        csvfile.close()


def append_csv(filename,record_id,logname,currentsize):
    csv_content=[record_id,logname,currentsize]
    with open(filename, 'a') as csvfile:
        newdata = csv.writer(csvfile)
        newdata.writerow(csv_content)
        csvfile.close()


def size_format(sizes):
    power = 2**10  #2 **10 = 1024
    n=0
    # power_labels = {0:'', 1: 'kilo', 2: 'mega',3: 'giga', 4: 'tera' }
    try:
    	while n < 2:
            sizes /= power
            n += 1
            print('n and size: {} and {}'.format(n,sizes))
            if n>2 and sizes>1024:
                return sizes
            else:
                return sizes
    except Exception as err:
        print("An exception happen under size format:"+ str(err))
	     

def Draw(filename):
    data=pd.read_csv(filename)
    # DataIndex is the x_ticks value
    # DataSize is the y_ticks value
    DataIndex=data["ID"]
    DataSize=data["CurrentSize"]
    plt.style.use("ggplot")
    plt.plot(DataIndex,DataSize,c ="r")
    plt.xlabel("Hours",fontweight = "bold")
    plt.ylabel("DataSize",fontweight = "bold")
    plt.title("FIREWALL MONITOR",fontsize = 18, fontweight = "bold", x=1.0,y =1.2)
    plt.xlim(0,24)
    plt.xticks(range(0,25,1))
    plt.yticks(range(0,10000,500))
    for Index,Size in zip(DataIndex, DataSize):
        plt.text(Index,Size,Size, ha='center', va='bottom', fontsize=10)
    plt.savefig(fullname[2], bbox_inches = 'tight', pad_inches=0.0)
    plt.close()
    

def Draw_Month(filelist):
    # This month function is different than Draw()
    # In Draw_Month(), we combine all log size in 30/31 csv file in one figure 
    # So X_tick can't use hour, we need to use day+hour as our x_tick

    frame = pd.DataFrame()
    for filenames in filelist:
        completefiles = StoragePath[1]+'/'+filenames
        data= pd.read_csv(completefiles, index_col=None, header=0)
        filedate='-'.join(filenames.split('/')[-1].split('-')[:3])
        t = time.mktime(dt.datetime.strptime(filedate, "%Y-%m-%d").timetuple())
        xticklist=[t + int(hour)*60*60 for hour in data["ID"]]
        data['x_value']= xticklist
        frame = frame.append(data)

    # X_DATA is the ID in csv file (ID is the hour of a day)
    # Y_DATA is the size of logfile 
    X_DATA=frame["x_value"]
    Y_DATA=frame["CurrentSize"]
    plt.style.use("ggplot")
    plt.figure(figsize=(100,40))
    plt.plot(X_DATA,Y_DATA, c="r")
    plt.xlabel("DateTime", fontweight = "bold")
    plt.ylabel("DataSize", fontweight = "bold")
    plt.title("FIREWALL MONITOR MONTH REPORT", fontsize = 12, fontweight ="bold", x=1.0, y=1.2)
    plt.xticks(xticklist)
    plt.yticks(range(0,10000,500))
    for Index,Size in zip(X_DATA, Y_DATA):
        plt.text(Index,Size,Size, ha='center', va='bottom', fontsize=10)
    plt.savefig(fullname[4], bbox_inches = 'tight', pad_inches=0.0)
    plt.close()

# 判斷是否為每月第一天
def firstDayOfMonth(date):
    now_day = (date+dt.timedelta(days=-date.day + 1)).day
    # input date is : datetime.date.today()
    return now_day == date.day

def main():
    '''
    index use hour 
    00:00 is first on 
    00:59 is second 
    and so on 
    so there will be 25 item in csv file 
    '''
    index = (dt.datetime.today().hour)+1 # Use hour add 1 for index

    # Chceck CSV exist
    check_csv = checkfile(fullname[1])  
    
    # Check Log file exist
    logsize = getlogsize(fullname[0],files[0])
    
    #Convert Size to MB
    formatsize = round(size_format(logsize),2)

    if check_csv:
        if logsize:
            append_csv(fullname[1],index,files[3],formatsize)
            Draw(fullname[1])
        else:
            return 'Log Disappear'
    else:
        create_csv(fullname[1])
    # The following if else condition will check the date is the first day of a month or not 
    # If yes, it will draw monthly pic
    if firstDayOfMonth(first_date):
        this_month = first_date.month
        last_month = (first_date.replace(month=first_date.month-1)).strftime("%m")
        year = first_date.year
        if this_month == 1:
            year = year-1
            # csv_name format is : Year-Month-Date-firewall.csv
            csv_lastmonth=[f.split('/')[-1] for f in glob.glob("csv/*.csv") if "{}-{}".format(year,last_month) in f ]    
            csv_lastmonth= sorted(csv_lastmonth)
            Draw_Month(csv_lastmonth)
        else:
            # csv_name format is : Year-Month-Date-firewall.csv
            csv_lastmonth=[f.split('/')[-1] for f in glob.glob("csv/*.csv") if "{}-{}".format(year,last_month) in f ]    
            csv_lastmonth= sorted(csv_lastmonth)
            Draw_Month(csv_lastmonth)
    else:
        return 'Today is : {}, not the first day of month'.format(dt.date.today().strftime("%Y-%m-%d"))
        



if __name__ == '__main__':
    main()





