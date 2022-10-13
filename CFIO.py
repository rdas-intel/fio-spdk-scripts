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
import FioResultDecoder
from dateutil.parser import parse
from Cmd import C_CMD, CMD_Group, Export_Env, Q_Cmd,  Q_Cmd_Ext
from utils import Inside_container

'''
      
        Available metrics of fio result for fio3-3:
        'jobname', 'groupid', 'error', 'eta', 'elapsed', 
        'read_io_bytes', 'read_io_kbytes', 'read_bw_bytes', 'read_bw', 'read_iops', 'read_runtime', 'read_total_ios', 'read_short_ios', 'read_drop_ios',
        'read_clat_ns_min', 'read_clat_ns_max', 'read_clat_ns_mean', 'read_clat_ns_stddev', 
        'read_clat_ns_p1', 'read_clat_ns_p5', 'read_clat_ns_p10', 'read_clat_ns_p20', 'read_clat_ns_p30', 'read_clat_ns_p40', 'read_clat_ns_p50', 
        'read_clat_ns_p60', 'read_clat_ns_p70', 'read_clat_ns_p80', 'read_clat_ns_p90', 'read_clat_ns_p95', 'read_clat_ns_p99', 'read_clat_ns_p99.5', 'read_clat_ns_p99.9', 'read_clat_ns_p99.95', 'read_clat_ns_p99.99', 
        'read_clat_ns_p0', 'read_lat_ns_min', 'read_lat_ns_max', 'read_lat_ns_mean', 'read_lat_ns_stddev', 
        'read_bw_min', 'read_bw_max', 'read_bw_agg', 'read_bw_mean', 'read_bw_dev', 'read_bw_samples',
        'read_iops_min', 'read_iops_max', 'read_iops_mean', 'read_iops_stddev', 'read_iops_samples', 'write_io_bytes', 'write_io_kbytes', 'write_bw_bytes', 'write_bw', 
        'write_iops', 'write_runtime', 'write_total_ios', 'write_short_ios', 'write_drop_ios', 
        'write_clat_ns_min', 'write_clat_ns_max', 'write_clat_ns_mean', 'write_clat_ns_stddev',
        'write_clat_ns_p1', 'write_clat_ns_p5', 'write_clat_ns_p10', 'write_clat_ns_p20', 'write_clat_ns_p30', 'write_clat_ns_p40', 'write_clat_ns_p50',
        'write_clat_ns_p60', 'write_clat_ns_p70', 'write_clat_ns_p80', 'write_clat_ns_p90', 'write_clat_ns_p95', 'write_clat_ns_p99', 'write_clat_ns_p99.5', 'write_clat_ns_p99.9', 'write_clat_ns_p99.95', 'write_clat_ns_p99.99', 'write_clat_ns_p0', 
        'write_lat_ns_min', 'write_lat_ns_max', 'write_lat_ns_mean', 'write_lat_ns_stddev',
        'write_bw_min', 'write_bw_max', 'write_bw_agg', 'write_bw_mean', 'write_bw_dev', 'write_bw_samples', 'write_iops_min', 'write_iops_max', 'write_iops_mean', 'write_iops_stddev', 'write_iops_samples',
        'trim_io_bytes', 'trim_io_kbytes', 'trim_bw_bytes', 'trim_bw', 'trim_iops', 'trim_runtime', 'trim_total_ios', 'trim_short_ios', 'trim_drop_ios', 'trim_clat_ns_min', 'trim_clat_ns_max', 'trim_clat_ns_mean', 'trim_clat_ns_stddev',
        'trim_clat_ns_p1', 'trim_clat_ns_p5', 'trim_clat_ns_p10', 'trim_clat_ns_p20', 'trim_clat_ns_p30', 'trim_clat_ns_p40', 'trim_clat_ns_p50',
        'trim_clat_ns_p60', 'trim_clat_ns_p70', 'trim_clat_ns_p80', 'trim_clat_ns_p90', 'trim_clat_ns_p95', 'trim_clat_ns_p99', 'trim_clat_ns_p99.5', 'trim_clat_ns_p99.9', 'trim_clat_ns_p99.95', 'trim_clat_ns_p99.99', 'trim_clat_ns_p0',
        'trim_lat_ns_min', 'trim_lat_ns_max', 'trim_lat_ns_mean', 'trim_lat_ns_stddev', 'trim_bw_min', 'trim_bw_max', 'trim_bw_agg', 'trim_bw_mean', 'trim_bw_dev', 'trim_bw_samples', 'trim_iops_min', 'trim_iops_max', 'trim_iops_mean', 'trim_iops_stddev', 'trim_iops_samples', 
        'usr_cpu', 'sys_cpu', 'ctx', 'majf', 'minf', 'latency_depth', 'latency_target', 'latency_percentile', 'latency_window'

        for fio3.19:
        'read_io_bytes', 'read_io_kbytes', 'read_bw_bytes', 'read_bw', 'read_iops', 'read_runtime', 'read_total_ios', 'read_short_ios', 'read_drop_ios',
        'read_clat_ns_min', 'read_clat_ns_max', 'read_clat_ns_mean', 'read_clat_ns_stddev',
        'read_clat_ns_N', 'read_clat_ns_p1', 'read_clat_ns_p5', 'read_clat_ns_p10', 'read_clat_ns_p20', 'read_clat_ns_p30', 'read_clat_ns_p40', 'read_clat_ns_p50',
        'read_clat_ns_p60', 'read_clat_ns_p70', 'read_clat_ns_p80', 'read_clat_ns_p90', 'read_clat_ns_p95', 'read_clat_ns_p99', 'read_clat_ns_p99.5', 'read_clat_ns_p99.9', 'read_clat_ns_p99.95', 'read_clat_ns_p99.99', 
        'read_lat_ns_min', 'read_lat_ns_max', 'read_lat_ns_mean', 'read_lat_ns_stddev', 'read_lat_ns_N', 'read_bw_min', 'read_bw_max', 'read_bw_agg', 'read_bw_mean', 'read_bw_dev', 'read_bw_samples', 'read_iops_min', 'read_iops_max',
         'read_iops_mean', 'read_iops_stddev', 'read_iops_samples', 'write_io_bytes', 'write_io_kbytes', 'write_bw_bytes', 'write_bw',
         'write_iops', 'write_runtime', 'write_total_ios', 'write_short_ios', 'write_drop_ios', 'write_clat_ns_min', 'write_clat_ns_max', 'write_clat_ns_mean', 'write_clat_ns_stddev', 
         'write_clat_ns_N', 'write_lat_ns_min', 'write_lat_ns_max', 'write_lat_ns_mean', 'write_lat_ns_stddev', 'write_lat_ns_N', 'write_bw_min', 'write_bw_max', 'write_bw_agg', 'write_bw_mean', 'write_bw_dev', 'write_bw_samples',
         'write_iops_min', 'write_iops_max', 'write_iops_mean', 'write_iops_stddev', 'write_iops_samples',
         'trim_io_bytes', 'trim_io_kbytes', 'trim_bw_bytes', 'trim_bw', 'trim_iops', 'trim_runtime', 'trim_total_ios', 'trim_short_ios', 'trim_drop_ios', 'trim_clat_ns_min', 'trim_clat_ns_max', 'trim_clat_ns_mean', 'trim_clat_ns_stddev',
         'trim_clat_ns_N', 'trim_lat_ns_min', 'trim_lat_ns_max', 'trim_lat_ns_mean', 'trim_lat_ns_stddev', 'trim_lat_ns_N', 'trim_bw_min', 'trim_bw_max', 'trim_bw_agg', 'trim_bw_mean', 'trim_bw_dev', 'trim_bw_samples', 
         'trim_iops_min', 'trim_iops_max', 'trim_iops_mean', 'trim_iops_stddev', 'trim_iops_samples', 'job_runtime', 'usr_cpu', 'sys_cpu', 'ctx', 'majf', 'minf', 'latency_depth', 'latency_target', 'latency_percentile', 'latency_window'
'''
fio_print_output_keys=False
#fio_print_output_keys=True

