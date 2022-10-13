
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
import math

from Cmd import C_CMD, Q_Cmd, T_Q_CMD, __ERROR_FLOAT, __ERROR_INT, Q_Remote_Cmd, Tmux_CMD #, CMD_Group, Export_Env, 
from utils import Update_Result_2_Xls


"""
    - iperf insatallation
        apt install -y iperf3            
        ln -s /usr/bin/iperf3 /usr/bin/iperf
    - Pre-set up for server / client,  refer to nic_iperf_setup.sh:
            1. Set vf number by updating sriov_numvfs
            2, Set ip address for ecah vport with same subnet
     - Server side example:
        iperf -B 192.168.100.2 -s
     - Client side example:
        iperf -c 192.168.100.2  -B 192.168.100.1
    - case definition example in xls:
    title_iperf	        case	                                server_ip	                client_ip	                parallel	    report_interval	test_time	bi-direction
    iperf	        iperf_single_direction	192.168.100.101	    192.168.100.201	2			                                0



How to run:
    - set up vms in spr1 / spr2:
        vm_set_up_vm1_2_3.sh
        vm_set_up_spr2_vm1_2_3.sh
     "ssh_ip": "10.112.227.150",       
 "remote_iperf_server_reset": "/media/data/ml/storage_io/Storage/vm_reset_iperf_server_spr2_vm1_2_3.sh",        
"""



with_log = True
#with_log = False
def LogOut(s1="", s2="", s3="", s4="",s5="",s6="",s7="",s8="",s9="",s10=""):
    if with_log == False:
        return
    print(s1,s2,s3,s4,s5,s6,s7,s8,s9,s10)

IPerf_Running = {
    #"ssh_ip": "10.112.227.155",
    "ssh_ip": "10.112.227.150",
    #"ssh_ip": "192.168.122.61",
    "local_local_ips_cmd": {},
    "remote_local_ips_started": {},
    "report_interval": 10,
    "test_time":90,
    "parallel":2,
    "iperf_cmd":"/usr/bin/iperf",
    #"remote_iperf_server_reset": "/media/data/ml/storage_io/Storage/vm_reset_iperf_server_spr2_2.sh",
    #"remote_iperf_server_reset": "/media/data/ml/storage_io/Storage/vm_reset_iperf_server_spr2_vm1_2_3_4.sh",
    #"remote_iperf_server_reset": "/media/data/ml/storage_io/Storage/vm_reset_iperf_server_spr2_vm1_2_3.sh",
    #"remote_iperf_server_reset": "/media/data/ml/storage_io/Storage/vm_reset_iperf_server_spr2_vm1.sh",
    #"local_iperf_server_reset": "/media/data/ml/storage_io/Storage/vm_reset_iperf_server_spr1_vm1.sh",
    # "remote_iperf_server_reset": "/media/data/ml/storage_io/Storage/vm_reset_iperf_server_spr2_vm1_2.sh",
     #"remote_iperf_server_reset": "/media/data/ml/storage_io/Storage/vm_reset_iperf_server_spr2_vm1_2_4.sh",
      "remote_iperf_server_reset": "/media/data/ml/storage_io/Storage/vm_reset_iperf_server_spr2_vm1_2_3_4.sh",
    "local_iperf_server_reset": "/media/data/ml/storage_io/Storage/vm_reset_iperf_server_spr1_vm1_2.sh",
    "remote_iperf_client": "/media/data/ml/storage_io/Storage/vm_start_iperf_client.sh",
    #"remote_emon_cmd": "/media/data/ml/storage_io/Storage/server_emon.sh",
    "remote_emon_cmd": "",
    "local_power_monitor_cmds": ["sys_start_power_monitor.sh", "sys_stop_power_monitor.sh"],
    "remote_power_monitor_cmds": [],    
    #"pre_run_cmds": ["/media/data/bin/tmc_upload.sh"],
    "pre_run_cmds": [],
    "client_additional_name": "c6_disabled_spr1_",
    "server_additional_name": "c6_disabled_spr2_",
    "tmux_pre_run_cmds": [],
    "post_run_cmds": [],
    "result_folder":"",
    #"numactl_server":False, #
    #"numactl_server":True,
    #"numactl_client":True,
    "numactl_default":"",
    "case_test_time":1,
    "parsing_shutdown":1,
    "parsing_last_unit":3,
    "server_already_running": True,
    "wait_extend": 2,
    #"numactl_client":False,
    #"additional_client_para":"",
    "additional_client_para":" ",
    "additional_para":"",
    "additional_para_windows_size":"256k ",
    "additional_para_buffer_size":"64k ",
    
}
iperf_server_cmd_cfg = {
     "cmd": IPerf_Running["iperf_cmd"] 
}
iperf_client_cmd_cfg = {
     "cmd": IPerf_Running["iperf_cmd"] ,
     #"expected": ["sender", "receiver"]
     "expected": ["Gbits/sec"]
}
xls_iperf_keys_offset = {
}
IPerf_address_keyword = ["server_ip", "client_ip"]
IPerf_address_host_keyword = ["server_host", "client_host"]
Iperf_host_to_ip ={
                                "spr_2": "10.112.227.150",
                                "spr_1": "10.239.85.180",
                                "spr_1_vm_1": "192.168.124.61",
                                "spr_1_vm_2": "192.168.124.62",
                                "spr_1_vm_3": "192.168.124.63",
                                "spr_1_vm_4": "192.168.124.63",  # be careful on it
                                "spr_1_vm_5": "192.168.124.65",
                                "spr_1_vm_6": "192.168.124.66",
                                "spr_1_vm_7": "192.168.124.67",
                                "spr_2_vm_1": "192.168.124.61",
                                "spr_2_vm_2": "192.168.124.62",
                                "spr_2_vm_3": "192.168.124.63",
                                "spr_2_vm_4": "192.168.124.64",
                                "spr_2_vm_5": "192.168.124.65",
                                "spr_2_vm_6": "192.168.124.66",
                                "spr_2_vm_7": "192.168.124.67",                                
                                }
