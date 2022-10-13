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

from utils import load_sheet_from_xls,df_2_csv, get_files_from_folder
from Cmd import Q_Cmd

with_log = True
with_log = False
xls_2_csv_Running = {
               "cmd_ws": os.path.abspath(os.path.dirname(__file__)), 
               "work_folder": os.path.abspath(os.path.dirname(__file__)), 
               "input_folder":   "",
               "input_xls":   "SPR_storage.xlsx",
               "sheet_name":   "Fio_FullKPI_Single",
               "output_csv":  "",
               "split_string":  ",",
}

kpi_extract = {
    "interesting": {
       "read": ["read_bw(MiB/s)","read_iops"] ,
       "write": ["write_bw(MiB/s)","write_iops"] ,
       "randwrite": ["write"] ,
       "randread": ["read"] ,
       "randrw": ["read","write"] ,
    },
     "interesting_running": {
    },
     "interesting_running_index": {
    },
    "colums":"",   
    "title_added":"FIO",
    "titles": ["blocksize", "read_write", "device_name"],
    "titles_renaming":{"rename_titles":["read_write"],
                            "rename_titles_index":[],
                            "read":"seqread",
                            "write":"seqwrite",
                            "randrw":"70read30write",
                            },
    "titles_index": [],
    "case_type_idx":9,
    "item_blacklist":{
        "blocksize": ["512"],
        #"blocksize": ["256k"],
    },
    }

def generate_interesting_items(colums= None):
    if type(colums)==  type(None):
        colums = kpi_extract["colums"]
    for item in kpi_extract["interesting"].keys():
        kpi_extract["interesting_running"][item] = []
        kpi_extract["interesting_running_index"][item] = []
        for interesting_colum in kpi_extract["interesting"][item]:
            if interesting_colum in colums:
                kpi_extract["interesting_running"][item].append(interesting_colum)
                kpi_extract["interesting_running_index"][item].append(colums.index(interesting_colum))
                
            else:
                if interesting_colum in kpi_extract["interesting_running"].keys():
                    kpi_extract["interesting_running"][item] += kpi_extract["interesting_running"][interesting_colum]
                    kpi_extract["interesting_running_index"][item] += kpi_extract["interesting_running_index"][interesting_colum]
                    
    for t in kpi_extract["titles"]:
        kpi_extract["titles_index"].append(colums.index(t))  
        if t in kpi_extract["titles_renaming"]["rename_titles"]:
            kpi_extract["titles_renaming"]["rename_titles_index"].append(colums.index(t))
    #print(kpi_extract)

def extract_case_kpi(idx, row):
    def is_in_black_list():
        for key in kpi_extract["item_blacklist"].keys():
            x = kpi_extract["titles"].index(key)
            xx = kpi_extract["titles_index"][x]
            if row[xx] in kpi_extract["item_blacklist"][key]:
                return 1
        return 0
    def get_title(row, v_c):
        ts = [kpi_extract["title_added"]]
        for i in kpi_extract["titles_index"]:
            renamed_title=row[i]
            if i in kpi_extract["titles_renaming"]["rename_titles_index"]:
                if renamed_title in kpi_extract["titles_renaming"].keys():
                    renamed_title=kpi_extract["titles_renaming"][renamed_title]
            ts.append(renamed_title)
        ts.append(v_c)
        return " ".join(ts)
    case_type_idx = kpi_extract["case_type_idx"]
    if row[case_type_idx] in kpi_extract["interesting_running_index"].keys():
        v =[]
        for i in kpi_extract["interesting_running_index"][row[case_type_idx]]:
            if is_in_black_list() == 1:
                continue
            ts = get_title(row, kpi_extract["colums"][i])
            kpi_item = [ts, row[i]]
            v.append(kpi_item)
        return v
    return None
def extract_kpi_info(df):
    #print(df)
    colums = df.columns.tolist()
    kpi_extract["colums"] = colums
    generate_interesting_items()
    if len(kpi_extract["interesting_running_index"].keys()) == 0:
        return None
    kpi_l = []
    for indexs in df.index:
        #print(df.loc[indexs].values[0:-1])
        v = extract_case_kpi(indexs, df.loc[indexs].values[0:-1])
        kpi_l += v
    #for row, data in df.iteritems():
        #
    #print(kpi_l)
    kpi_df = pd.DataFrame(kpi_l)
    #print(kpi_df)
    return kpi_df
def xls2csv(xls_fn, sheet_name, csv_fn):
    df, _ = load_sheet_from_xls(xls_fn, sheet_name)
    if type(df) != type(None):
        df_2_csv(csv_fn, df,sep=xls_2_csv_Running["split_string"])
        if not xls_2_csv_Running["extract"]:
            print(xls_fn, sheet_name, " ==> ", csv_fn)
            return
        kpi_df = extract_kpi_info(df)
        kpi_csv_fn = ""
        if type(kpi_df) != type(None):
            kpi_csv_fn = csv_fn[:-4] + "_ext.csv"
            header=["Test Cases", "Values"]
            kpi_df.columns = header
            df_2_csv(kpi_csv_fn, kpi_df,sep=xls_2_csv_Running["split_string"])
        print(xls_fn, sheet_name, " ==> ", csv_fn, "  ", kpi_csv_fn)
    
def main():
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--input_folder', type=str,help='folder name of xls, default is empty. If not default, all xls file inside will  will be processed', default= xls_2_csv_Running["input_folder"])
    parser.add_argument('--input_xls', type=str,help='xls file to be processed. Valid only when the input_folder is empty. ', default=xls_2_csv_Running["input_xls"])
    parser.add_argument('--sheet_name', type=str,help="the sheet name of xls. if input as '', the xls file name without extention will be used", default=xls_2_csv_Running["sheet_name"])
    #parser.add_argument('--output_csv', type=str,help="output csv, default will be as same input xls file name.", default="")
    parser.add_argument('--split_string', type=str,help="split string of csv", default=xls_2_csv_Running["split_string"])
    parser.add_argument('--extract', type=str2bool,help="generate result in kpi formate", default='True')

    args = parser.parse_args()
    print(args)

    xls_2_csv_Running["input_folder"] = args.input_folder
    xls_2_csv_Running["input_xls"] = args.input_xls
    xls_2_csv_Running["sheet_name"] = args.sheet_name
    #xls_2_csv_Running["output_csv"] = args.output_csv
    xls_2_csv_Running["split_string"] = args.split_string
    xls_2_csv_Running["extract"] = args.extract

    def processing_xls(xls, sheet=""):
        fn = os.path.basename(xls)
        path = os.path.dirname(xls)
        file_name, file_extension = os.path.splitext(fn)
        csv_file_name = path + "/" + file_name + ".csv"
        if sheet == "":
            sheet = file_name
        
        xls2csv(xls, sheet, csv_file_name)
    if xls_2_csv_Running["input_folder"] == "":
        processing_xls(xls_2_csv_Running["input_xls"] , xls_2_csv_Running["sheet_name"].strip())
        return
    xls_files = get_files_from_folder(xls_2_csv_Running["input_folder"])
    for x in xls_files :
        processing_xls(x)
    exit()
    
if __name__ == '__main__':
    main()
        

    

