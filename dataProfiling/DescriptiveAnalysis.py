from datetime import timedelta
import datetime
import re
import seaborn as sns
from statistics import mean,stdev
import numpy as np
from collections import deque 
import pandas as pd
import plotly
import plotly.graph_objs as go
import plotly.express as px

def get_datetime(newVal):
    stuff = re.split('\s+', newVal)
    date = re.split('-', stuff[0])
    time = re.split(':', stuff[1])
    sec = []
    if re.search('\.', time[2]) == None:
        sec.append(time[2])
        sec.append("0")
    else:
        sec = re.split('\.', time[2])
        dt = datetime.datetime(int(date[0]),
                          int(date[1]),
                          int(date[2]),
                          int(time[0]),
                          int(time[1]),
                          int(sec[0]),
                          int(sec[1]))
    return dt

def read_uploaded_data(inp):
    filtered = []
    for line in inp:
        x = str(str(line).strip()).split()
        if len(x) > 5:
            filtered.append(x)
    inp.close()
    return pd.DataFrame(filtered,columns=["Date","Time","Sensor","Status","Activity","Begin_or_End"])


def data_preprocessing(df):
    df['Activity']=df['Activity'].str.lower()
    df.loc[df.Activity=='clean', 'Activity'] = 'cleaning'
    for i in range(df.shape[0]):
        if len(df.iloc[i,2])==3:
            df.iloc[i,2]=df.iloc[i,2][0:1]+'0'+df.iloc[i,2][1:]
    df["Date_Time"] = df["Date"]+' '+df["Time"]
    df["Date_Time"]=df["Date_Time"].apply(lambda x:get_datetime(x))
    df['Date']=pd.to_datetime(df['Date'])
    df.sort_values(by=['Date_Time'], inplace=True, ascending=True,ignore_index=True)
    df.drop(df[df['Activity']=='r1_housekeeping'].index, inplace = True) 
    df.drop(df[df['Activity']=='wash_bathtub'].index, inplace = True) 
    return df

def non_zero(row, columns):
    return list(columns[~(row == 0)])

def check_validity(df):
    activities = list(df["Activity"].unique())
    unequal = 0
    for i in activities:    
        a = len(df[df['Activity']==i])
        df_i=df[df['Activity']==i]
        b_c = len(df_i[df_i['Begin_or_End']=='begin'])
        e_c = len(df_i[df_i['Begin_or_End']=='end'])
        if b_c != e_c:
            unequal+=1
    return unequal==0

def activity_to_sensor_fc(df):
    activity_to_sensor = pd.crosstab(df['Activity'],df['Sensor'])
    # activity_to_sensor['List_of_Sensors'] = activity_to_sensor.apply(lambda x: non_zero(x, activity_to_sensor.columns), axis=1)
    return activity_to_sensor


def activity_to_sensor_viz(d):
    act_list= []
    for col in d.columns:
        for ind in d.index:
            if ind=='r1_bed_to_toilet':
                act_list.append([col ,ind,(d[col][ind]+d[col]["r2_bed_to_toilet"])])
                continue
            elif ind=="r1_breakfast":
                act_list.append([col ,ind,(d[col][ind]+d[col]["r2_breakfast"])])
                continue
            elif ind=="r1_groom":
                act_list.append([col ,ind,(d[col][ind]+d[col]["r2_groom"])])
                continue
            elif ind=="r1_sleep":
                act_list.append([col ,ind,(d[col][ind]+d[col]["r2_sleep"])])
                continue
            elif ind=="r1_work_at_computer":
                act_list.append([col ,ind, (d[col][ind]+d[col]["r2_work_at_computer"])])
                continue
            elif ind!="r2_work_at_computer" and ind!="r2_sleep" and ind!="r2_groom" and ind!="r2_breakfast" and ind!="r2_bed_to_toilet":
                act_list.append([col ,ind,  d[col][ind]])

    return pd.DataFrame(act_list,columns=['sensor','activity','frequency'])

    


