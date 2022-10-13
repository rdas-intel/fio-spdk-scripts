import json
import os
from os.path import exists, abspath, dirname, basename
from pathlib import Path
import argparse
import xlrd
from copy import deepcopy
from xlutils.copy import copy
import numpy as np
import pandas as pd
from pandas import Series, DataFrame   
import time

#import FioResultDecoder
from dateutil.parser import parse
from Cmd import Q_Cmd, C_CMD, CMD_Group, Export_Env, __ERROR_INT
from CFio import Fio_Init, Fio_nvme_spdk_setup, FIO_Para,New_Fio_Case, xls_fio_keys_offset, Fio_Get_Cmd_Paras, FIO_Parser_Json_Result, FIO_Result_Additional, Fio_Get_Additional_Result_Items
from CIperf import  xls_iperf_keys_offset, New_Iperf_Case, New_Iperf_Cmd, Start_Iperf_Cmds, Wait_Iperf_Cmds_Done, Iperf_Init, Iperf_Close, Iperf_Parsing_Result, Iperf_Update_Result_2_Xls
from utils import Save_ndarray_cases, Get_Items_Combination , Get_Test_Item_Ranges,New_Items_From_Ranges, Update_Result_2_Xls, Get_Cell_Value_From_Xls
from SysInfo import Collect_Sys_Info



IO_Running = {
               "cmd_ws": os.path.abspath(os.path.dirname(__file__)), 
               #"test_case_xls":  os.path.abspath(os.path.dirname(__file__)) + "/SPR_storage.xls",
               "test_case_xls":  os.path.abspath(os.path.dirname(__file__)) + "/SPR_storage.xlsx",
               "case_sheet": None,
               "test_case_generated_xls": "",
               "expand_mix_cases_xls": "",
               "result_xls": "",
               "output_sheet": "",
               "case_generating": False,
               "run_single": 0,
               "run_from": 0,
               "run_from_to": "",
               "run_to": __ERROR_INT,
               "work_space": "./",
               "result_folder": "./_result",
               "test_case_sheet": "Fio",
               "fio_output":"JSON",
               "case_read_sheet": None,
               "case_read_wb": None,
               "case_write_sheet": None,
               "case_write_wb": None,
               "fio_rampup": 5,
               "fio_runtime": 90,
               "fio_engine": "sync", #libaio 
                "fio_iodepth_dynamic": 0,               
                #"fio_device": "/media/data/ml/storage_io/Storage/test",               #with key word DEFAULT
                "fio_device": "",               #with key word DEFAULT
                "fio_cmd": "run_fio_case.sh ",
                "fio_default_para": "fio_libaio",
                "fio_reult_key_index": 5,
                "fio_reult_key_name": "run_status",
                "row_offset": 1,
                "title_key": "title_",
                "title_position": 0,
                "fio_key": "fio_",
                "iperf_key": "iperf",
                "fio_header": None,
                "iperf_header": None,
                "iperf_reult_key_index": 5,
                "iperf_reult_key_name": "run_status",               
                "iperf_additional_para_windows_size":"",
                "iperf_additional_para_buffer_size":"",
                #"iperf_client": "10.112.227.155",               
                #"iperf_client": "10.239.85.52",               
                "iperf_client": "192.168.122.61",               
                "with_iperf": False,               
                "with_fio": False,               
                "sysinfo": False, 
                "fio_simulation": "TRUE", 
                "fio_nvme_env":{},
}

fio_envs = {
    "WORK_SPACE": IO_Running["work_space"],
    "FIO_ENGINE": IO_Running["fio_engine"],
    "FIO_RUNTIME": IO_Running["fio_runtime"],
    "FIO_OUTPUT": IO_Running["fio_output"],
    "FIO_RAMPUP": IO_Running["fio_rampup"],
    "FIO_SIMULATION": IO_Running["fio_simulation"],
}

fio_cmd_cfg_template = {
                            "cmd": IO_Running["cmd_ws"] + "/" + IO_Running["fio_cmd"],
}
fio_result_items = []



def Fio_Reload_Env_Settings():
    for key in fio_envs.keys():
        fio_envs[key] = IO_Running[key.lower()]


