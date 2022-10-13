import os
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from pandas import Series, DataFrame   


with_log = True
with_log = False
power_monitor_parsing_running = {
               "cmd_ws": os.path.abspath(os.path.dirname(__file__)), 
               "work_folder": os.path.abspath(os.path.dirname(__file__)), 
               "input_folder":   "",
#               "input_folder":   "./xiperf_6_ports_3vms_simple/",
#               "input_log":   "rapl.log",
               "input_log":   "",
}
__ERROR_FLOAT=float(0.0000000001)

def df_2_csv(fn, df, index=False, sep=',',na_rep=""):
    df.to_csv(fn, index=index, sep=sep,na_rep=na_rep)

def get_files_from_folder(path, ext=".xls", _filter=""):
    import os
    files = []
    def listdir(path, ext, list_name = []):  
        for file in os.listdir(path):  
            file_path = os.path.join(path, file)  
            if os.path.isdir(file_path):  
                listdir(file_path, ext, list_name)  
            elif ext in  os.path.splitext(file_path)[1]:  
                if _filter != "":
                    if _filter in os.path.splitext(file_path)[0]:
                        list_name.append(file_path) 
                else:
                        list_name.append(file_path) 
    if os.path.isdir(path):
        listdir(path, ext, files)
    return files   
    
def get_df_statistics(df):
    df_stat = []
    st_header = ["max", "min", "mean","std","p99"]
   
    df_stat.append(list(df.max().values))
    df_stat.append(list(df.min().values))
    df_stat.append(list(df.mean().values))
    df_stat.append(list(df.std().values))
    p99 = []
    for c in df.columns:
        las = las=np.sort(df[c].values)
        p99.append(np.percentile(las, 99))    
        
    df_stat.append(p99)
    return  st_header, df_stat
def read_rapl_log(input_file=power_monitor_parsing_running["input_log"]):
    records = []
    record = []
    header = []
    secord = 0
    with open(input_file, "r") as logfile:
        line = logfile.readline()
        idx = -1
        while len(line) != 0:
            if "package-0" in line:
                idx += 1
                if len(record) != 0:
                    records.append(record)
                    record = []
            r = line.split(":")[1].replace(" ", "").replace("J", "").replace("\n", "")
            f = float(r)
            if f < __ERROR_FLOAT:
                f = __ERROR_FLOAT
            record.append(f)
            if idx < 1:
                h = line.split(":")[0].replace(" ", "").replace("\t", "")
                header.append(h)

            line = logfile.readline()
    if len(record) != 0:
        records.append(record)
    if len(records) == 0 :
        print("Fail to load ", input_file)
        exit(1)
    package=""
    for i in range(len(header)):
        if "package" in header[i]:
            package = header[i]
        else:
            header[i] = package + "-" + header[i]       
    return header, records

    
def parsing_a_single_rapl_log(logfile=power_monitor_parsing_running["input_log"]):
    print("\nParsing",logfile)
    header, records = read_rapl_log(input_file=logfile)
    r = pd.DataFrame(records,columns=header)
    st_header, st  = get_df_statistics(r)

    st_df = pd.DataFrame(st, columns=header)
    st_header_df = pd.DataFrame(st_header)
    st_df['statistics'] = st_header_df.values
    n_header = ["statistics"] + header
    st_df =  st_df[n_header]
    print(st_df)

    df_file_name = logfile + ".csv"
    df_st_file_name = logfile + "_statistics.csv"
    
    df_2_csv(df_file_name, r, index=False)
    df_2_csv(df_st_file_name, st_df, index=False)
    print("Saved to ", df_file_name, df_st_file_name)
    return r, st_df

def get_rapl_log_files(input_folder=power_monitor_parsing_running["input_folder"]):
    logs = get_files_from_folder(input_folder, ext=".log",_filter="rapl")
    return logs
def convert_statistics(df, col, file_name):
    v = [file_name]
    for c in col:
        cv = list(df[c].values)
        #print(cv)
        v.extend(cv)
    return v
    #print(v)
def get_st_table_header(df):
    st_name='statistics'
    col = list(df.columns)
    st = list(df[st_name])
    col.remove(st_name)
    header = []
    for c in col:
        for s in st:
            h = c + "_" + s
            header.append(h)
            
    return col, st, header
def main():
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--input_log', type=str,help='the log file of sys_start_power_monitor.sh  ', default=power_monitor_parsing_running["input_log"])
    parser.add_argument('--input_folder', type=str,help='The input folder to check power monitor logs. All *rapl.log under the folder will be parsed. ', default=power_monitor_parsing_running["input_folder"])

    args = parser.parse_args()
    print(args)

    power_monitor_parsing_running["input_log"] = args.input_log
    power_monitor_parsing_running["input_folder"] = args.input_folder
    if power_monitor_parsing_running["input_folder"] !="":
        logs = get_rapl_log_files(power_monitor_parsing_running["input_folder"])
        print("input_folder:", power_monitor_parsing_running["input_folder"], "rapl log files:", logs)
        st_tables_h= ["file_name"]
        sts = []
        for f in logs:
            r, st_df = parsing_a_single_rapl_log(logfile = f)
            file_name = os.path.basename(f)
            if len(st_tables_h) == 1:
                col, st, st_tables_header = get_st_table_header(st_df)
                st_tables_h.extend(st_tables_header)
            v = convert_statistics(st_df, col, file_name)
            sts.append(v)
        sts_df =  pd.DataFrame(sts, columns=st_tables_h)
        folder_pure_name =  power_monitor_parsing_running["input_folder"].strip().split("/")
        folder_pure_name_1 = folder_pure_name[-1] if folder_pure_name[-1]!="" else folder_pure_name[-2]
        print(folder_pure_name, folder_pure_name_1)
        ext = "/" if folder_pure_name[-1] !="" else ""
        sts_file_name =  power_monitor_parsing_running["input_folder"].strip() + ext + folder_pure_name_1 + "_statistics.csv"
        print(sts_df)
        df_2_csv(sts_file_name, sts_df, index=False)
        print("Saved to ", sts_file_name)

    elif power_monitor_parsing_running["input_log"] != "":
        parsing_a_single_rapl_log(logfile=power_monitor_parsing_running["input_log"])

    else:
        print("Please provide rapl log file or folder that contains rapl log. ")
        
    exit()
    
if __name__ == '__main__':
    main()
        

    