def con_acts(df,resident_no):
    # print(df.head())
    df = df[df['Activity'].str.startswith('r'+str(resident_no))]
    response = ''
    conc_actvts=[]
    stack_list = []
    stack = deque()
    for i in range(len(df)-1):
        if len(stack)==0 and df.iloc[i,4]==df.iloc[i+1,4] and df.iloc[i,5]=='begin' and df.iloc[i+1,5]=='end':
            i+=1
            continue
        else:
            if df.iloc[i,5]=='begin':
                stack.append(df.iloc[i,4])
                stack_list.append(df.iloc[i,4][3:]+' '+df.iloc[i,5]+' '+str(df.iloc[i,6])+' '+df.iloc[i,4][:2])
            else:
                if len(stack):
                    stack.pop()
                    stack_list.append(df.iloc[i,4][3:]+' '+df.iloc[i,5]+' '+str(df.iloc[i,6])+' '+df.iloc[i,4][:2])
                if len(stack)==0:
                    if len(stack_list):
                        response = response+'\n'+str(stack_list)[0:]
                        conc_actvts.append(list(stack_list))
                        stack_list=[]
    return conc_actvts


def con_acts_rule_mining(df,resident_no):
    df = df[df['Activity'].str.startswith('r'+str(resident_no))]
    conc_actvts=[]
    stack_list = []
    stack = deque()
    for i in range(len(df)-1):
        if len(stack)==0 and df.iloc[i,4]==df.iloc[i+1,4] and df.iloc[i,5]=='begin' and df.iloc[i+1,5]=='end':
            i+=1
            continue
        else:
            if df.iloc[i,5]=='begin':
                stack.append(df.iloc[i,4])
                stack_list.append(df.iloc[i,4][3:])
            else:
                if len(stack):
                    stack.pop()
                if len(stack)==0:
                    if len(stack_list):
                        conc_actvts.append(list(stack_list))
                        stack_list=[]
    return conc_actvts


def cal_time(date1,date2):
  datetimeFormat = '%Y-%m-%d %H:%M:%S.%f'
  diff = datetime.datetime.strptime(date1, datetimeFormat)\
    - datetime.datetime.strptime(date2, datetimeFormat)
  return diff.seconds

def concurrent_res(data):
    data = data.fillna("")
    row_num,column_num=data.shape

    acts=[]
    for i in range(0,row_num):
        r=data.iloc[i]
        li=r.tolist()
        a=[]
        for x in li:
            temp=x.split(" ")
            if (temp[0] not in a):
                a.append(temp[0])
        if(a[-1]==''):
            a.pop(-1)
        acts.append(a)

    total_act=[]
    for i in range(0,row_num):
        temp_row=acts[i]
        total_act.append(len(temp_row))

    activity_time=[]
    activity_test=[]
    dict2={}
    for i in range(0,row_num):
        row=data.iloc[i]
        r=row.tolist()
        rows=[]
        for x in r:
            temp=x.split(" ")
            if(len(temp)>1):
                rows.append(temp)
        # print(rows)
        #sets=[]
        #sets.append(i+1)
        for x in acts[i]:
            act=x
            sets=[]
            sets.append(x)
            for k in rows:
                if(k[0]==x and k[1]=='begin'):
                    btime=k[2]+' '+k[3]
                elif(k[0]==x and k[1]=='end'):
                    etime=k[2]+' '+k[3]
            total_time=cal_time(etime,btime)
            #sets.append(x)
            sets.append(k[2])
            activity_time.append(total_time)
            sets.append(total_time)
            activity_test.append(sets)
        dict2[i+1]=total_time

    activity_sets=activity_test
    k=0
    for i in range(0,len(total_act)):
        number_per_row=total_act[i]
        for m in range(0,number_per_row):
            activity_sets[k].append("s"+str(i+1))
            k=k+1 

    return pd.DataFrame(activity_sets,columns=['activity','date','time','parent'])