def Run_Pre_Post_Process(paras, pre=True):
    for para in paras:
        k = "pre_process" if pre else "post_process"
        exe_cmd = para[k]  if k in para.keys() else None
        if exe_cmd is not None and exe_cmd != "NA":
            print(k, ": ", exe_cmd)
            print(Q_Cmd(exe_cmd))
    
def Run_Grouped_Cases(paras):
    fio_cmds = []
    iperf_cmds = []
    Run_Pre_Post_Process(paras, pre=True)
    for para in paras:
        if IO_Running["fio_key"] in para["work_type"]:
            cfg = fio_cmd_cfg_template.copy()
            cfg["default_para"] = para["work_type"]  + " " + Fio_Get_Cmd_Paras(para)
            if IO_Running["fio_iodepth_dynamic"] > 0:
                if para["numjobs"] != "NA":
                    try:
                        fio_envs["FIO_IODEPTH"] = str(int(para["numjobs"]) * IO_Running["fio_iodepth_dynamic"])
                    except:
                        print("Error: fio_iodepth_dynamic can only work with right number job settings")
                        exit(1)
            fio_cmd = C_CMD(cfg = cfg, simulation = False, show_all=False,  block_mode=False, extra_paras=fio_envs, process_extra_paras=Export_Env) 
            fio_cmds.append(fio_cmd)
        elif  IO_Running["iperf_key"] in para["work_type"]:
            iperf_cmd = New_Iperf_Cmd(para)
            iperf_cmds.append(iperf_cmd)
    if len(fio_cmds) > 0:
        fio_cg =   CMD_Group(cmds=fio_cmds, pre_run=Fio_nvme_spdk_setup,pre_run_para=paras)
     
    if len(fio_cmds) > 0:
        fio_cg.group_exe(block_mode=False)
        localtime = time.asctime( time.localtime(time.time()) )
        print("     \t==>Fio case started at", localtime)

    Start_Iperf_Cmds(iperf_cmds, IO_Running["iperf_additional_para_windows_size"], IO_Running["iperf_additional_para_buffer_size"])

    if len(fio_cmds) > 0:
        fio_cg.wait_for_group_exe_done()
        localtime = time.asctime( time.localtime(time.time()) )
        print("\n\n     \t==>Fio case done at", localtime)
    Wait_Iperf_Cmds_Done(iperf_cmds)
    Run_Pre_Post_Process(paras, pre=False)

    #print("line 145, Io_test.py Temporally added for debugging")
    #exit(1)

def Get_Header(work_type):
    if "fio" in work_type:
        return IO_Running["fio_header"]
    elif "iperf" in work_type:
        return IO_Running["iperf_header"]
        
def Update_Header(title_type, head_row):
    if "fio" in title_type:
        IO_Running["fio_header"] = head_row
        Keys_Offset("fio", head_row)
    elif "iperf" in title_type:
        IO_Running["iperf_header"] = head_row
        Keys_Offset("iperf", head_row)


def Keys_Offset(h_type, d):
    if "fio" in h_type:
        for (offset,items) in enumerate(d): 
            xls_fio_keys_offset[items] = offset
        IO_Running["fio_reult_key_index"] = xls_fio_keys_offset[IO_Running["fio_reult_key_name"]]
    elif "iperf" in h_type:
        for (offset,items) in enumerate(d): 
            xls_iperf_keys_offset[items] = offset
        IO_Running["iperf_reult_key_index"] = xls_iperf_keys_offset[IO_Running["iperf_reult_key_name"]]

'''    
def Key_Offset(d, k):
    for (offset,items) in enumerate(d): 
        if items == k:
            return offset
    return None
'''