IPerf_Para = {
               #"work_type": "iperf",  #only for iperf type
               "case": 1,
               IPerf_address_keyword[0]: "",
               IPerf_address_keyword[1]: "",              
               "direction": "s_c",              
}
IPerf_Para_Optional = {
               "parallel": 2,
               "TCP_window_size": "",         
                "buffer_size":	 "",         
               "report_interval":	 10,         
              "test_time":	 60,  
               "client_numa_ctl": "NA",
               "server_numa_ctl": "NA",
}
#For result itemes in xls: sender_bw_1	recv_bw_1	retry_1
IPerf_Result_Items = {'average': "average_", 'last_3_interval': "last_3_interval_", 'last_6_interval': "last_6_interval_"}
#'average': 89.9, 'last_3_interval': 90.03333333333335, 'last_6_interval'

IPerf_Para_With_Space = [ "client_numa_ctl", "server_numa_ctl","additional_para"]

def Get_Additional_Paras(iperf_cmds, simple=False):
    #print(iperf_cmds[0].TCP_window_size)
    TCP_window_size = iperf_cmds.TCP_window_size if iperf_cmds.TCP_window_size != "NA" else IPerf_Running["additional_para_windows_size"]
    buffer_size = iperf_cmds.buffer_size if iperf_cmds.buffer_size != "NA" else IPerf_Running["additional_para_buffer_size"]
    #exit(1)
    if simple:
        #s = IPerf_Running["additional_para"] + IPerf_Running["additional_para_windows_size"] + " " + IPerf_Running["additional_para_buffer_size"] 
        s = IPerf_Running["additional_para"] + TCP_window_size + " " + buffer_size 
    else:
        #s = IPerf_Running["additional_para"] + " -w " + IPerf_Running["additional_para_windows_size"] + " -l  " + IPerf_Running["additional_para_buffer_size"] 
        s = IPerf_Running["additional_para"]
        if TCP_window_size != "":
            s = s + " -w " + TCP_window_size 
        if buffer_size != "":
            s = s + " -l  " + buffer_size 
    return s    
    
def New_Iperf_Case(xls_item, row, case_generating, row_offset, work_type,io_running):
    iperf_p = IPerf_Para.copy()
    keys_l = list(iperf_p.keys()) + list(IPerf_Para_Optional.keys())
    for key in  keys_l :
        v = xls_item[xls_iperf_keys_offset[key]]
        if v == "":
             # for mandatory paras
            if key in iperf_p.keys():
                print("Ignored the case with invalid definition(s): ", xls_item)
                io_running["case_write_sheet"].write(row, io_running["iperf_reult_key_index"], "Invalid_case")
                return None
            # for optional paras
            else:           
                v = "NA"
        if not case_generating  and key in IPerf_Para_With_Space:
            v = v.replace("\n", " ") 
            #v = v.replace(" ", "#") 
        else:
            if type(v) == type(1.0) and  math.isclose(v, float(int(v))): 
                v = str(int(v))
            if not case_generating and type(v) == type("string"): 
                v = v.replace("\n", "") 
                v = v.replace(" ", "")    
        if key is "case":
            #print(v)
            if type(v) == type(1.0) and v % 1 == 0.0: 
                v = str(int(v))

        #192.168.100.1@spr_1_vm_1
        for i in range(len(IPerf_address_keyword)):
            if key == IPerf_address_keyword[i]:
                if "@" in v:
                    rv = v.split("@")
                    #print(IPerf_address_host_keyword[i],key, rv)
                    #if not IPerf_address_host_keyword[i] in Iperf_host_to_ip.keys():
                    #    print("Error for host information in ", key, v )
                    #    exit(1)
                    iperf_p[IPerf_address_host_keyword[i]] = rv[1]#Iperf_host_to_ip[rv[1]]
                    v = rv[0]
                else:
                    iperf_p[IPerf_address_host_keyword[i]] = ""
        iperf_p[key] = v
    iperf_p["row"] =  row + 1 #+ row_offset
    iperf_p["work_type"] = work_type
    #print(iperf_p)
    return  iperf_p
    
def New_Iperf_Cmd(para):
#    print(para)
#    exit(1)
    bi_direction= True if para["direction"]=="both" else False
    try:
        t = int(para["test_time"])
    except:
        t = IPerf_Running["test_time"]
    report_interval = IPerf_Running["report_interval"]    
    if para["report_interval"] != "NA":
        try:
            report_interval = int(para["report_interval"])
        except:
            report_interval = IPerf_Running["report_interval"] 
    ci_ = C_IPerf(server_ip = para["server_ip"], client_ip = para["client_ip"], bi_direction=bi_direction, xls_row=para["row"], \
            test_time=t, parallel=para["parallel"], report_interval=report_interval, \
            server_host=para["server_host"], client_host=para["client_host"], \
            server_numa_ctl=para["server_numa_ctl"], client_numa_ctl=para["client_numa_ctl"], direction=para["direction"], \
            TCP_window_size=para["TCP_window_size"], buffer_size=para["buffer_size"])
    #ci = deepcopy(ci_)
    return ci_

def Iperf_Dump_Result(fn, result):
    jsObj = json.dumps(result)
    with open(fn, "w",encoding='utf-8') as f:
       f.write(jsObj)
       f.close()
       
