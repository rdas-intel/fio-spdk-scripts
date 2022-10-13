import json
import os
from os.path import exists, abspath, dirname, basename
#from os.environ import get as EnvGet
from pathlib import Path
import argparse
import xlrd, xlwt

from copy import deepcopy
from xlutils.copy import copy
import numpy as np
import pandas as pd
from pandas import Series, DataFrame   
import time
from Cmd import Q_Cmd_Ext, Q_Remote_Cmd, Q_Remote_S_Result
with_log = False
def Enable_Log(enable=True):
    global with_log
    with_log = enable

def LogOut(s1="", s2="", s3="", s4="",s5="",s6="",s7="",s8="",s9="",s10=""):
    global with_log
    if with_log == False:
        return
    print(s1,s2,s3,s4,s5,s6,s7,s8,s9,s10)

def Env_Read(env_k):
    return os.environ.get(env_k, "")
def Env_Set(env_k, new_v):
    os.environ[env_k] = new_v

# Save nddarray to an excel file with sheet name
def Save_ndarray_cases(header, ndarray, filename, sheet_name, not_sort=False):
    writer = pd.ExcelWriter(filename)
    
    df = pd.DataFrame(data=ndarray, columns =header)
    if not not_sort:
        dn = df.sort_values(by='case')
    df.to_excel(writer,index=False,sheet_name=sheet_name)
    writer.save()


#Cartesian products of lists    
class Cartesian():
    def __init__(self, datagroup):
        self.datagroup = datagroup
        self.counterIndex = len(datagroup)-1
        self.counter = [0 for i in range(0, len(self.datagroup))]
        self.combination = []
    def countlength(self):
        i = 0
        length = 1
        while(i < len(self.datagroup)):
            length *= len(self.datagroup[i])
            i += 1
        return length
    
    def handle(self):
        self.counter[self.counterIndex]+=1
        if self.counter[self.counterIndex] >= len(self.datagroup[self.counterIndex]):
            self.counter[self.counterIndex] = 0
            self.counterIndex -= 1
            if self.counterIndex >= 0:
                self.handle()
            self.counterIndex = len(self.datagroup)-1

    def assemble(self):
        length = self.countlength()
        i = 0
        while(i < length):
            attrlist = []
            j = 0
            while(j<len(self.datagroup)):
                attrlist.append(self.datagroup[j][self.counter[j]])
                j += 1
            self.combination.append(attrlist)
            self.handle()
            i += 1
        return self.combination    
# Parsing Range and Multiple setting, return list
def Get_Test_Item_Ranges(ti, para):
    i_l = {}
    single_item = True
    for key in para.keys():
        if "Range" in ti[key]:  #Example of Range:     Range: From:2 To: 20 Step:2
            print(  " \t", key,":", ti[key])
            r = ti[key].replace("Range:", "").replace(";", "").replace(",", "")
            rl = r.split(":")
            try:
                r_f = int(rl[1].lower().replace("to", ""))
                r_t = int(rl[2].lower().replace("step", ""))
                r_s= int(rl[3])
                g_r_l = list(range(r_f, r_t, r_s))
                i_l[key] = g_r_l
                single_item = False
            except:
                print( " \t", ti[key], ", Range defintion error.")
        if "Multiple" in ti[key]:  #Example of Multiple:     Multiple:256k;128k;512;1k
            print( " \t", key,":", ti[key])
            r = ti[key].replace("Multiple:", "").split(";")
            r_clean = []
            for r_n in r:
                r_n_s = r_n.strip()
                if r_n_s is not "":
                    r_clean.append(r_n_s)
                    
            if len(r_clean) > 0:
                i_l[key] = r_clean
                single_item = False
            else:
                print( " \t",ti[key], ", Multiple defintion error with len=", len(r_clean))
        if "Mix" in ti[key]:  #Example of Multiple:     Mix:256k;128k;512;1k
            print( " \t", key,":", ti[key])
            r = ti[key].replace("Mix:", "").split(";")
            r_clean = []
            for r_n in r:
                r_n_s = r_n.strip()
                if r_n_s is not "":
                    r_clean.append(r_n_s)
                    
            if len(r_clean) > 0:
                i_l[key] = r_clean
                single_item = False
            else:
                print( " \t",ti[key], ", Multiple defintion error with len=", len(r_clean))
    if not single_item:
        print(" \t  ==> ", i_l)
    return(i_l, single_item)