fio_analyser = {
#    "fio_result_items": ["usr_cpu", "sys_cpu", "read_bw", "write_bw", "read_iops", "write_iops"],
    "fio_result_items": ["usr_cpu", "sys_cpu", "read_bw(MiB/s)", "write_bw(MiB/s)", "read_iops", "write_iops"],
    "fio_result_append_s": "t_",
    "fio_result_append_items": ["t_usr_cpu", "t_sys_cpu", "t_read_bw(MiB/s)", "t_write_bw(MiB/s)", "t_read_iops", "t_write_iops"],
}
def Group_Analyser(cases):
    group_c = {}
    for c in cases:
        c_id_s = c[xls_fio_keys_offset["case"]]
        if c_id_s in group_c.keys():
            group_c[c_id_s]["items"].append(c)
            for ri in fio_analyser["fio_result_items"]:
                ri_append = fio_analyser["fio_result_append_s"] + ri
                if str(group_c[c_id_s][ri_append])  is not "":
                    if str(c[xls_fio_keys_offset[ri]]) is not "":
                        group_c[c_id_s][ri_append] += c[xls_fio_keys_offset[ri]]
                else:
                    group_c[c_id_s][ri_append] = c[xls_fio_keys_offset[ri]]

        else:
            group_c[c_id_s] = {}
            group_c[c_id_s]["items"] = [c]
            for ri in fio_analyser["fio_result_items"]:
                ri_append = fio_analyser["fio_result_append_s"] + ri
                group_c[c_id_s][ri_append] = c[xls_fio_keys_offset[ri]]
    return   group_c   

def Fill_Analyse_2_Cases_List(cases, group_c):
    cases_with_analysis = []
    for c in cases:
        c_id_s = c[xls_fio_keys_offset["case"]]
        if c_id_s in group_c.keys():
            for ri in fio_analyser["fio_result_items"]:
                ri_append = fio_analyser["fio_result_append_s"] + ri
                c.append(group_c[c_id_s][ri_append])
            del group_c[c_id_s]      
        else:
            for ri in fio_analyser["fio_result_items"]:
                c.append("")
        cases_with_analysis.append(c)
    return cases_with_analysis

# To get to start row number of real cases, ignore the title rows
# Update the header for each work_type
def Get_Row_Offset(cases_sheet):
    for row in range(0, cases_sheet.nrows):
        k_item = cases_sheet.row_values(row)
        if IO_Running["title_key"] not in k_item[IO_Running["title_position"]]:
            IO_Running["row_offset"] = row
            break;
        else:
            Update_Header(k_item[IO_Running["title_position"]], k_item)
    
            
def Get_Cases_From_Xls(analyser=False):
    workbook_fn = IO_Running["test_case_xls"]
    try:
        workbook = xlrd.open_workbook(workbook_fn) 
        IO_Running["case_write_wb"] = copy(workbook)
    except:          
        print("Error! Fail to open workbook ", workbook_fn, ". Please provide right test_case_xls.")
        exit(1)
    
    case_sheet_name = IO_Running["test_case_sheet"]
    try:
        cases_sheet = workbook.sheet_by_name(case_sheet_name)    
        case_sheet_id = workbook.sheet_names().index(case_sheet_name)
        IO_Running["case_write_sheet"] = IO_Running["case_write_wb"].get_sheet(case_sheet_id)    
        IO_Running["case_sheet"] = cases_sheet    
        IO_Running["case_sheet_id"] = case_sheet_id    
    except:          
        print("Fail to open sheet ", case_sheet_name, " in ", workbook_fn)
        exit(1)
    print("\nUsing workbook:", workbook_fn, " sheet:", case_sheet_name, "\n")

    Get_Row_Offset(cases_sheet)
    cases = []
    if analyser is False:
        for row in range(IO_Running["row_offset"], cases_sheet.nrows):
            c = None
            k_item = cases_sheet.row_values(row)
            #remove no use colum and do para check
            if IO_Running["fio_key"] in k_item[IO_Running["title_position"]]:
                if not "spdk" in k_item[xls_fio_keys_offset["title_fio"]]:
                    if IO_Running["test_case_generated_xls"] is "" and IO_Running["expand_mix_cases_xls"] is "" and "DEFAULT" in k_item[xls_fio_keys_offset["device_name"]].upper(): 
                        k_item[xls_fio_keys_offset["device_name"]] = IO_Running["fio_device"]
                c = New_Fio_Case(k_item, row, IO_Running["case_generating"], IO_Running["row_offset"], k_item[IO_Running["title_position"]], IO_Running)
                IO_Running["with_fio"] = True
            elif IO_Running["iperf_key"] in k_item[IO_Running["title_position"]]:
                c = New_Iperf_Case(k_item, row, IO_Running["case_generating"], IO_Running["row_offset"], k_item[IO_Running["title_position"]], IO_Running)
                IO_Running["with_iperf"] = True
            if c is not None:
                cases.append(c)
        return cases
    else:
        #return original xls cases item list for analysing
        for row in range(IO_Running["row_offset"], cases_sheet.nrows):
            k_item = cases_sheet.row_values(row)
            if k_item is not None:
                cases.append(k_item)
        return cases