def Iperf_Update_Result_2_Xls(xls_sheet, row, results):
    def update_result_(jr, ns):
        if jr is None:
            return
        for k in jr.keys():
            re_item = IPerf_Result_Items[k] + ns
            if re_item in xls_iperf_keys_offset.keys():
                re_itme_colume = xls_iperf_keys_offset[re_item]
                Update_Result_2_Xls(xls_sheet, row, re_itme_colume, jr[k])
    if results is None:
        return
    print(results)
    update_result_(results["1"], "1")
    update_result_(results["2"], "2")
    LogOut("Iperf_Update_Result_2_Xls " + str(results))
    
    if results["1"]  is None or results["2"]  is None :
        return
    return
    bw_1 = float(results["1"]["sender"]) if results["local_client"] is not None else float(0.0)
    bw_2 = float(results["remote_client"]["sender"]) if results["remote_client"] is not None else float(0.0)
    bw = bw_1 + bw_2
    
    both_bw_c = xls_iperf_keys_offset["both_bw"]
    Update_Result_2_Xls(xls_sheet, row, both_bw_c, bw)

    retry_1 = float(results["local_client"]["Retr"]) if results["local_client"] is not None else float(0.0)
    retry_2 = float(results["remote_client"]["Retr"]) if results["remote_client"] is not None else float(0.0)
    retry = retry_1 + retry_2

    both_retry_c = xls_iperf_keys_offset["both_retry"]
    Update_Result_2_Xls(xls_sheet, row, both_retry_c, retry)

def Iperf_Parsing_Result(file_name, direction="s_c"):
    def parsing_single_direction(fn):
        sum_s_cmd  = "cat " + fn + " | grep [SUM]  "
        sum_s = Q_Cmd(sum_s_cmd)
        print(fn, sum_s, len(sum_s))
        sum_l = sum_s.split("\n")
        results = []
        for s in sum_l:
            if len(s.strip()) > 1:
                s_items = s.split()
                if len(s_items) > 5:
                    try:
                        bw = float(s_items[5])
                        bw_s = [s_items[1], bw]
                        results.append(bw_s)
                    except:
                        print("error, ", s)
        total = len(results)
        _r = {"1": None, "2": None}
        v_2nd_unit_mean = ""
        v_1st_unit_mean = ""
        if total == 0:
            _r = {"average":"", "last_3_interval":"", "last_6_interval":""}
            return _r
        
        if total >  IPerf_Running["parsing_shutdown"] + IPerf_Running["parsing_last_unit"] + 1:
            v_1st = []
            print(total)
            for i in range(IPerf_Running["parsing_last_unit"]):
                v_1st.append(results[total -1 - i - IPerf_Running["parsing_shutdown"]][1])
            v_1st_unit_mean =  np.mean(v_1st)
            print(v_1st, v_1st_unit_mean)

        if total >  IPerf_Running["parsing_shutdown"] + IPerf_Running["parsing_last_unit"] * 2:
            v_2nd = []
            for i in range(IPerf_Running["parsing_last_unit"] * 2):
                v_2nd.append(results[total -1 - i - IPerf_Running["parsing_shutdown"]][1])
            v_2nd_unit_mean =  np.mean(v_2nd)
            print(v_2nd, v_2nd_unit_mean)

            
        _r = {"average":results[-1][1], 
                    "last_3_interval":v_1st_unit_mean, 
                    "last_6_interval":v_2nd_unit_mean}
        
        return _r
    re = {"1":{}, "2":{}}
    if direction == "s_c":
        result_file = file_name.strip()[:-4] + "txt"
        LogOut("Iperf_Parsing_Result", result_file, direction)
        re["1"] = parsing_single_direction(result_file)
    elif direction == "c_s":
        result_file = file_name.strip()[:-5] + "_2nd.txt"
        LogOut("Iperf_Parsing_Result", result_file, direction)
        re["2"] = parsing_single_direction(result_file)
    elif direction == "both":
        result_file = file_name.strip()[:-4] + "txt"
        re["1"] = parsing_single_direction(result_file)
        result_file_2 = file_name.strip()[:-5] + "_2nd.txt"
        re["2"] = parsing_single_direction(result_file_2)
        LogOut("Iperf_Parsing_Result", result_file, result_file_2, direction)
    return re
    
def Iperf_Parser_Json_Result(file_name):
    try:
        json_data = open(file_name)
    except:
        print("Error on opening ", file_name)
        return None        
    try:
        data = json.load(json_data)
        return data
    except:
        print("Error on processing ", file_name)
        return None