def only_act_names(df):
    acts = []
    activities = list(df["Activity"].unique())
    for i in activities:
        if i[2]=='_':
            acts.append(i[3:])
        else:
            acts.append(i)
    acts=list(np.unique(acts))
    return acts


def get_frgrnd_act_def():
    foreground_only_acts=['bathing',
 'bed_to_toilet',
 'bed_toilet_transition',
 'breakfast',
 'cleaning',
 'eating',
 'enter_home',
 'groom',
 'grooming',
 'leave_home',
 'shower',
 'sleep',
 'sleeping_not_in_bed',
 'wakeup',
 'wandering_in_room']
    return foreground_only_acts


def foreground_background_acts(df,resident_no):
    df = df[df['Activity'].str.startswith('r'+str(resident_no))]
    foreground_only_acts = get_frgrnd_act_def()
    foreground_acts = []
    background_acts = []
    stack_list = []
    stack = deque()
    for i in range(len(df)-1):
        if len(stack)==0 and df.iloc[i,4]==df.iloc[i+1,4] and df.iloc[i,5]=='begin' and df.iloc[i+1,5]=='end':
            i+=1
            continue
        else:
            if df.iloc[i,5]=='begin':
                stack.append(df.iloc[i,4])
                stack_list.append([df.iloc[i,4][3:],df.iloc[i,5],str(df.iloc[i,6])])
            else:
                if len(stack):
                    stack.pop()
                    stack_list.append([df.iloc[i,4][3:],df.iloc[i,5],str(df.iloc[i,6])])
                if len(stack)==0:
                    if len(stack_list):
                        foreground_acts.append(list(x for x in stack_list if x[0] in foreground_only_acts))
                        background_acts.append(list(x for x in stack_list if x[0] not in foreground_only_acts))
                        stack_list=[]
    return pd.DataFrame(foreground_acts),pd.DataFrame(background_acts)


def foreground_background_acts_mining(df,resident_no):
    df = df[df['Activity'].str.startswith('r'+str(resident_no))]
    foreground_only_acts = get_frgrnd_act_def()
    foreground_acts = []
    stack_list = []
    stack = deque()
    for i in range(len(df)-1):
        if len(stack)==0 and df.iloc[i,4]==df.iloc[i+1,4] and df.iloc[i,5]=='begin' and df.iloc[i+1,5]=='end':
            i+=1
            continue
        else:
            if df.iloc[i,5]=='begin':
                stack.append(df.iloc[i,4])
                stack_list.append(df.iloc[i,4][3:])
            else:
                if len(stack):
                    stack.pop()
                if len(stack)==0:
                    if len(stack_list):
                        tmp = list(x for x in stack_list if x in foreground_only_acts)
                        if len(tmp)>1:
                            foreground_acts.append(list(np.unique(tmp)))
                        stack_list=[]
    return foreground_acts


def sensor_to_time(df):
    df['Hour']=df['Time'].apply(lambda x: x[0:2])
    df['Hour']=df['Hour'].astype('int')
    sensor_time = pd.crosstab(df['Sensor'],df['Hour'])
    return sensor_time

def getConcurrentViz():
    inp = open("./upload/dataset") #TODO Check if this is being accessed correctly
    df = read_uploaded_data(inp)
    df = data_preprocessing(df)
    if (check_validity(df)==False):
        return None
    df = con_acts(df,1) #change this value depending on which resident's conc viz u wanna show
    df = pd.DataFrame(df)
    df = concurrent_res(df)
    return df

def getSensorFreqViz():
    inp = open("./upload/dataset") #TODO Check if this is being accessed correctly
    df = read_uploaded_data(inp)
    df = data_preprocessing(df)
    if (check_validity(df)==False):
        return None
    df = activity_to_sensor_fc(df)
    df = activity_to_sensor_viz(df)
    return df