FIO_Addtional_Result_Keywords = {
    "MiB/s)": 1024.0,
    "GiB/s)": 1024.0*1024.0,
    "us)": 1000.0,
}
FIO_Addtional_Result = {}
FIO_Addtional_Result_ = {
    "read_bw(MiB/s)": 1024.0,
    "read_bw(GiB/s)": 1024.0*1024.0,
    "write_bw(MiB/s)": 1024.0,
    "write_bw(GiB/s)": 1024.0*1024.0,
    "read_lat_ns_mean(ms)": 1000.0,
    "write_lat_ns_mean(ms)": 1000.0,
    "read_clat_ns_p90(ms)": 1000.0,
    "read_clat_ns_p95(ms)": 1000.0,
    "write_clat_ns_p90(ms)": 1000.0,
    "write_clat_ns_p95(ms)": 1000.0,

}
FIO_nvme_env = {
    "single_nvmes":[],
    "group_nvmes":[],
    "nvmes_pcie_address":[],
    #    os.environ["OMP_NUM_THREADS"] 
}
FIO_Running = {
    "with_spdk": True,
    "in_container": False, #True,
    "spdk_setup_cmd":  "./spdk/scripts/setup.sh ",
    "nvme_devices": [],
     "prev_nvmes_in_spdk":[],
     "spdk_work_type":"fio_spdk",
     "cpu_even_only": True,
     "nvme_env": {},
}