def Start_Iperf_Cmds(iperf_cmds, additional_para_windows_size="", additional_para_buffer_size=""):
    if len(iperf_cmds) == 0:
        return
    offset = 0

    if additional_para_windows_size != "":
        IPerf_Running["additional_para_windows_size"] = additional_para_windows_size
    if additional_para_buffer_size != "":
        IPerf_Running["additional_para_buffer_size"] = additional_para_buffer_size
    
    IPerf_Running["case_test_time"] = iperf_cmds[0].test_time

    #print("Start_Iperf_Cmds ...")
    if iperf_cmds[0].direction == "both":
        if IPerf_Running["remote_iperf_server_reset"] != "":
            remote_command_s = IPerf_Running["remote_iperf_server_reset"] + " " + Get_Additional_Paras(iperf_cmds[0], simple=True)
            print(remote_command_s)
            Q_Remote_Cmd(Iperf_host_to_ip["spr_2"], remote_command_s)     
        if IPerf_Running["local_iperf_server_reset"] != "":
            remote_command_s = IPerf_Running["local_iperf_server_reset"] + " " + Get_Additional_Paras(iperf_cmds[0], simple=True)
            print(remote_command_s)
            Q_Remote_Cmd(Iperf_host_to_ip["spr_1"], remote_command_s)           
    elif iperf_cmds[0].direction == "s_c":
        if IPerf_Running["remote_iperf_server_reset"] != "":
            remote_command_s = IPerf_Running["remote_iperf_server_reset"] + " " + Get_Additional_Paras(iperf_cmds[0], simple=True)
            print(remote_command_s)
            Q_Remote_Cmd(Iperf_host_to_ip["spr_2"], remote_command_s)        
    elif iperf_cmds[0].direction == "c_s":
        if IPerf_Running["local_iperf_server_reset"] != "":
            remote_command_s = IPerf_Running["local_iperf_server_reset"] + " " + Get_Additional_Paras(iperf_cmds[0], simple=True)
            print(remote_command_s)
            Q_Remote_Cmd(Iperf_host_to_ip["spr_1"], remote_command_s)        
        
        #time.sleep(5)
    pre_id = 0
    for pre_cmd in IPerf_Running["pre_run_cmds"] :
        pre_name = "pre_tmux_" + str(pre_id)
        cmd_s = pre_cmd + " " + IPerf_Running["client_additional_name"] + "_row_" + str(iperf_cmds[0]. xls_row) + " " + str(IPerf_Running["case_test_time"] - 5)
        tx = Tmux_CMD(pre_name,auto_delete=False)
        #IPerf_Running["tmux_pre_run_cmds".append(tx)
        r = tx.exe_remote_cmd(cmd_s)
        LogOut(r)
        pre_id += 1
        
    if IPerf_Running["remote_emon_cmd"] != "":
        server_pre_name = "pre_tmux_" + str(pre_id)
        cmd_s =  IPerf_Running["remote_emon_cmd"] + " " + IPerf_Running["server_additional_name"] + "_row_" + str(iperf_cmds[0]. xls_row) + " " + str(IPerf_Running["case_test_time"] - 5)
        tx_s = Q_Remote_Cmd(Iperf_host_to_ip["spr_2"], cmd_s)

    if len(IPerf_Running["local_power_monitor_cmds"]) != 0:
        if IPerf_Running["local_power_monitor_cmds"][0] != "":
            #power_monitor_log_file = IPerf_Running["result_folder"]  + "row_" + str(iperf_cmds[0]. xls_row) + "_rapl.log"
            power_monitor_log_file = iperf_cmds[0].log_file_name + "_rapl.log"
            print("Starting local_power_monitoring, saving to", power_monitor_log_file)
            r = Q_Cmd(IPerf_Running["local_power_monitor_cmds"][0] + " " + power_monitor_log_file)
            #print(r)
        #server_pre_name = "pre_tmux_" + str(pre_id)
        #cmd_s =  IPerf_Running["remote_emon_cmd"] + " " + IPerf_Running["server_additional_name"] + "_row_" + str(iperf_cmds[0]. xls_row) + " " + str(IPerf_Running["case_test_time"] - 5)
        #tx_s = Q_Remote_Cmd(Iperf_host_to_ip["spr_2"], cmd_s)

    time.sleep(5)
    for iperf in iperf_cmds:
        if iperf.direction == "both":
            iperf.iperf_start_1st_direction_v2(offset)
            iperf.iperf_start_2nd_direction_v2(offset)
            #time.sleep(iperf.test_time + 5)
            #iperf.iperf_stop_2nd_direction_v2(offset)
        elif iperf.direction == "s_c":
            #iperf.iperf_start_1st_direction_v2(offset)
            #time.sleep(iperf.test_time + 5)
            iperf.iperf_start_1st_direction_v2(offset)
        elif iperf.direction == "c_s":
            #iperf.iperf_start_1st_direction_v2(offset)
            #time.sleep(iperf.test_time + 5)
            iperf.iperf_start_2nd_direction_v2(offset)
        offset += 1


    localtime = time.asctime( time.localtime(time.time()) )
    print("     \t==>Iperf case started at", localtime)

        
def Wait_Iperf_Cmds_Done(iperf_cmds):
    if len(iperf_cmds) == 0:
        return
    offset = 0
    time.sleep(IPerf_Running["case_test_time"] + IPerf_Running["wait_extend"] + 5)

    for iperf in iperf_cmds:
        if iperf.direction == "both":
            iperf.iperf_stop_1st_direction_v2(offset)
            iperf.iperf_stop_2nd_direction_v2(offset)
        elif iperf.direction == "s_c":
            iperf.iperf_stop_1st_direction_v2(offset)
        elif iperf.direction == "c_s":
            iperf.iperf_stop_2nd_direction_v2(offset)
        offset += 1
    #time.sleep(IPerf_Running["case_test_time"] + IPerf_Running["wait_extend"])
    if len(IPerf_Running["local_power_monitor_cmds"]) > 1:
        print("Stopping local_power_monitoring")    
        if IPerf_Running["local_power_monitor_cmds"][1] != "":
            r = Q_Cmd(IPerf_Running["local_power_monitor_cmds"][1])
            #print(r)
    time.sleep(IPerf_Running["wait_extend"])
    localtime = time.asctime( time.localtime(time.time()) )
    print("     \t==>Iperf case done at", localtime)
    time.sleep(5)