# put the cases in to lists group based case name        
def Group_Cases(cases):
    group_c = {}
    for c in cases:
        c_id_s = c["case"]
        if c_id_s in group_c.keys():
            group_c[c_id_s].append(c)
        else:
            group_c[c_id_s] = [c]
    return   group_c     


def Get_Result_File_Name(para, ext=".json"):
    result_folder = IO_Running["result_folder"] 
    fn = result_folder + "row_" + str(para["row"]) +  ext
    return fn


def Get_Result_Items(re):
        if fio_result_items == []:
            for k in xls_fio_keys_offset.keys():
                if k in re.keys():
                    fio_result_items.append(k)

        return fio_result_items

#def Update_Result_2_Xls(row, item, v_l):
#    IO_Running["case_write_sheet"].write(row - 1, xls_fio_keys_offset[item], v_l)
    
def Get_Group_Result(paras):
    cmds = []
    Fio_Get_Additional_Result_Items()
    for para in paras:
        fn = Get_Result_File_Name(para)
        #print(fn)
        if "fio" in para["work_type"]:
            re_ = FIO_Parser_Json_Result(fn)
        
            if re_ is not None:
                re = re_["jobs"][0]
                re_items = []
                for item in Get_Result_Items(re):
                    if item in re.keys():
                        re_items.append(str(re[item]))
                        Update_Result_2_Xls(IO_Running["case_write_sheet"], para["row"] , xls_fio_keys_offset[item], re[item])
                        run_status = "OK"
                print(" \t".join(re_items))
                added = FIO_Result_Additional(re)
                for key in added.keys():
                    if key in xls_fio_keys_offset.keys():
                        Update_Result_2_Xls(IO_Running["case_write_sheet"], para["row"] , xls_fio_keys_offset[key], added[key])
                
            else:
                print("Failed case", para)
                run_status = "Error"
            Update_Result_2_Xls(IO_Running["case_write_sheet"], para["row"] , xls_fio_keys_offset[IO_Running["fio_reult_key_name"]], run_status)
            #update the defult device name to real one
            d = Get_Cell_Value_From_Xls(IO_Running["case_sheet"], para["row"] - IO_Running["row_offset"], xls_fio_keys_offset["device_name"])
            if "DEFAULT" in d.upper():
                Update_Result_2_Xls(IO_Running["case_write_sheet"], para["row"] - IO_Running["row_offset"], xls_fio_keys_offset["device_name"], IO_Running["fio_device"], 0)
        elif "iperf" in para["work_type"]:
            re_ = Iperf_Parsing_Result(fn, para["direction"])
            Iperf_Update_Result_2_Xls(IO_Running["case_write_sheet"], para["row"],re_)
            if re_ is not None:
                print(re_)
                run_status = "OK"
            else:
                run_status = "Error"            
            Update_Result_2_Xls(IO_Running["case_write_sheet"], para["row"] , xls_iperf_keys_offset[IO_Running["iperf_reult_key_name"]], run_status)
def get_default_output_fn():
    if IO_Running["fio_device"] == "":
        return ""
    dl = ""
    for device in IO_Running["fio_device"].split(";"):
        n = device.split("n1")[0].replace("nvme", "")
        if n != "":
            dl = dl + "_" + n
    if dl != "":
        return "nvme"+dl + ".xls", "nvme"+dl
    return ""