FIO_Para = {
               #"work_type": "fio_libaio",
               "case": 1,
               "device_name": "",
               "blocksize":	"512",              
               "numjobs": 1,
               "read_write": "randrw",
               "iodepth": "32",
}
FIO_Para_Optional = {
               "numa_ctl": "NA",
               "cpus_allowed": "NA",
               "rwmixread":	 "NA",         
               "additional_para":	 "NA",         
               "pre_process": "",
               "post_process": "",
}
FIO_Para_With_Space = [ "numa_ctl", "additional_para"]
FIO_Para_With_Space_No_Replace = [ "pre_process", "post_process"]
xls_fio_keys_offset = {
}

nvme_devices_info = {}
nvme_detail = {
    "dev": "",
    "dev_path": "",
    "size": "",
    "slot": "",
    "numa_node":0,
    "cpu_affinity":""
    }
nodes_cpu_affinity = {}
node_cpus = {"start":0, "end":0}

def exclude_1st_core(c_affinity):
    k = c_affinity.find("-")
    nv = c_affinity[:k]
    excluded = int(nv) + 1
    n_cpu_affinity = str(excluded) + c_affinity[k:]
    return  n_cpu_affinity

def init_cpu_affinity_list():
    pcie_devices_cmd ="ls /sys/class/pci_bus/ "
    pcie_ds = Q_Cmd_Ext(pcie_devices_cmd)
    for d in pcie_ds:
        dr = d.replace(":", "\:")
        pcie_aff_cmd ="cat  /sys/class/pci_bus/" + dr + "/cpulistaffinity"
        dca = Q_Cmd_Ext(pcie_aff_cmd)
        
        if dca[0] not in nodes_cpu_affinity.keys():
            cl = dca[0].split(",")
            cpus = []
            s_l = []
            first_cores = 1
            for c in cl:
                nc = node_cpus.copy()
                cccc = c.split("-")
                nc["start"] = int(cccc[0]) + first_cores # to exclude the first core
                nc["end"] = int(cccc[1])
                first_cores = 0
                for c in range (nc["start"], nc["end"] + 1):
                    s_l.append(str(c))                   
                cpus.append(nc)
            nodes_cpu_affinity[dca[0]] = cpus
            nodes_cpu_affinity[dca[0] + "_list"] = s_l

def nvme_get_cpus(nvme_device, local=True):
    d = nvme_get_detail(nvme_device)
    if d is None:
        print("nvme_get_cpus, error for local ", nvme_device)
        print("error for ", nvme_devices_info)
        exit(1)
    if local:
        return exclude_1st_core(d['cpu_affinity'])
    else:
        for key in nodes_cpu_affinity.keys():
            if d['cpu_affinity'] not in key:
                if "_list" not in key:
                    return exclude_1st_core(key)
    print("error for remote ", nvme_device)
    print("error for ", nvme_devices_info)
    exit(1)

def nvme_get_cpus_partly(nvme_device, part, total, local=True):
    d = nvme_get_detail(nvme_device)
    print("nvme_get_cpus_partly", d, d['cpu_affinity'], nodes_cpu_affinity )
    if d is None:
        print("nvme_get_cpus_partly, error for local ", nvme_device)
        print("error for ", nvme_devices_info)
        exit(1)
    
    if local:
        vvv = d['cpu_affinity']
    else:
        for key in nodes_cpu_affinity.keys():
            if d['cpu_affinity'] != key and "_list" not in key:
                vvv =  key
                break

    w_l =  nodes_cpu_affinity[vvv +"_list"]
    len_ca = int(len(w_l)/int(total))
    start_ca = len_ca * (int(part) - 1)
    end_ca = start_ca + len_ca
    wa = w_l[start_ca:end_ca]
    wa_s=""
    for w in wa:
        if FIO_Running["cpu_even_only"] is True:
            if int(w) %2 == 0:
                wa_s +=","+w
        else:
            wa_s +=","+w
    #print(wa_s[1:])
    return wa_s[1:]
    print("error for remote ", nvme_device)
    print("error for ", nvme_devices_info)
    exit(1)

 
        # get nvme devices list and reset to default as no spdk