class C_IPerf():
    def __init__(self, server_ip, client_ip, test_time=IPerf_Running["test_time"], parallel=IPerf_Running["parallel"], \
                bi_direction=True, xls_row=-1, report_interval=-1, server_host="",client_host="", \
                server_numa_ctl="NA", client_numa_ctl="NA", direction="s_c", TCP_window_size="", buffer_size=""):      
        self.server_ip = server_ip
        self.client_ip = client_ip
        self.ssh_ip = ""
        self.server_host=server_host
        self.client_host=client_host
        self.server = None
        self.client = None
        self.bi_server = None
        self.bi_client = None
        self.server_numa_ctl = server_numa_ctl
        self.client_numa_ctl = client_numa_ctl
        
        self.test_time = test_time
        self.report_interval= IPerf_Running["report_interval"] if report_interval == -1 else report_interval
        self.parallel = parallel
        self.ipv6 = True if ":" in self.server_ip else False
        self.s_cmd = None #for server cmd
        self.c_cmd = None #for client cmd
        self.remote_client = None
        self.log_file = None
        self.bi_direction = bi_direction
        self.direction = direction
        self.TCP_window_size = TCP_window_size
        self.buffer_size = buffer_size
        self.start_time = None
        self.end = None
        self.log_file_name = ""
        self.log_file_tmp_name = ""
        self.bi_log_file_tmp_name = ""
        self.log_file = None
        self.result_json_file = None
        self.xls_row = xls_row
        if xls_row > 0:
            self.log_file_name = IPerf_Running["result_folder"] + "row_" + str(xls_row)
    def __del__(self):
        pass
        #if self.server_ip in IPerf_Running["remote_local_ips_started"].keys():
        #    self.stop_remote_server()

    #for local server, remote client
    def start_local_server(self, offset = 0):
        if self.s_cmd is None:
            self.s_cmd = C_CMD(iperf_server_cmd_cfg, block_mode=False,sys_cmd=True,bash_added=True)
            s_para = "-B " +  self.local_ip + " -s" + " -i " + str(self.report_interval)
            self.s_cmd.cmd_exe(paras=s_para, print_expected=with_log)
            IPerf_Running["local_local_ips_cmd"][self.local_ip] = self.s_cmd
            #time.sleep(1)
        return self.s_cmd
    def dump_result(self, result):
        LogOut(result)
        if self.log_file_name is not "":
            json_file = self.log_file_name + ".json"
            Iperf_Dump_Result(json_file, result)
            
    def stop_local_server(self):
        if self.s_cmd is not None:
            self.s_cmd.stop()
            print("iperf server", self.local_ip, "is stopped.")
            del IPerf_Running["local_local_ips_cmd"][self.local_ip]
    def run_remote_client(self, block=True):
        iperf_client_para_s = " -t " + str(self.test_time) + " -P " + str(self.parallel) + " -i " + str(self.report_interval) 
        iperf_client_para_s += " -fg" # for Gbits/sec
        iperf_client_para_s += " -V" if self.ipv6 else ""
        c_cmd_s ="ssh "+ self.ssh_ip + ' "' +  iperf_client_cmd_cfg["cmd"] + " -c " + self.local_ip + " -B " + self.remote_ip + iperf_client_para_s + ' "' 
        LogOut(c_cmd_s)
        q = T_Q_CMD(c_cmd_s, expected = iperf_client_cmd_cfg["expected"], show_all=True)
        self.remote_client = q
        if block:
            result=q.wait_till_finish()
            return result
        return None

    def run_remote_client_w(self, block=True):
        iperf_client_para_s = " -t " + str(self.test_time) + " -P " + str(self.parallel) + " -i " + str(self.report_interval) 
        iperf_client_para_s += " -fg" # for Gbits/sec
        iperf_client_para_s += " -V" if self.ipv6 else ""
        c_cmd_s ="ssh "+ self.ssh_ip + ' "' +  iperf_client_cmd_cfg["cmd"] + " -c " + self.local_ip + " -B " + self.remote_ip + iperf_client_para_s + ' "' 
        #LogOut(c_cmd_s)
        print(c_cmd_s)
        q = Q_Remote_Cmd(c_cmd_s, expected = iperf_client_cmd_cfg["expected"], show_all=True)
        self.remote_client = q
        if block:
            result=q.wait_till_finish()
            return result
        return None


    def get_remote_client_result(self):
        if self.remote_client is None:
            print("Error in get_remote_client_result")
        return self.remote_client.wait_till_finish()
        
    def iperf_exe_remote_client_block(self, exit_server_when_done=False):
        if self.local_ip not in IPerf_Running["local_local_ips_cmd"].keys():
            s_cmd = self.start_local_server()
            
        r = self.run_remote_client()
        if exit_server_when_done:
            self.stop_local_server()    
        #print(r)
        parsed_r = self.parsing_result(r)
        print(parsed_r)

    #for local client, remote server
    def start_remote_server(self, offset = 0):
        #LogOut("start_remote_server")
        if self.remote_ip in IPerf_Running["remote_local_ips_started"].keys():
        #    LogOut("Remote server has already been started. No need to run again.")
        #    return
            self.stop_remote_server()
        session_name =  self.remote_ip.replace(".", "_") if not self.ipv6 else self.remote_ip.replace(":", "_")
        #print(session_name)
        if IPerf_Running["numactl_server"]:
            numactl_s = Get_Numactl_Infor("", 1, offset, Local = False)
        else:
            numactl_s = ""
        iperf_cmd_s =  numactl_s + IPerf_Running["iperf_cmd"] + " -B " + self.remote_ip + " -s" + " -i " + str(self.report_interval)  
            
        r_s = "tmux new-session -d -s " + session_name + ' "' + iperf_cmd_s + '"' 
        #LogOut(self.ssh_ip + " " + r_s)
        print(self.ssh_ip + " " + r_s)
        Q_Remote_Cmd(self.ssh_ip, r_s)
        #LogOut("====>remote_server started " + r_s)
        IPerf_Running["remote_local_ips_started"][self.remote_ip] = True
        
    def stop_remote_server(self):
        Stop_remote_iperf_server(self.ssh_ip, self.remote_ip)

    def run_local_client(self, block=True, offset = 0):
        iperf_client_para_s = " -t " + str(self.test_time) + " -P " + str(self.parallel) + " -i " + str(self.report_interval) 
        iperf_client_para_s += " -fg" # for Gbits/sec
        if "additional_client_para" in IPerf_Running.keys() and IPerf_Running["additional_client_para"].strip() != "":
            iperf_client_para_s += " " + IPerf_Running["additional_client_para"].strip()
        iperf_client_para_s = iperf_client_para_s + Get_Additional_Paras(self, simple=False)
        iperf_client_para_s += " -V" if self.ipv6 else ""
        iperf_client_para_s =  " -c " + self.remote_ip + " -B " + self.local_ip + iperf_client_para_s 
        if IPerf_Running["numactl_client"]:
            #print("run_local_client: ", offset)
            numactl_s = Get_Numactl_Infor("", 0, offset, Local = True)
        else:
            numactl_s = ""
            
        if block:
            cmd_s =  numactl_s + iperf_client_cmd_cfg["cmd"] + iperf_client_para_s
            LogOut("run_local_client:" + cmd_s)
            r = Q_Cmd(cmd_s)
            return r
        else:
            if IPerf_Running["numactl_client"]:
                local_client_cmd = {"cmd": numactl_s.split(" ")[0]  ,"expected": iperf_client_cmd_cfg["expected"]}
                iperf_client_para_s = numactl_s[len(numactl_s.split(" ")[0]) :].strip() + " " + IPerf_Running["iperf_cmd"] + iperf_client_para_s
            else:
                local_client_cmd = {"cmd":  IPerf_Running["iperf_cmd"] ,"expected": iperf_client_cmd_cfg["expected"]}
                
            self.c_cmd = C_CMD(local_client_cmd, block_mode=False,sys_cmd=True,bash_added=False)
            LogOut("run_local_client noblock:" + iperf_client_para_s)
            #print("local_client_cmd:", local_client_cmd)
            self.c_cmd.cmd_exe(paras=iperf_client_para_s, print_expected=with_log)
            return None
    def get_local_client_result(self):
        if self.c_cmd is None:
           return None
        _, r = self.c_cmd.check_output(print_expected=with_log)
        return r
    def iperf_exe_local_client_block(self, exit_server_when_done=False):
        self.start_remote_server()
        r = self.run_local_client(block=True)
        print(r)
        self.stop_remote_server()
        
    def iperf_exe_local_client_no_block(self, exit_server_when_done=False):
        self.start_remote_server()
        self.run_local_client(block=False)
        r = self.get_local_client_result()
        pr = self.parsing_result(r)
        print(pr)
        if exit_server_when_done:
            self.stop_remote_server()    
    def get_client_result(self, first=True, offset=0):
        #client_host_ip = self.get_host_ip(self.client_host)  if first else self.get_host_ip(self.server_host)
        client_host_ip = self.get_host_ip(self.client_host)  if first else self.get_host_ip("spr_2")
        if client_host_ip != "":
            log_tmp = self.log_file_tmp_name if first else "/tmp/" +  self.log_file_name.split("/")[-1] +  "_2nd.txt"
            log_file = self.log_file_name if first else self.log_file_name + "_2nd"
            result_scp = "scp -r " + client_host_ip + ":" +log_tmp + " " + log_file + ".txt"
            r = Q_Cmd(result_scp)
            LogOut(result_scp,r)
        
    def start_client_V2(self, block=True, offset = 0, first=True):
        client_host_ip = self.get_host_ip(self.client_host)  if first else self.get_host_ip(self.server_host)
        server_ip = self.server_ip if first else self.client_ip
        client_ip = self.client_ip if first else self.server_ip

        LogOut("start_client_V2",self.server_host, client_host_ip)
        iperf_client_para_s = " -t " + str(IPerf_Running["case_test_time"]) + " -P " + str(self.parallel) + " -i " + str(IPerf_Running["report_interval"]) 
        iperf_client_para_s += " -fg" # for Gbits/sec
        session_name =  "ip_c_" + client_ip.replace(".", "_") if not self.ipv6 else client_ip.replace(":", "_")

        if "additional_client_para" in IPerf_Running.keys() and IPerf_Running["additional_client_para"].strip() != "":
            iperf_client_para_s += " " + IPerf_Running["additional_client_para"].strip()
        iperf_client_para_s = iperf_client_para_s + Get_Additional_Paras(self, simple=False)
        iperf_client_para_s += " -V" if self.ipv6 else ""
        iperf_client_para_s =  " -c " + server_ip + " -B " + client_ip + iperf_client_para_s 

        numactl_s = self.Get_Numactl_Infor(server=False, first=first)
        if first:
            self.log_file_tmp_name = "/tmp/" + session_name + "_log.txt" if client_host_ip != "" else self.log_file_name
        else:
            self.bi_log_file_tmp_name =  "/tmp/" +  self.log_file_name +  "_2nd.txt"
        r_log = self.log_file_tmp_name if first else self.bi_log_file_tmp_name + "_2nd_" +str(offset)
        
        iperf_cmd_s =  numactl_s + " " + IPerf_Running["iperf_cmd"] +iperf_client_para_s + " |& tee " + r_log 
        if first:
            self.client = Tmux_CMD(session_name, ssh_ip=client_host_ip,auto_delete=False,silent_mode=True)
            c = self.client
            LogOut(first, client_host_ip, iperf_cmd_s)
            print("==============>start_client_V2", iperf_cmd_s)
            r = c.exe_remote_cmd(iperf_cmd_s)
            LogOut(r)
        else:
            self.bi_client = Tmux_CMD(session_name, ssh_ip=Iperf_host_to_ip["spr_2"],auto_delete=False,silent_mode=True)
            c = self.bi_client
            # vm_ip server_ip client_ip test_time P logfile windows buffer
            windows_s=iperf_client_para_s.split("-w")[1].strip().split(" ")[0]
            buffer_s=iperf_client_para_s.split("-l")[1].strip().split(" ")[0]
            log_file_name=  "/tmp/" +  self.log_file_name.split("/")[-1] +  "_2nd.txt"
            para_s = client_host_ip + " " + server_ip + " " + client_ip + " "  + str(IPerf_Running["case_test_time"]) + " "+ str(self.parallel) + " " + \
                    log_file_name  + " "  + windows_s + " " + buffer_s + " " + str(offset)
            print("para_s, ", para_s, "iperf_client_para_s ", iperf_client_para_s, "w ", windows_s, "b ", buffer_s)
            
            iperf_cmd_s=IPerf_Running["remote_iperf_client"] + " " + para_s 
            LogOut(first, client_host_ip, iperf_cmd_s)
            r = c.exe_remote_cmd(iperf_cmd_s)
            LogOut(r)
            
        
        return

    def Get_Numactl_Infor(self, server, first=True):
        numa_setting = self.server_numa_ctl
        if first and not server:
            numa_setting = self.client_numa_ctl
        if  server and not first:
            numa_setting = self.client_numa_ctl
        numa_ctl = IPerf_Running["numactl_default"] if numa_setting == "NA" else numa_setting
        return numa_ctl
            

    def get_host_ip(self, host):
        if host == "":
            return ""
        print("get_host_ip ", host)
        if not host in Iperf_host_to_ip.keys():
            print("Error for host information in ", host,  Iperf_host_to_ip)
            exit(1)
        return Iperf_host_to_ip[host]

    def start_server_V2(self, offset = 0, first=True):
        
        server_host_ip = self.get_host_ip(self.server_host) if first else self.get_host_ip(self.client_host)
        server_ip = self.server_ip if first else self.client_ip
        LogOut("start_server_V2", server_host_ip, server_ip)
        session_name =  "ip_s_" + server_ip.replace(".", "_") if not self.ipv6 else server_ip.replace(":", "_")
        numactl_s = self.Get_Numactl_Infor(server=True, first=first)
        iperf_cmd_s =  numactl_s + " " + IPerf_Running["iperf_cmd"] + " -B " + server_ip + " -s" + " -i " + str(self.report_interval)  
        LogOut(first, server_host_ip, iperf_cmd_s)
        if first:
            self.server = Tmux_CMD(session_name, ssh_ip=server_host_ip,auto_delete=False,silent_mode= not with_log)
            s = self.server
        else:
            self.bi_server = Tmux_CMD(session_name, ssh_ip=server_host_ip,auto_delete=False,silent_mode= not with_log)
            s = self.bi_server
        s.exe_remote_cmd(iperf_cmd_s)
        return

    def iperf_start_1st_direction_v2(self, offset = 0):
        #LogOut("iperf_start_1st_direction_v2", self.server_host)
        if not IPerf_Running["server_already_running"] :
            if type(self.server_host) != type(None) and not "STARTED" in self.server_host.upper():
                self.start_server_V2(offset)
        self.start_client_V2(block=False,  offset=offset)

    def iperf_stop_1st_direction_v2(self, offset = 0):
        #LogOut("iperf_stop_1st_direction_v2", self.server_host)
        if not IPerf_Running["server_already_running"]:  
            if type(self.server_host) != type(None) and not "STARTED" in self.server_host.upper():
                self.server.send_Ctrl_C_stop()
        self.get_client_result(offset=offset)
        self.client.send_Ctrl_C_stop()

    def iperf_start_2nd_direction_v2(self, offset = 0):
        #LogOut("iperf_start_2nd_direction_v2")
        #self.start_server_V2(offset,  first=False)
        #self.start_client_V2(block=False,  offset=offset,first=False)
        #LogOut("iperf_start_2nd_direction_v2", self.server_host)
        #if not IPerf_Running["server_already_running"] :
        #    if type(self.server_host) != type(None) and not "STARTED" in self.server_host.upper():
        #        self.start_server_V2(offset)
        self.start_client_V2(block=False,  offset=offset,first=False)   

    def iperf_stop_2nd_direction_v2(self, offset = 0):
        #LogOut("iperf_stop_2nd_direction_v2")
        #self.bi_server.send_Ctrl_C_stop()
        self.get_client_result(first=False)
        self.bi_client.send_Ctrl_C_stop()

    def iperf_start_one_direction_no_block(self, offset = 0):
        self.start_remote_server(offset)
        self.run_local_client(block=False,  offset=offset)
        
    def iperf_wait_one_direction_done(self,  exit_server_when_done=True):
        r = self.get_local_client_result()
        p_result_local = self.parsing_result(r)
        full_result = {"local_client": p_result_local, "remote_client":None}
        self.dump_result(full_result)

        if exit_server_when_done:
            self.stop_remote_server()    

        
    def iperf_start_bi_direction_no_block(self, offset = 0):
        #LogOut("iperf_start_bi_direction_no_block")
        self.start_remote_server(offset)
        self.run_local_client(block=False)
        exit(1)
        self.start_local_server(offset)
        self.run_remote_client(block=False)   
            
    def iperf_wait_bi_direction_done(self,  exit_server_when_done=True):
        result_local = self.get_local_client_result()
        p_result_local = self.parsing_result(result_local)
        localtime = time.asctime( time.localtime(time.time()) )
        print("         \t ======>local_client:",p_result_local, "\t", localtime)

        result_remote = self.get_remote_client_result()
        p_result_remote = self.parsing_result(result_remote)
        localtime = time.asctime( time.localtime(time.time()) )
        print("         \t ======>remote_client:",p_result_remote, "\t", localtime)
        full_result = {"local_client": p_result_local, "remote_client":p_result_remote}
        self.dump_result(full_result)
        
        if exit_server_when_done:
            self.stop_remote_server()    
            self.stop_local_server()    
            
    def iperf_exe_bi_direction_no_block(self, exit_server_when_done=False):
        self.iperf_start_bi_direction_no_block()
        self.iperf_wait_bi_direction_done(exit_server_when_done=exit_server_when_done)
        
    #parsing iperf output      
    def parsing_result(self, result):
        #example:
        #'[  3]  0.0- 5.0 sec  18.0 GBytes  30.9 Gbits/sec'
        #'[  3]  0.0- 5.0 sec  24.1 GBytes  41.4 Gbits/sec',
        #'[  4]  0.0- 5.0 sec  20.1 GBytes  34.5 Gbits/sec', 
        #'[SUM]  0.0- 5.0 sec  44.2 GBytes  75.9 Gbits/sec']

        return
        
        parsed_r = {}
        new_r = []
        sum_not_found = True
        for line in result:
            if "SUM" in line:
                new_r.append(line)
                sum_not_found = False
                result=new_r
            
        if sum_not_found:
            result=result[len(result) -1]
            throughput = result.split(" ")[-2]
            print(throughput, "Gbits/sec   ", result)
            parsed_r = {"sender":throughput, "receiver":throughput, "Retr":0}
            return parsed_r
            
        r_ = result[len(result) - 1].split(" ")
        if len(r_) > 2:
            throughput = r_[-2]
            parsed_r = {"sender":throughput, "receiver":throughput, "Retr":0}
        else:
            parsed_r = {"sender":0.0, "receiver":0.0, "Retr":0}
        print(throughput, "Gbits/sec   ", result)
        return parsed_r

        
        exit(1)
        if len(result) < 2:
            parsed_r = {"sender":0.0, "receiver":0.0, "Retr":0}
            print("Error on parsing iperf result.", result)
            return parsed_r
        for line in result:
            for e in iperf_client_cmd_cfg["expected"]:
                if e in line:
                    sl = line.split()
                    try:
                        bd_p = len(sl) - 3
                        if "Gbits/sec" in sl[len(sl) - 3]:
                            bd_p = len(sl) - 4
                            try:
                                parsed_r["Retr"] = int(sl[len(sl) - 2])
                            except:
                                parsed_r["Retr"] = __ERROR_INT
                        Bandwidth_=sl[bd_p]
                        try:
                            Bandwidth = float(Bandwidth_)
                        except:
                            Bandwidth = __ERROR_FLOAT
                        parsed_r[e] = Bandwidth
                    except:
                        parsed_r = {"sender":0.0, "receiver":0.0, "Retr":0}
                        print("Error on parsing iperf result.", result)
                        print("Error on parsing iperf result. line:", line)
                    
        return parsed_r
        
