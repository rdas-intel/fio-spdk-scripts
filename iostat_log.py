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

from Cmd import Q_Cmd
from utils import load_csv, save_csv_2_xls


iostat_Running = {
               "cmd_ws": os.path.abspath(os.path.dirname(__file__)), 
               "devices": "nvme0n1", 
}



def get_log_files():
    ws = iostat_Running["cmd_ws"] + "/_result/"
    log_files_cmd = "ls  " + ws + "*iostat_log.txt"
    lf = Q_Cmd(log_files_cmd)
    
    return lf.split("\n")
def extract_device_infor(log_f, devices):
    extra_log_files_cmd = "iostat_extract.sh   " + log_f + " " + devices 
    print(extra_log_files_cmd)
    lf = Q_Cmd(extra_log_files_cmd)
    cvf_f = log_f + "_" + devices + ".csv"
    return cvf_f 

def main():
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--devices', type=str,help='setting worksheet in xls format: setting', default=iostat_Running["devices"])


    args = parser.parse_args()
    print(args)
    
    iostat_Running["devices"] = args.devices

    lfs = get_log_files()
    print(lfs)
    #exit()
    for f in lfs:
        if f is not "":
            print(f, iostat_Running["devices"])
            extra_f = extract_device_infor(f, iostat_Running["devices"])
            log = load_csv(extra_f, '  \s+')
            print(log)
            #print(log[0][0])
            #save_csv_2_xls(extra_f + ".xls", "x", log)
            save_csv_2_xls(extra_f + ".xls", iostat_Running["devices"], log)
            #print(log)
    exit(0)
    
if __name__ == '__main__':
    main()
        

    