# need to set up huge page when running with nic dpdk, refer to dpdk_hugepage.sh
def nvme_devices_init():
    print("nvme_devices_init")
    nvme_decices_cmd = "lspci -vv   2>/dev/null  | grep 'Non-Volatile memory controller' | awk '{print $1}'"
    r = Q_Cmd(nvme_decices_cmd)
    rl = r.split("\n")
    for nvme in rl:
        r_d = nvme.strip()
        if r_d is not "":
            r_d = r_d.replace(":", ".")
            if "0000." not in r_d:
                r_d = "0000."  + r_d
            FIO_Running["nvme_devices"].append(r_d)
    if not FIO_Running["with_spdk"]:
        return
    cmd_s = FIO_Running["spdk_setup_cmd"] + "  reset "
    Q_Cmd(cmd_s) 

# check if the device is in nvme_devices list
def Fio_nvme_device_check(para):
    return para["device_name"]  in FIO_Running["nvme_devices"]
    
# check nvme spdk devices list, compare it to previous one, re-init if it's changed
# to reset nvme device, run cmd "run_fio_case.sh fio_nvme_reset"
def Fio_nvme_spdk_setup(gc, paras):
    if FIO_Running["in_container"] or not FIO_Running["with_spdk"]:
        return
    nvme_devices_in_gc = []
    changed = False
    for para in paras:
        if FIO_Running["spdk_work_type"] in para["work_type"]:
            if para["device_name"] in FIO_Running["nvme_devices"]:
                if para["device_name"] not in nvme_devices_in_gc:
                    nvme_devices_in_gc.append(para["device_name"])
                    if para["device_name"] not in FIO_Running["prev_nvmes_in_spdk"]:
                        changed = True
    if len(nvme_devices_in_gc) != len(FIO_Running["prev_nvmes_in_spdk"]):
        changed = True
    if changed:
        FIO_Running["prev_nvmes_in_spdk"] = nvme_devices_in_gc
        if len(nvme_devices_in_gc) is 0:
            cmd_s = FIO_Running["spdk_setup_cmd"] + "  reset"
            r = Q_Cmd(cmd_s)    
            return
            
        nvme_s = "'"
        for nv in nvme_devices_in_gc:
            nvl = nv.split(".")
            nvme_s += nvl[0] + ":" + nvl[1] + ":" + nvl[2] + "."  + nvl[3] + " "
        nvme_s +="'"    
        cmd_s ="PCI_ALLOWED=" + nvme_s + " " + FIO_Running["spdk_setup_cmd"]
        print(cmd_s)
        Q_Cmd(cmd_s)

def Load_Nvme_Info(IO_Running):
    try:
        for e in FIO_nvme_env.keys():
            FIO_nvme_env[e] = os.environ[e].split(",")
            if len(FIO_nvme_env[e]) == 0:
                return
    except:
        return
    try:
        for nvme in FIO_nvme_env["single_nvmes"]:
            IO_Running["fio_nvme_env"][nvme]= {}
            IO_Running["fio_nvme_env"][nvme]["pcie_address"] = FIO_nvme_env["nvmes_pcie_address"][FIO_nvme_env["single_nvmes"].index(nvme)]
        IO_Running["fio_nvme_env"]["group_nvmes"] = FIO_nvme_env["group_nvmes"]
    except:
        print("Error on parsing FIO_nvme_env ", FIO_nvme_env)
        exit(1)
    FIO_Running["nvme_env"] = IO_Running["fio_nvme_env"]
        
# Called during initialization
def Fio_Init(IO_Running):
    FIO_Running["in_container"] = Inside_container()
    Load_Nvme_Info(IO_Running)
    print("Fio_Init in_container", FIO_Running["in_container"])
    #if not FIO_Running["in_container"]:
    #if  FIO_Running["in_container"]:
    nvme_devices_init()
    for d in FIO_Running["nvme_devices"]:
        nvme_device_detail(d)

    init_cpu_affinity_list()

    

# return fio command line from a case para dictory
def Fio_Get_Cmd_Paras(para):
    try:
        ps = str(para["row"]) + " " + para["numa_ctl"] + " " +  para["device_name"] + " " + para["blocksize"] + " " + para["numjobs"] \
            + " " + para["read_write"] + " " + para["rwmixread"] + " " + para["iodepth"] + " " + para["additional_para"] + " " + para["cpus_allowed"] 
    except:
        print(para)
        exit(1)
    return ps


