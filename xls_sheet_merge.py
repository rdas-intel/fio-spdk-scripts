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

from utils import Save_ndarray_cases,  Update_Result_2_Xls,Xls_Read_Worksheet, Xls_Read_Row, Xls_Set_Value_BkgColor, load_sheet_from_xls,save_csv_2_xls
from Cmd import Q_Cmd


with_log = True
with_log = False
xls_sheet_merging_Running = {
               "cmd_ws": os.path.abspath(os.path.dirname(__file__)), 
               "work_folder": os.path.abspath(os.path.dirname(__file__)), 
               "input_xls":   "SPR_storage.xlsx  xx.xls:Fio",
               "sheet_name":   "",
               "output_sheets":  {
                    "sheets":[],
                    "df":[]
               },
               "output_xls":  "output.xlsx",
               "inputs":{},
}


def get_filename(xls_fn):
    return xls_sheet_merging_Running["work_folder"] + "/" +xls_fn

def parsing_input_list():
    for inputs in  xls_sheet_merging_Running["input_xls"].split(" "):
        if len(inputs) and len(inputs.strip()) > 0:
            xls_sheets=inputs.split(":")
            xls_sheet_merging_Running["inputs"][xls_sheets[0]] = {}
            if len(xls_sheets) > 1:
                xls_sheet_merging_Running["inputs"][xls_sheets[0]]["sheets"] = xls_sheets[1].split(",")
            else:
                xls_sheet_merging_Running["inputs"][xls_sheets[0]]["sheets"] = []
                
    print(xls_sheet_merging_Running["inputs"])

def update_sheets_name(xls, sheets):
    return sheets
def get_output_sheets():
    x = xls_sheet_merging_Running
    for xls in x["inputs"].keys():
        s = x["inputs"][xls]["sheets"]
        #print(xls, s)
        s_ = update_sheets_name(xls, s)
        x["output_sheets"]["sheets"] = x["output_sheets"]["sheets"] + s_ #is None else x["output_sheets"]["sheets"].append(s)
        #print(x["output_sheets"]["sheets"])
        dfs = [x["inputs"][xls]["dfs"][df] for df in x["inputs"][xls]["dfs"].keys()]
        x["output_sheets"]["df"] =  x["output_sheets"]["df"] + dfs # is None else x["output_sheets"]["df"].append(dfs)
    #print(x["output_sheets"]["sheets"])
    #print(x["output_sheets"]["df"])
def merging_sheets():
    x = xls_sheet_merging_Running
    all_dfs = []
    for xls in x["inputs"].keys():
        sheets = None if x["inputs"][xls]["sheets"] == [] else x["inputs"][xls]["sheets"]
        xls_fn = get_filename(xls)
        x["inputs"][xls]["dfs"], sheet_names = load_sheet_from_xls(xls_fn, sheets)
        x["inputs"][xls]["sheets"] = sheet_names
    get_output_sheets()
    writer = None
    out_f = get_filename(x["output_xls"])
    if len(x["output_sheets"]["sheets"]) == 1:
        x["output_sheets"]["sheets"][0] = x["sheet_name"] if x["sheet_name"] !="" else x["output_sheets"]["sheets"][0] 
    for i in range(len(x["output_sheets"]["sheets"])):
        #print(i, x["output_sheets"]["sheets"][i])
        #print(i, x["output_sheets"]["df"][i])
        writer = save_csv_2_xls(out_f, x["output_sheets"]["sheets"][i],x["output_sheets"]["df"][i],writer=writer, final=False)
    writer.save() 

    print("generated:", out_f, x["output_sheets"]["sheets"])
    out_xls_ls = "ls -lh " + out_f
    r_s = Q_Cmd(out_xls_ls)
    print(r_s)  
def main():
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--input_xls', type=str,help='input xls/xlsx and sheets, seperated by " " for xls/xlsx files and "," for sheet name.  Example: "SPR_storage.xls  xx.xls:Fio,xx,ww"', default=xls_sheet_merging_Running["input_xls"])
    parser.add_argument('--output_xls', type=str,help="output xls", default=xls_sheet_merging_Running["output_xls"])
    parser.add_argument('--sheet_name', type=str,help="new sheet name if there is only one sheet", default=xls_sheet_merging_Running["sheet_name"])

    args = parser.parse_args()
    print(args)

    xls_sheet_merging_Running["input_xls"] = args.input_xls
    xls_sheet_merging_Running["output_xls"] = args.output_xls
    xls_sheet_merging_Running["sheet_name"] = args.sheet_name

    parsing_input_list()
    merging_sheets()
    exit()
    
if __name__ == '__main__':
    main()
        

    

