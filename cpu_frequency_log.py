import json
import os
from pathlib import Path
import argparse
import xlrd
from copy import deepcopy
from xlutils.copy import copy
import numpy as np
import pandas as pd
from pandas import Series, DataFrame   
import time

from Cmd import Q_Cmd, Q_Cmd_Ext
from utils import load_csv, save_array_2_xls

from Record import C_Record

cpu_frequency_Running = {
               "cmd_ws": os.path.abspath(os.path.dirname(__file__)), 
               "cores": "", 
               "cores_list": "", 
               "core_num":0,
               "core_num_max":1000,
               "smooth":True,
               "pre_freq":0,
}



def get_log_files():
    ws = cpu_frequency_Running["cmd_ws"] + "/_result/"
    log_files_cmd = "ls  " + ws + "*_cpus_frequency_log.txt"
    lf = Q_Cmd(log_files_cmd)
    
    return lf.split("\n")
def get_core_num(log_f):
    extra_log_files_cmd = 'cat  ' + log_f + ' | grep  processor | cut -d ":" -f2 '
    lf = Q_Cmd_Ext(extra_log_files_cmd)
    max_=0
    xx = cpu_frequency_Running["core_num_max"] if cpu_frequency_Running["core_num_max"] < len(lf) else len(lf)
    print(xx, cpu_frequency_Running["core_num_max"], len(lf))
    for i in range(0, xx):
        try:
            v = int(lf[i]) 
            if v > max_:
                max_ = v
        except:
            continue
    return max_ 
def get_next_process(lines, i_):
    found = False
    while not found:
        if i_ >= len(lines) or  "processor" in lines[i_] :
            found = True
        else:
            i_= i_ + 1
    if i_ < len(lines):
        try:
            cs = lines[i_].split(":")[1]
            c = int(cs)
            return  c , i_  
        except:
            return -1, i_    
    return -1, i_    
def get_frequency(lines, i_):
    nl = lines[i_]
    if  nl is not None and  "cpu MHz" in nl:
        try:
            fs = nl.split(":")[1]
            f = float(fs)
            return f, i_
        except:
            return 0, i_
    else:
        return 0, i_
def get_a_record(lines, i):
    core, i = get_next_process(lines, i)
    if core == -1:
        return -1, 0, i
    frequency, i = get_frequency(lines, i + 1)
    return core, frequency, i
    #print(core, frequency)
    
def get_core_frequency_list(log_f):
    f = C_Record(record_file_name=log_f, mode="r")
    lines = f.read_whole_record()
    i = 0
    core = 0
    f_l = []
    while core != -1 :
        core, frequency, ni = get_a_record(lines, i)
        i = ni + 1
        f_i = [core, frequency]
        f_l.append(f_i)
        #print(core, frequency)
    return f_l
def find_page_start(fl, ind):
    for i in range(ind, len(fl)):
        #print("find_page_start", i, fl[i])
        if fl[i][0] == 1:
            return i
        if fl[i][0] == -1:
            return -1
    return -1
    
def Core_frequency_list_to_array(fl):
    
    start_i = 0
    ended = False

    fal = []
    while not ended:
        si = find_page_start(fl, start_i)
        ei = find_page_start(fl, start_i + 2) 
        if si == -1 or ei == -1  :
            ended = True
        else:
            a =  np.zeros((cpu_frequency_Running['core_num'] + 1), dtype=np.float32)
            for i in range(si, ei):
                a[fl[i][0]] = fl[i][1]
            fal.append(a)
        start_i = ei
    return fal
        

def main():
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--cores', type=str,help='cores interested', default=cpu_frequency_Running["cores"])


    args = parser.parse_args()
    print(args)
    
    cpu_frequency_Running["cores"] = args.cores

    lfs = get_log_files()
    cpu_frequency_Running["core_num"] = get_core_num(lfs[0])
    head = ["c_"+ str(c) for c in range(cpu_frequency_Running["core_num"]+1)]
    for f in lfs:
        if f is not "":
            #extra_f = extract_device_infor(f, iostat_Running["devices"])
            #log = load_csv(extra_f, '  \s+')
            #print(log)
            #print(log[0][0])
            #save_csv_2_xls(extra_f + ".xls", "x", log)
            #print(log)
            fl = get_core_frequency_list(f)
            fal = Core_frequency_list_to_array(fl) 
            nf = f + ".xls"
            s = "c_frequency"
            save_array_2_xls(nf, s, fal,head)
            
            print(f, cpu_frequency_Running["cores"],  " ==> ", nf, s)
            
    exit(0)
    
if __name__ == '__main__':
    main()
        

    