def Fio_Case_Generating(gc, seperate=True):
    rows = []
    cases = []
    for g  in gc.keys():
        test_case = gc[g]
        print("\ngenerating case ", g, test_case)
        item_l = []
        for i in range(len(test_case)):
            #generate combination for each item
            case = []
            test_item  = test_case[i]           
            if IO_Running["multiple_default_devices"]:
                if "DEFAULT" in test_item["device_name"].upper(): 
                    test_item["device_name"] = "Mix:"+ IO_Running["fio_device"]

            paras_with_range, single_item = Get_Test_Item_Ranges(test_item, FIO_Para)
            if not single_item:
                items = New_Items_From_Ranges(test_item, paras_with_range, seperate=seperate)
            else:
                items = [test_item]
            for item in items:
                row = []
                for key in IO_Running["fio_header"]:
                    if key in item.keys():
                        row.append(item[key])
                    else:
                        row.append("")
                        #row.append("NA")
                case.append(row)
            item_l.append(case)

        #generate combination for each case
        c_c = Get_Items_Combination(item_l)
        #update the case name, expanding the name to org_name_xx
        n_c_id = 0
        for c in c_c:
            c_copy = deepcopy(c)
            for _item in c_copy:
                if len(c_c) > 1:
                    _item[1] = g + "_" + str(n_c_id)
                else:
                    _item[1] = g
                    
                #_item[0] = "Fio"
            cases.append(c_copy)        
            n_c_id += 1
    for case in cases:
        for r in case:
            rows.append(r)
    #save to new xls        
    ndarray = np.array(rows)   
    output_xls = IO_Running["test_case_generated_xls"] if seperate else IO_Running["expand_mix_cases_xls"]
    base_fn=basename(output_xls)
    dfn, dsheet = get_default_output_fn()
    if base_fn.upper() == "DEFAULT.XLS":
        new_fn = dfn
        if new_fn != "":
            output_xls = dirname(output_xls) + "/" + new_fn
    print(ndarray)
    if IO_Running["output_sheet"] == "":
        IO_Running["output_sheet"] = basename(output_xls).split(".")[0]
    if IO_Running["output_sheet"].upper() == "DEFAULT":
        if dsheet != "":
            IO_Running["output_sheet"] = dsheet
    
    print("Generated xls file:",output_xls, "sheet:", IO_Running["output_sheet"])
    Save_ndarray_cases(IO_Running["fio_header"], ndarray, output_xls, IO_Running["output_sheet"])
    out_xls_ls = "ls -lh " + output_xls
    r_s = Q_Cmd(out_xls_ls)
    print(r_s)
def Get_Single_Case_Of_Row(row, gc):
    for g  in gc.keys():       
        for item in gc[g]:
            if item['row'] == row:
                return g
    print("\nError!, Get_Single_Case_Of_Row not found:", row)
    return None
                
def Get_Single_Cases_from_Row(row, gc, row_end=__ERROR_INT):
    cases_to_run = []
    for g  in gc.keys():       
        for item in gc[g]:
            to_run = True
            if item['row'] < row:
                to_run = False
            if row_end !=__ERROR_INT and item['row'] > row_end:
                to_run = False
            if to_run:
                if g not in cases_to_run:
                    cases_to_run.append(g)
    return cases_to_run
    