# Parsing fio case xls row item, return a test item as a para dictory    
def New_Fio_Case(xls_item, row, case_generating, row_offset, work_type, io_running):
    fio_p = FIO_Para.copy()
    keys_l = list(fio_p.keys()) + list(FIO_Para_Optional.keys())
    for key in  keys_l :
        if key not in xls_fio_keys_offset.keys():
            continue
        v = xls_item[xls_fio_keys_offset[key]]
        if v == "":
             # for mandatory paras
            if key in fio_p.keys():
                print("Ignored the case with invalid definition(s): ", xls_item)
                io_running["case_write_sheet"].write(row, io_running["fio_reult_key_index"], "Invalid_case")
                return None
            # for optional paras
            else:           
                v = "NA"
        if not case_generating  and key in FIO_Para_With_Space:
            if key not in FIO_Para_With_Space_No_Replace:
                v = v.replace("\n", " ") 
                v = v.replace(" ", "#") 
        else:
            if type(v) == type(1.0) and  math.isclose(v, float(int(v))): 
                v = str(int(v))
            if key not in FIO_Para_With_Space_No_Replace:
                if not case_generating and type(v) == type("string"): 
                    v = v.replace("\n", "") 
                    v = v.replace(" ", "")    
        if key is "case":
            #print(v)
            if type(v) == type(1.0) and v % 1 == 0.0: 
                v = str(int(v))

        if not io_running["case_generating"]:
            if key is "device_name":
                if v.upper() == "DEFAULT":
                    if work_type != "fio_spdk":
                        v = io_running["fio_device"]
                    else:
                        if "00." in io_running["fio_device"]:
                            v = io_running["fio_device"]
                        else:
                            if FIO_Running["nvme_env"] != {} and io_running["fio_device"] in FIO_Running["nvme_env"].keys():
                                v = FIO_Running["nvme_env"][io_running["fio_device"]]['pcie_address'].replace(":",".")
                            else:
                                print("Error on fio_device setting,", io_running["fio_device"] )
                                exit(1)
                # for fio_spdk, replacing nvme_dev name, like nvme1n1 with pcie adderess 
                elif work_type == "fio_spdk" and not "00." in v:
                    if FIO_Running["nvme_env"] != {} and v in FIO_Running["nvme_env"].keys():
                        v = FIO_Running["nvme_env"][v]['pcie_address'].replace(":",".")
                    else:
                        print("Error on fio_device setting,", io_running["fio_device"] )
                        exit(1)
                    
                elif not "/" in v:
                    if work_type != "fio_spdk":
                        v = "/dev/" + v

            elif key == "cpus_allowed":
                if work_type != "fio_spdk":
                    if ":" in v:
                            v_l = v.split(":")
                            if "/"  in v_l[1]:
                                n = v_l[1].split("/")[0]
                                t = v_l[1].split("/")[1]                    
                    if "LOCAL" in v.upper():                       
                        if "LOCAL" == v.upper():
                            v = nvme_get_cpus(fio_p["device_name"], local=True)
                        elif ":" in v:
                                v = nvme_get_cpus_partly(fio_p["device_name"], n, t, local=True)
                        else:
                            print("Error on cpus_allowed setting: ", v)
                            exit(1)
                    elif "REMOTE" in v.upper():
                        if "REMOTE" == v:
                            v = nvme_get_cpus(fio_p["device_name"], local=False)
                        elif ":" in v:
                                v = nvme_get_cpus_partly(fio_p["device_name"], n, t, local=False)
                        else:
                            print("Error on cpus_allowed setting: ", v)
                            exit(1)
        fio_p[key] = v
    fio_p["row"] =  row + 1 # + row_offset
    fio_p["work_type"] = work_type
    #print(fio_p)
    return  fio_p

# Parse fio json format result with the result file name provided
# return a json dictory
def FIO_Parser_Json_Result(file_name):
    try:
        json_data = open(file_name)
    except:
        print("Error on opening ", file_name)
        return None        
    try:
        data = json.load(json_data, cls=FioResultDecoder.FioResultDecoder)
        if fio_print_output_keys:
            if data is not None:
                if 'jobs' in data.keys():
                    print(data['jobs'][0].keys())
        return data
    except:
        print("Error on processing ", file_name)
        return None
