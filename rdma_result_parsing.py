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

from utils import load_sheet_from_xls,df_2_csv, get_files_from_folder, load_csv
from Cmd import Q_Cmd

with_log = True
#with_log = False
rdma_result_parsing = {
               "cmd_ws": os.path.abspath(os.path.dirname(__file__)), 
               "work_folder": os.path.abspath(os.path.dirname(__file__)), 
               "input_folder":   "/media/data/ml/ice/rdma_2ports_bi_direction_ddio_swapping",
               "input_csv":   "/media/data/ml/ice/rdma_4ports_bi_direction_ddio_swapping/ddio_0x6000__1_1st_ib_write_bw_qp_1_log.txt_result.csv",
               "excluding":   "",
               "including":  "",
               "catogary":  "ddio_parsing",
               "header":  "",
               "extra_header":  "",
               "output_csv":  "overall_result.csv",
}





    
def main():
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--input_folder', type=str,help='folder name of xls, default is empty. If not default, all xls file inside will  will be processed', default= rdma_result_parsing["input_folder"])
    parser.add_argument('--input_csv', type=str,help='csv file to be processed. Valid only when the input_folder is empty. ', default=rdma_result_parsing["input_csv"])
    parser.add_argument('--excluding', type=str,help='csv file to be excluded in the file name. Valid only with folder. ', default=rdma_result_parsing["excluding"])
    parser.add_argument('--including', type=str,help='csv file to be included in the file name. Valid only with folder.', default=rdma_result_parsing["including"])    
    parser.add_argument('--catogary', type=str,help='csv file type for parsing. ddio_parsing bkc customer', default=rdma_result_parsing["catogary"])    
    parser.add_argument('--header', type=str,help=' header for  customerized catogary,seperated with  , ', default=rdma_result_parsing["header"])    


    args = parser.parse_args()
    print(args)

    rdma_result_parsing["input_folder"] = args.input_folder
    rdma_result_parsing["input_csv"] = args.input_csv
    rdma_result_parsing["excluding"] = args.excluding
    rdma_result_parsing["including"] = args.including
    rdma_result_parsing["catogary"] = args.catogary
    rdma_result_parsing["header"] = args.header

    def parsing_fn(base_fn):
        if rdma_result_parsing["catogary"] == "ddio_parsing":
            items=base_fn[:-4].replace("__","_").split("_")
            #print(items)
            if len(items) > 8:
                return [base_fn, items[1], items[2],items[3],items[8]]
                if len(header) > 0:
                    return header
        if rdma_result_parsing["catogary"] == "customer":
            items=base_fn[:-4].replace("__","_").split("_")
            return items
        return [base_fn]   
        #interesting[2, 3,8]
    def processing_csv(fn):

        base_fn= os.path.basename(fn)
        #print("Parising csv: ", fn, base_fn)
        extra = parsing_fn(base_fn)
        #print(interesting, extra)
        df = load_csv(fn, skiprows=1, seperate="\\s+")
        #df = load_csv(fn, seperate="\r\t\s+", header=0)        
        #print(df)
        #print(df.index)
        #print(df.columns)
        ndf = []
        for idx in df.index:
            v = np.array(df.iloc[idx]).tolist()
            v_a = extra + v
            #print(v_a)
            ndf.append(v_a)
        #print(ndf)
        return ndf
        #df.columns = header
        #print(df[df>1.0])

    def get_extra_header(m, header):
        if rdma_result_parsing["catogary"] == "ddio_parsing":
            return    ["fn", "ddio_reg", "#port","#direction","qp"]    

        if rdma_result_parsing["catogary"] == "customer":
            if rdma_result_parsing["header"] != "":
                return rdma_result_parsing["header"].split(",")
               
        left = len(m[0]) - len(header)
        interesting=[]
        for i in range(left):
            interesting.append(str(i))
        return interesting
        
    if rdma_result_parsing["input_folder"] == "":
        df = processing_csv(rdma_result_parsing["input_csv"])# , rdma_result_parsing["sheet_name"].strip())
        print(df)
        return
    result_csv_files = get_files_from_folder(rdma_result_parsing["input_folder"], ext=".csv", _filter="_result")
    #print(result_csv_files)
    merged=[]
    for x in result_csv_files :
        ignore = False
        if "overall" in x:
            continue
        if  rdma_result_parsing["excluding"] != "" and rdma_result_parsing["excluding"] in x:
            continue
        if  rdma_result_parsing["including"] != "" and rdma_result_parsing["including"] not in x:
            continue
        df = processing_csv(x)
        print(x)
        if merged == []:
            merged = df
        else:
            merged.extend(df)
    header=['#bytes', '#iterations', 'BW peak[Gb/sec]', 'BW average[Gb/sec]','MsgRate[Mpps]']    
    interesting=get_extra_header(merged,header)
    output_csv = rdma_result_parsing["input_folder"]+ "/" + rdma_result_parsing['output_csv'] 
    all_header=interesting + header
    all_df = DataFrame(merged)
    all_df.columns = all_header
    print(all_df.head)
    print("Overall result is saved to ", output_csv)
    df_2_csv(output_csv,all_df)
    exit()
    
if __name__ == '__main__':
    main()
        

    