def main():
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--test_case_xls', type=str,help='test case workbook in xls format: xxx.xls.', default=IO_Running["test_case_xls"])
    parser.add_argument('--output_test_case_xls', type=str,help='test case in xls format that will be generated: ooo.xls.', default=IO_Running["test_case_generated_xls"])
    parser.add_argument('--expand_mix_cases_xls', type=str,help='test case in xls format that will be generated: ooo.xls.', default=IO_Running["expand_mix_cases_xls"])
    parser.add_argument('--output_sheet', type=str,help='sheet name of generated xls.', default=IO_Running["output_sheet"])
    parser.add_argument('--result_xls', type=str,help='result xls.', default=IO_Running["result_xls"])
    parser.add_argument('--test_case_sheet', type=str,help='input test case worksheet in xls format: fio', default=IO_Running["test_case_sheet"])
    parser.add_argument('--run_single', type=int,help='run single row case with the row number specified: int', default=0)
    parser.add_argument('--run_from', type=int,help='run cases from the row specified: int', default=0)
    parser.add_argument('--run_from_to', type=str,help='run cases from the row specified: int', default="")
    parser.add_argument('--fio_runtime', type=int,help='fio runtime setting: int', default=IO_Running["fio_runtime"])
    parser.add_argument('--fio_rampup', type=int,help='fio rampup setting: int', default=IO_Running["fio_rampup"])
    parser.add_argument('--parsing_only', type=str2bool,help='parsing test result only: True/False', default=False)
    parser.add_argument('--fio_test_result_analyser', type=str2bool,help='anlyse fio test result: True/False', default=False)
    parser.add_argument('--fio_output_json', type=str2bool,help='fio_output in json format for single run: True/False', default=False)
    parser.add_argument('--iperf_client', type=str,help='ip address of client for iperf test', default=IO_Running["iperf_client"])
    parser.add_argument('--fio_device', type=str,help='the default device for fio test, replacing the key word DEFAULT in test case. For multiple nvme devices, seperated by ";"', default=IO_Running["fio_device"])
    parser.add_argument('--fio_engine', type=str,help='io depth', default=IO_Running["fio_engine"])
    parser.add_argument('--sysinfo', type=str2bool,help='Collect system info', default=True)
    parser.add_argument('--simulation_mode', type=str2bool,help='Simulation mode', default=False)
    parser.add_argument('--iperf_additional_para_windows_size', type=str,help='Iperf additional parameter tcp windows size', default=IO_Running["iperf_additional_para_windows_size"])
    parser.add_argument('--iperf_additional_para_buffer_size', type=str,help='Iperf additional parameter buffer size', default=IO_Running["iperf_additional_para_buffer_size"])

    args = parser.parse_args()
    print(args)

    IO_Running["test_case_xls"] = args.test_case_xls
    IO_Running["test_case_generated_xls"] = args.output_test_case_xls
    IO_Running["expand_mix_cases_xls"] = args.expand_mix_cases_xls
    IO_Running["output_sheet"] = args.output_sheet
    IO_Running["result_xls"] = args.result_xls
    IO_Running["test_case_sheet"] = args.test_case_sheet
    IO_Running["fio_runtime"] = args.fio_runtime
    IO_Running["fio_rampup"] = args.fio_rampup
    IO_Running["work_space"] = os.path.abspath(os.path.dirname(IO_Running["test_case_xls"]))
    IO_Running["run_single"] = args.run_single
    IO_Running["run_from"] = args.run_from
    IO_Running["run_from_to"] = args.run_from_to
    IO_Running["iperf_client"] = args.iperf_client
    IO_Running["fio_device"] = args.fio_device
    IO_Running["fio_engine"] = args.fio_engine
    IO_Running["sysinfo"] = args.sysinfo
    IO_Running["fio_simulation"] = "TRUE" if args.simulation_mode else "FALSE"
    IO_Running["iperf_additional_para_windows_size"] = args.iperf_additional_para_windows_size
    IO_Running["iperf_additional_para_buffer_size"] = args.iperf_additional_para_buffer_size

    if IO_Running["run_from_to"] is not "":
        from_to = IO_Running["run_from_to"].split("-")
        if len(from_to) != 2:
            print("Eror on run_from_to", IO_Running["run_from_to"])
            try:
                IO_Running["run_to"] = __ERROR_INT
                IO_Running["run_from"] = int(from_to[0])
            except:
                print("Eror on run_from_to", IO_Running["run_from_to"])
                exit(1)
        else:    
            try:
                IO_Running["run_from"] = int(from_to[0])
                IO_Running["run_to"] = int(from_to[1])
            except:
                print("Eror on run_from_to", IO_Running["run_from_to"])
                exit(1)
        
    IO_Running["multiple_default_devices"]=False 
    if not IO_Running["fio_device"] is None and  len(IO_Running["fio_device"].split(";")) > 1:
       IO_Running["multiple_default_devices"]=True 

    if IO_Running["test_case_generated_xls"] is not "" :
        IO_Running["case_generating"] = True
    if IO_Running["expand_mix_cases_xls"] is not "" :
        IO_Running["case_generating"] = True

    if args.fio_test_result_analyser:
        print("FIO test result analyser")
        c_l = Get_Cases_From_Xls(analyser=True)
        g_r = Group_Analyser(c_l)
        c_a_l = Fill_Analyse_2_Cases_List(c_l, g_r)
        output_fn = IO_Running["test_case_xls"] + "_analysing.xls"
        ndarray = np.array(c_a_l)   
        sheet_header = IO_Running["fio_header"] + fio_analyser["fio_result_append_items"]
        Save_ndarray_cases(sheet_header, ndarray, output_fn, "Fio_an", not_sort=True)
        print("\nResult is saved to ",output_fn,"\n")
        return
    
    Fio_Reload_Env_Settings()    
    Fio_Init(IO_Running)
    
    IO_Running["result_folder"] = IO_Running["work_space"] + "/_result/"
    c_l = Get_Cases_From_Xls()
    for case in c_l:
        if not IO_Running["case_generating"]:
            print(case)
    gc = Group_Cases(c_l)
    if IO_Running["test_case_generated_xls"] is not "" :
        print("Generating cases from", IO_Running["test_case_xls"], "to", IO_Running["test_case_generated_xls"] )
        Fio_Case_Generating(gc)
        return

    if IO_Running["expand_mix_cases_xls"] is not "":
        #Expand_Mix_Cases(gc)
        print("Generating cases from", IO_Running["test_case_xls"], "to", IO_Running["expand_mix_cases_xls"] )
        Fio_Case_Generating(gc,  seperate=False)
        return
        
    try:
        if IO_Running["with_iperf"]:
            Iperf_Init(ssh_ip = IO_Running["iperf_client"], result_folder = IO_Running["result_folder"], run_time = IO_Running["fio_runtime"])

        if IO_Running["run_single"] != 0 :
            g = Get_Single_Case_Of_Row(IO_Running["run_single"] , gc)
            if g is None:
                return
            ext=".json"
            if args.fio_output_json is not True:
                 IO_Running["fio_output"] = "TXT"
                 ext=".txt"
            print("Running case ", g)
            Fio_Reload_Env_Settings()
            Run_Grouped_Cases(gc[g])
            for c in gc[g]:
                fn = Get_Result_File_Name(c, ext)
                print("Saved to ", fn)
            return        
        cases_to_run = gc.keys()
        end_line_msg = "end" if IO_Running["run_to"] == __ERROR_INT else str(IO_Running["run_to"])        
        print("\n\nStart running cases from row", IO_Running["run_from"], "to", end_line_msg)
        if IO_Running["run_from"] != 0 :
            cases_to_run = Get_Single_Cases_from_Row(IO_Running["run_from"], gc, IO_Running["run_to"])
        if not args.parsing_only:
            for g  in cases_to_run:
                localtime = time.asctime( time.localtime(time.time()) )
                print("\n",localtime, "\tRunning case ", g, "\trow:", gc[g][0]["row"], "of", IO_Running["case_sheet"].nrows)
                Run_Grouped_Cases(gc[g])
        if IO_Running["fio_simulation"] == "TRUE":
            exit(0)
        print("\n\n")
        for g  in gc.keys():
            print("Parsing case ", g)
            Get_Group_Result(gc[g])
        output_fn = IO_Running["test_case_xls"] + "_reslut.xls"  if IO_Running["result_xls"] == "" else IO_Running["result_xls"]
        out_sheet_name = IO_Running["test_case_sheet"]   if IO_Running["output_sheet"]== "" else IO_Running["output_sheet"]
        IO_Running["case_write_wb"].get_sheet(IO_Running["case_sheet_id"]).name = out_sheet_name
        IO_Running["case_write_wb"].save(output_fn)
        print("\nResult is saved to ",output_fn,"sheet:", out_sheet_name,"\n")
        if IO_Running["with_iperf"]:
            Iperf_Close()
        exit(0)
    except KeyboardInterrupt:
        print("Interrupted!")
        exit(1)

    if IO_Running["sysinfo"]:
        Collect_Sys_Info()


if __name__ == '__main__':
    main()
        

    