#Init additional result keys, ex: "read_bw(MiB/s)"        
def Fio_Get_Additional_Result_Items():
    for key in xls_fio_keys_offset.keys():
        k = key.split("(")
        if len(k) > 1:
            if k[1] in FIO_Addtional_Result_Keywords.keys():
                FIO_Addtional_Result[key] = FIO_Addtional_Result_Keywords[k[1]]
#Get additional result, ex:     read_bw(MiB/s) = read_bw / 1024.0
def FIO_Result_Additional(re):
    added_p = FIO_Addtional_Result.copy()

    for added_key in added_p.keys():
        k = added_key.split("(")
        if k[0] in re.keys():
            added_p[added_key] = float(re[k[0]]) / FIO_Addtional_Result[added_key]
            #print(re[k[0]], added_p[added_key] )
    return added_p


def nvme_get_detail(nvme_device):
    for key in nvme_devices_info.keys():
        d = nvme_devices_info[key]
        if nvme_device in d['dev_path']:
            return d
    #print(nvme_device)
    #print(nvme_devices_info)
    return None

def nvme_device_detail(pci_domain_bus_slot_func):
    nd = nvme_detail.copy()
    #print("nvme_device_detail")
    dev_cmd ="nvme list-subsys  2>/dev/null | grep " +   pci_domain_bus_slot_func  + "  |  awk  '{print $2}' "
    dev = Q_Cmd_Ext(dev_cmd)
    if len(dev) > 0:
        nd["dev"] = dev[0]
    else:
        print("Error on checking nvme device", pci_domain_bus_slot_func)
        return 
    
    dev_path_cmd ="nvme list   2>/dev/null  | grep " +   nd["dev"]   + "  |  awk  '{print $1}' "
    dev_path = Q_Cmd_Ext(dev_path_cmd)
    if len(dev_path) > 0:
        nd["dev_path"] = dev_path[0]
    else:
        print("Error on checking nvme device", pci_domain_bus_slot_func)
        exit(1)

    #example cat /sys/class/pci_bus/0000\:07/device/numa_node
    dev = pci_domain_bus_slot_func.split(".")
    numa_node_cmd ="cat /sys/class/pci_bus/" + dev[0] + "\:" + dev[1]+ "/device/numa_node"
    numa_node = Q_Cmd_Ext(numa_node_cmd)
    if len(numa_node) > 0:
        nd["numa_node"] = numa_node[0]
    else:
        print("Error on checking nvme device", pci_domain_bus_slot_func)
        exit(1)   

    #example cat /sys/class/pci_bus/0000\:16/cpulistaffinity
    cpu_affinity_cmd ="cat /sys/class/pci_bus/" + dev[0] + "\:" + dev[1]+ "/cpulistaffinity"
    cpu_affinity = Q_Cmd_Ext(cpu_affinity_cmd)
    if len(cpu_affinity) > 0:
        #to exclude cpu 0 for node 0, and the corresponding one for node 1, ect.
        #print("nvme_device_detail", cpu_affinity[0])
        #k = cpu_affinity[0].find("-")
        #nv = cpu_affinity[0][:k]
        #excluded = int(nv) + 1
        #n_cpu_affinity = str(excluded) + cpu_affinity[0][k:]
        #print(nv, excluded, n_cpu_affinity)
        #exit(1)
        nd["cpu_affinity"] = cpu_affinity[0]
        #nd["cpu_affinity"] = exclude_1st_core(cpu_affinity[0])
    else:
        print("Error on checking nvme device", pci_domain_bus_slot_func)
        exit(1)  
        #print(numa_node_cmd, numa_node)

    nvme_devices_info[pci_domain_bus_slot_func] = nd

def nvme_device_warm_up(nvme_d):
    dev = None
    for n_d in nvme_devices_info.keys():
        if nvme_d in nvme_devices_info[n_d]["dev_path"]:
            dev = nvme_devices_info[n_d]
    if dev is not None:
        c = int(float(dev["size"]) *0.9) * 1000
        wm_cmd ="dd if=/dev/zero of=" + dev["dev_path"] + " bs=1M   count=" + str(c)
        print(wm_cmd)
        wm = Q_Cmd_Ext(wm_cmd) 
        print(wm)
def nvme_device_test():
    Fio_Init()
    print(FIO_Running["nvme_devices"])
    for d in FIO_Running["nvme_devices"]:
        nvme_device_detail(d)
    #nvme_detail = {}
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="")

    parser.add_argument('--device', type=str,help='device to be warmed up', default="")
    args = parser.parse_args()
    print(args)
    
    nvme_device_test()
    nvme_device_warm_up(args.device)
    