# Get Cartesian products of items list      
def Get_Items_Combination(items):
    comb = []
    cartesian = Cartesian(items)
    comb = cartesian.assemble()
    return comb
    
# Get Cartesian products of paras with range    
def Get_Range_Item_Combination(paras_with_range):
    comb = []
    keys =  list(paras_with_range.keys())

    datagroup = []
    for key in keys:
        datagroup.append(paras_with_range[key])
    cartesian = Cartesian(datagroup)
    comb = cartesian.assemble()
    return keys, comb

# Expand test cases with Cartesian products of item combination, return item list
def New_Items_From_Ranges(item, paras_with_range, seperate=True):
    keys, comb = Get_Range_Item_Combination(paras_with_range)
    items = []
    r = 0
    for c in comb:
        fio_p = item.copy()
        for i in range(len(keys)):
            fio_p[keys[i]] = c[i] 
        if seperate:
            fio_p['case'] =   str(fio_p['case']) + "_r_" + str(r)
        fio_p['title_fio'] = fio_p['work_type']
        #print(fio_p)
        items.append(fio_p)
        r += 1
    return items

def Hide_colums_in_Xls(xls_sheet, columes):
    for c in columes:
        xls_sheet.col(c).hidden = 1
def Hide_rows_in_Xls(xls_sheet, row):
    for r in rows:
        xls_sheet.row(r).hidden = 1
def Update_Result_2_Xls(xls_sheet, row, colume, v_l, offset = 1):
    xls_sheet.write(row - offset, colume, v_l)
def Get_Cell_Value_From_Xls(xls_sheet, row, colume):
    return xls_sheet.row_values(row)[colume]
def Xls_Set_Value_BkgColor(xls_sheet, row, colume, v_l, offset = 1, bkg_color=5):
    pattern = xlwt.Pattern() # Create the Pattern
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN # May be: NO_PATTERN, SOLID_PATTERN, or 0x00 through 0x12
    pattern.pattern_fore_colour = bkg_color # May be: 8 through 63. 0 = Black, 1 = White, 2 = Red, 3 = Green, 4 = Blue, 5 = Yellow, 6 = Magenta, 7 = Cyan, 16 = Maroon, 17 = Dark Green, 18 = Dark Blue, 19 = Dark Yellow , almost brown), 20 = Dark Magenta, 21 = Teal, 22 = Light Gray, 23 = Dark Gray, the list goes on...
    style = xlwt.XFStyle() # Create the Pattern
    style.pattern = pattern # Add Pattern to Style
    xls_sheet.write(row -offset, colume, v_l, style)

def df_2_csv(fn, df, index=False, sep=',',na_rep=""):
    df.to_csv(fn, index=index, sep=sep,na_rep=na_rep)
    
def load_csv(fn, seperate=";",skiprows=0,header=None):
    return pd.read_csv(fn, sep=seperate, header=header, engine='python', skiprows=skiprows)    
def load_xls_sheet(xls_fn, sheet_name):
    df = pd.read_xls(open(xls_fn, 'rb'), sheet_name=sheet_name)
    return df
def load_sheet_from_xls(IO, sheet_name):
    if not exists(IO):
        print("Error. Fail to find", IO)
        return None, None
    try:
        df = pd.read_excel(io=IO, sheet_name=sheet_name,header=0)
        #print(df.keys())
    except:
        print("Error. Fail on loading ", sheet_name, "from", IO)
        return None, None
    return df, list(df.keys())