# kill iperf server in local side
def Stop_local_iperf_servers():
    for local_ip in IPerf_Running["local_local_ips_cmd"].keys():
        IPerf_Running["local_local_ips_cmd"][local_ip].stop()
        del IPerf_Running["local_local_ips_cmd"][local_ip]

# kill iperf server inside tmux in remote side
def Stop_remote_iperf_server(ssh_ip, ip_address):
    ipv6 = True if ":" in ip_address else False
    session_name =  ip_address.replace(".", "_") if not ipv6 else ip_address.replace(":", "_")
    r_s = "tmux kill-session -t " + session_name 
    Q_Remote_Cmd(ssh_ip, r_s)
    if ip_address in IPerf_Running["remote_local_ips_started"].keys():
        del  IPerf_Running["remote_local_ips_started"][ip_address]

        
def Stop_remote_Iperf_servers():
    for local_ip in IPerf_Running["remote_local_ips_started"].keys():
        Stop_remote_iperf_server(local_ip)

# Check iperf cmd and remote server 
def Iperf_Init(ssh_ip, result_folder, run_time):
    LogOut("Iperf_Init")
    IPerf_Running["ssh_ip"] = ssh_ip
    IPerf_Running["result_folder"] = result_folder
    IPerf_Running["test_time"] = run_time
    #result_f = Path(IPerf_Running["result_folder"])    
    result_f_s = "mkdir -p " + IPerf_Running["result_folder"]
    Q_Cmd(result_f_s)
    cmd_file = Path(IPerf_Running["iperf_cmd"])    
    if cmd_file.exists() is not True:       
        print("Error: ", IPerf_Running["iperf_cmd"], "does not exist")
        exit()
    if 0:
        q_c = "ssh " + ssh_ip + " ' ls -lh " + IPerf_Running["iperf_cmd"] + "'" + " |&  tee  /tmp/tmp.txt "
        LogOut("Iperf_Init " + q_c)
        r = Q_Cmd(q_c)
        if "No such file or directory" in r:
            print("Error! in ", ssh_ip, r)
            exit(1)
    if 0: #clean up existing iperf instance
        clean_iperf_s="ps aux | grep iperf | awk '{print $2}' |xargs kill  > /dev/null"
        LogOut("Iperf_Init " + clean_iperf_s)
        Q_Cmd(clean_iperf_s)
        LogOut("Iperf_Init remote " + clean_iperf_s)
        Q_Remote_Cmd(ssh_ip, clean_iperf_s)
        session_s="ps aux | grep tmux | awk '{print $2}' |xargs kill"
        session_s="tmux kill-session"
        Q_Remote_Cmd(ssh_ip, session_s)
    LogOut("Iperf_Init done")

# Stop the tmux iperf server in the remote side    
def Iperf_Close():
    Stop_remote_Iperf_servers()

# For debug       
def Iperf_Try():
    LogOut("Iperf_Try")
    iperf_try = C_IPerf(local_ip="192.168.100.101", remote_ip="192.168.100.201")
    #iperf_try.iperf_exe_remote_client_block(exit_server_when_done=True)
    #iperf_try.iperf_exe()
    #iperf_try.iperf_exe_local_client_block(exit_server_when_done=True)
    #iperf_try.iperf_exe_local_client_no_block(exit_server_when_done=True)
    #iperf_try.iperf_exe_bi_direction_no_block(exit_server_when_done=True)
    iperf_try.iperf_exe_bi_direction_no_block(exit_server_when_done=True)
    
if __name__ == '__main__':
    Iperf_Try()
        