def save_csv_2_xls(xls_fn, sheet_name, df,writer=None, index=False,final=True):
    if writer is None:
        writer = pd.ExcelWriter(xls_fn)
    df.to_excel(writer,index=index,sheet_name=sheet_name)
    if final:
        writer.save()
    return writer
def save_array_2_xls(xls_fn, sheet_name, array, head=[], with_index=False, Final=True, writer=None):

    df=pd.DataFrame(array)
    df.columns = head
    if writer == None:
        writer = pd.ExcelWriter(xls_fn)
    df.to_excel(writer,index=with_index,sheet_name=sheet_name)
    if Final:
        writer.save()
    return writer


def Xls_Read_Worksheet(xls_file, sheet_name):
    workbook_fn = xls_file
    try:
        print("Opening", workbook_fn)
        workbook = xlrd.open_workbook(workbook_fn) 
        #print("work_book is opened")
    except:          
        print("Error! Fail to open workbook ", workbook_fn, ". Please provide right xls file name.")
        exit(1)
    
    case_sheet_name = sheet_name
    try:
        cases_sheet = workbook.sheet_by_name(case_sheet_name)    
        case_sheet_id = workbook.sheet_names().index(case_sheet_name)
    except:          
        print("Fail to open sheet ", case_sheet_name, " in ", workbook_fn)
        exit(1)

    return workbook, cases_sheet

def Xls_Read_Row(sheet, row, start_from=0):
    return sheet.row_values(row - start_from)

def Inside_container():
    d_s = "cat  /proc/self/cgroup | grep docker"
    ic = Q_Cmd_Ext(d_s)
    return len(ic) != 0

nodes_cpus = {}
def Init_Nodes_CPUs():
    nodes_cpu_cmd = "numactl --hardware | grep  cpus "
    nc = Q_Cmd_Ext(nodes_cpu_cmd)
    return nc
    
def utils_test():
    nc = Init_Nodes_CPUs()
    print(nc)
    
def get_remote_time(server_ip):
#    cmd='date +"%Y-%m-%d %H:%M.%S" '
    cmd='date  ' ' +%Y%m%d%H%M%S '

    dt = Q_Remote_Cmd(server_ip, cmd, silent_mode=True)
    r = Q_Remote_S_Result()
    ds = r[len(r) - 1]
    year=ds[:4]
    month=ds[4:6]
    day=ds[6:8]
    hour=ds[8:10]
    minute=ds[10:12]
    print(ds)
    
    ds_= str(year) + "-" +  str(month) + "-" + str(day) + " " + str(hour) + ":"  +str(minute)
    return ds_
def update_date_time(s):
    cmd='date  -s  ' + '"' + s + '"'
    
    return Q_Cmd_Ext(cmd)


def get_statistics(dl):
    npl = np.array(dl) 
    std_v = np.std(npl,ddof=1)
    _max = np.max(npl)
    _min = np.min(npl)
    _mean= np.mean(npl)
    #df= pd.DataFrame(dl)
    npls=np.sort(npl)
    p95 = np.percentile(npls, 95)
    return _mean, std_v, _min, _max, p95

def load_add_cfg(cfg_file):
    print("\n\n===>Loading", cfg_file)
    with open(cfg_file, 'r') as f:
        user_dic = json.load(f)
        return user_dic   
    print("Fail to load cfg file ", cfg_file)
    return None    

def load_json(json_file):
    with open(json_file, 'r') as f:
        user_dic = json.load(f)
        return user_dic   
    print("Fail to load json file ", json_file)
    return None    
def save_json(json_file,data):
    with open(json_file, 'w') as f:
        json.dump(data, f)
        return

def get_files_from_folder(path, ext=".xls", _filter=""):
    import os
    files = []
    def listdir(path, ext, list_name = []): 
        #print(path, ext)
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
    #print(path)
    if os.path.isdir(path):
        listdir(path, ext, files)
    return files        
if __name__ == '__main__':
    #utils_test()
    rd = get_remote_time("10.239.89.154")
    update_date_time(rd)
    print(rd)

