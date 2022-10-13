import time
import os
from pathlib import Path
import argparse
from Cmd import C_CMD, Q_Cmd, Q_Cmd_Ext, T_Q_CMD, Tmux_CMD, Q_Remote_Cmd, Q_Remote_Cmd_Ext
from utils import get_statistics, save_array_2_xls, load_json
from os.path import exists
import numpy as np
import pandas as pd

"""
    fw for intel 810e
        mkdir -p  /lib/firmware/updates/intel/ice/ddp/
        cp $e810_driver_folder/ice_comms-1.3.30.0.pkg  /lib/firmware/updates/intel/ice/ddp/
        cp $e810_driver_folder/ice.pkg /lib/firmware/updates/intel/ice/ddp/

    Pktgen:
       - update pktgen_in_a_single_sever.json, according the nic devices. The pci bod can be got with command "lspci | grep Eth "
       - run : python CPktgen_DPDK.py
"""
_args = None

t_remote = None

Pktgen_env_settings = {
}

_nic_device_infor = {
    "bod":"",
    "device": "Intel810c",
    "Ethernet controller":"",
    "NUMA node":"",
}

_cpu_nodes_infor = {}

Pktgen_Running = {

    "cmd_ws": os.path.abspath(os.path.dirname(__file__)), 
    "local_power_monitor_cmds": ["sys_start_power_monitor.sh", "sys_stop_power_monitor.sh"],
    "remote_ip":"10.112.227.150",
    "test_time": 200,        
    "_test_time": 2,         
    "result_folder": "./_result/",     
    "ext_fn":"Pktgen_",      
    "pkt_size_range":[128, 256, 512, 1024, 2048, 4096],        
    "_pkt_size_range":[128],   
    "core_num_range":[1, 2, 3, 4, 5, 6],        
    "_core_num_range":[1],    
     "cfg": "./pktgen_in_a_single_sever.json",
    "with_remote_server": False,
    
    "naming_with_no": True, 
    "Pktgen_startup_up_time": 6,
    "Pktgen_warming_up_time": 20,
    "Pktgen_shutdown_time": 5,
    "client_bench_size": 1000,
    "ports_num": 6,
    "port_infor_local":{},
    "port_infor_remote":[],
    "ports_mapping_local":[6], #
    "ports_mapping_remote":[2,4], #
    #"cores_available_local": ["60-102"],
    "cores_available_remote": ["1-30","60-102"],
    "server_core": 24,
    "result_folder":os.path.abspath(os.path.dirname(__file__)) + "/_result/",
    #"with_remote_server": True,
    "local_mlnx_eth_devices": None,
    "remotel_mlnx_eth_devices": None,
    "local_e810c_eth_devices": None,
    "remotel_e810c_eth_devices": None,
    
    "dpdk_huge_page": os.path.abspath(os.path.dirname(__file__)) + "/dpdk_hugepage.sh",
     "dpdk_huge_page_reset": os.path.abspath(os.path.dirname(__file__)) + "/dpdk_hugepage_reset.sh",
     "dpdk_device_status": os.path.abspath(os.path.dirname(__file__)) + "/dpdk_device_status.sh",
     "dpdk_device_bind": os.path.abspath(os.path.dirname(__file__)) + "/dpdk_device_bind_vfio-pci.sh",
    "launch_cmd":os.path.abspath(os.path.dirname(__file__)) + "/launch_pktgen_with_excluded.sh",
    "with_setting_up": True,    
}
def get_nic_link_status(device):
    link_s = "ethtool " + device + " | grep "+ '"' + "Link detected:" + '"'
    interested= "yes"
    r = Q_Cmd_Ext(link_s, expected=interested)
    if len(r) > 0:
        return "Linked"
    return "Not_linked"
def get_nic_device_alias(pci, all_lshw):
    for n in all_lshw:
        if pci in n:
            #print(n.split(" ")[1])
            if n.split(" ")[1] != "network":
                return n.split(" ")[1]
            else:
                return ""
    print("Error in get_nic_device_alias ", pci, all_lshw)
    exit(1)        
def generate_default_cfg():
    mlnx_devices = get_mlnx_eth_device_list();
    e810c_devices = get_E810C_eth_device_list();

    print("\nDetecting NIC devices of E810C/MLNX")
    lshw_cmd_s = "lshw -c network -businfo | awk   '{print $1" + '" ' +  '"' +" $2 }' "
    interested = ":"
    print(lshw_cmd_s)
    r = Q_Cmd_Ext(lshw_cmd_s, expected=interested)
    #print(r)
    if len(r) == 0:
        print("Error on running ", lshw_cmd_s)
        print("Please check if lshw is available or not.")
        exit(1)

    all_device= mlnx_devices + e810c_devices
     

    for device in all_device:
        a = get_nic_device_alias(device, r)
        linked=""
        if a != "":
            linked = get_nic_link_status(a)
        if device in mlnx_devices:
            print("MLNX",device, a, linked)
        else:
            print("E810",device, a, linked)
    cfg_file = Pktgen_Running["cfg"]
    cmd_s = "echo { > " + cfg_file
    r = Q_Cmd_Ext(cmd_s)
    cmd_s = "echo " +"'" + '"' + "ports_local" + '":'  + '"' + " ".join(all_device) + '"' +"'"  + " >> " + cfg_file
    r = Q_Cmd_Ext(cmd_s)
    cmd_s = "echo } >> " + cfg_file
    r = Q_Cmd_Ext(cmd_s)

    print("\n")
    print(cfg_file, "is generated for reference. Please updated it based on needs.\n")
    cmd_s = " ls -lh  " + cfg_file
    print(Q_Cmd(cmd_s))
    cmd_s = "cat  " + cfg_file
    print(Q_Cmd(cmd_s))
   
def get_cpu_nodes_info(local_server=True):
    node_info_cmd_s = "numactl --hardware"
    interested = ["cpus"]
    if local_server:
        r = Q_Cmd_Ext(node_info_cmd_s, expected=interested) 
    else:
        r = Q_Remote_Cmd_Ext(Pktgen_Running["remote_ip"], node_info_cmd_s, expected=interested) 
    if len(r) > 0:
        for node in r:
            v = node.split(":")
            _cpu_nodes_infor[v[0].split(" ")[1]] = v[1].strip().split(" ")
    if not "cores_available_local" in Pktgen_Running.keys():
        Pktgen_Running["cores_available_local"] = list(len(_cpu_nodes_infor.keys()) * "-")
        for node in _cpu_nodes_infor.keys():
            s = int(_cpu_nodes_infor[node][1])
            e = int(len(_cpu_nodes_infor[node]) /2 + s -2)
            new_s = str(s)  + "-" + str(e)
            Pktgen_Running["cores_available_local"][int(node)] = new_s
        
def get_nodes_number():
    return len(_cpu_nodes_infor.keys())
def get_ports_number():
    return len(Pktgen_Running["port_infor_local"].keys())

def get_port_mapping(local_server=True):
    n_mapping = {}
    for i in range(get_nodes_number()):
       n_mapping[str(i)] = 0; 
    for bod in Pktgen_Running["port_infor_local"].keys():
        nd = Pktgen_Running["port_infor_local"][bod]
        n_mapping[nd["NUMA node"]] += 1
    nn = get_nodes_number()
    Pktgen_Running["ports_mapping_local"] = list(range(nn))
    for i in range(0,nn):
        Pktgen_Running["ports_mapping_local"][i] = n_mapping[str(i)]
    print("get_port_mapping", local_server, Pktgen_Running["ports_mapping_local"])
    
def get_nic_device_infor(eth_device, local_server=True):
    nd = _nic_device_infor.copy()
    nd["bod"] = eth_device
    info_cmd = " lspci -vv -s "+ eth_device # + "  > "+  tmp_f
    interested = list(_nic_device_infor.keys())
    if local_server:
        r = Q_Cmd_Ext(info_cmd, expected=interested) 
    else:
        r = Q_Remote_Cmd_Ext(Pktgen_Running["remote_ip"], info_cmd, expected=interested) 
    #print(r)
    if len(r) > 1:
        if "Ethernet controller" in r[0]:
            nd["Ethernet controller"] = r[0][len("16:00.1 Ethernet controller: "):]
        if "NUMA node" in r[1]:
            nd["NUMA node"] = r[1][len("'NUMA node:"):].strip()
    if "ConnectX" in nd["Ethernet controller"] :
        nd["device"] = nd["Ethernet controller"] [nd["Ethernet controller"].find("[") + 1 : -1]
    #print(nd)
    return nd

def is_mlnx_eth_device(eth_device, local_server=True):
    mlnx_devices = get_mlnx_eth_device_list(local_server,kept=True)
    if eth_device in mlnx_devices :
        return True
    return False
def remove_mlnx_eth_device(eth_device, local_server=True):
    mlnx_devices = get_mlnx_eth_device_list(local_server, kept=True)
    if local_server:
        if Pktgen_Running["local_mlnx_eth_devices"] != [] and eth_device in  Pktgen_Running["local_mlnx_eth_devices"]  :
            Pktgen_Running["local_mlnx_eth_devices"].remove(eth_device)
    else:
        if Pktgen_Running["remotel_mlnx_eth_devices"] != [] and eth_device in  Pktgen_Running["remotel_mlnx_eth_devices"] :
            Pktgen_Running["remotel_mlnx_eth_devices"].remove(eth_device)
    
def get_mlnx_eth_device_list(local_server=True, kept=False):
    mlnx_device_list_cmd = "lspci | grep Eth | grep  MT |   awk  '{print $1}'"
    interested=":"
    r_list = None
    if local_server:
        if type( Pktgen_Running["local_mlnx_eth_devices"]) == type(None):
            r = Q_Cmd_Ext(mlnx_device_list_cmd, expected=interested) 
            Pktgen_Running["local_mlnx_eth_devices"] = r
            Pktgen_Running["local_mlnx_eth_devices_kept"] = r.copy()
        r_list = Pktgen_Running["local_mlnx_eth_devices_kept"] if kept else Pktgen_Running["local_mlnx_eth_devices"]
            
    else:
        if type( Pktgen_Running["remotel_mlnx_eth_devices"]) == type(None):
            r = Q_Remote_Cmd_Ext(Pktgen_Running["remote_ip"], mlnx_device_list_cmd, expected=interested)
            Pktgen_Running["remotel_mlnx_eth_devices"] = r
            Pktgen_Running["remote_mlnx_eth_devices_kept"] = r.copy()
        r_list = Pktgen_Running["remote_mlnx_eth_devices_kept"] if kept else Pktgen_Running["remote_mlnx_eth_devices"]
    return r_list
def get_E810C_eth_device_list(local_server=True):
    mlnx_device_list_cmd = "lspci | grep Eth | grep  E810-C |   awk  '{print $1}'"
    interested=":"
    if local_server:
        if type( Pktgen_Running["local_e810c_eth_devices"]) == type(None):
            r = Q_Cmd_Ext(mlnx_device_list_cmd, expected=interested) 
            Pktgen_Running["local_e810c_eth_devices"] = r
            #print(r)
        return Pktgen_Running["local_e810c_eth_devices"] 
    else:
        if type( Pktgen_Running["remotel_e810c_eth_devices"]) == type(None):
            r = Q_Remote_Cmd_Ext(Pktgen_Running["remote_ip"], mlnx_device_list_cmd, expected=interested)
            Pktgen_Running["remotel_e810c_eth_devices"] = r
        return Pktgen_Running["remotel_e810c_eth_devices"] 
   
    
def pktgen_setting_up():
    def check_hugepage(local_server=True):
        dpdk_huge_page_cmd = Pktgen_Running["dpdk_huge_page"] 
        interested = ["HugePages_Total", "HugePages_Free"]
        r = Q_Cmd_Ext(dpdk_huge_page_cmd, expected=interested)  if local_server else Q_Remote_Cmd_Ext(Pktgen_Running["remote_ip"], dpdk_huge_page_cmd, expected=interested)

        run_error = True
        for l in r:
            if "HugePages_Total" in l:
                total = int(l.split(":")[1])
                run_error = False
            elif "HugePages_Free" in l:
                free = int(l.split(":")[1])  
        if run_error:
            s = "Local" if local_server else Pktgen_Running["remote_ip"]
            print("Error on running", s, dpdk_huge_page_cmd)
            print(r)
            exit(1)
        return total, free

    def get_dpdk_device_status(local_server=True):
        dpdk_device_status_cmd = Pktgen_Running["dpdk_device_status"] 
        interested = [""]
        r = Q_Cmd_Ext(dpdk_device_status_cmd, expected=interested)  if local_server else Q_Remote_Cmd_Ext(Pktgen_Running["remote_ip"], dpdk_device_status_cmd, expected=interested)
        #print(r)
        s_start = False
        run_error = True
        dpdk_devices = []
        for l in r:
            if s_start:
                s_s = l.split(" ")
                if len(s_s) > 1 and ":" in s_s[0] :
                    dpdk_devices.append(s_s[0])
            if "DPDK-compatible" in l:
                s_start = True
                run_error = False
            if "using kernel driver" in l:
                s_start = False    
        if run_error and len(dpdk_devices) != 0:
            s = "Local" if local_server else Pktgen_Running["remote_ip"]
            print("Error on running", s, dpdk_device_status_cmd)
            print(r)
            exit(1)
        return dpdk_devices
        
    def dpdk_device_bind(local_server, s, devices):
        dpdk_device_bind_cmd = Pktgen_Running["dpdk_device_bind"]  + " " + " ".join(devices)
        print("Binding ", s, devices, "  Command: ", dpdk_device_bind_cmd)
        Q_Cmd_Ext(dpdk_device_bind_cmd, expected=[])  if local_server else Q_Remote_Cmd_Ext(Pktgen_Running["remote_ip"], dpdk_device_bind_cmd, expected=[])
        return

    remote_local =[True, False] if Pktgen_Running["with_remote_server"] else [True] 
    
    for local in remote_local:
        max_retry = 5
        s = "local" if local else "remote"
        for i in range(max_retry):
            t, f  = check_hugepage(local)
            print(s, "huge page, total:", t, "free:", f)
            if f > 8096:
                break
            hugepage_reset=Pktgen_Running["dpdk_huge_page_reset"]
            Q_Cmd(hugepage_reset) 

        def get_to_be_init(logout = True):
            dpdk_devices = get_dpdk_device_status(local)
            if logout:
                print("Already bound: ", dpdk_devices)
            devices_key = "ports_" + s
            to_be_init = []
            mlnx_init = []
            if devices_key in Pktgen_Running.keys() or len(Pktgen_Running[devices_key].split(" ")) < 1:
                devices = Pktgen_Running[devices_key].split(" ")
                for d in devices:
                    bus_add = "0000:"
                    if not bus_add in d:
                        d = bus_add + d
                    if not d in dpdk_devices:
                        if not is_mlnx_eth_device(d[5:], local):
                            to_be_init.append(d)
                        else:
                            mlnx_init.append(d[5:])
                            remove_mlnx_eth_device(d[5:], local)
                    if not d[5:] in  Pktgen_Running["port_infor_local"].keys():
                        nd = get_nic_device_infor(d[5:], local)
                        Pktgen_Running["port_infor_local"][d[5:]] = nd
            else:
                print("No nic device pci address is provided in", devices_key)
                exit()
            if logout:
                print("To_be_init:", s, to_be_init)
                if len(mlnx_init) > 0:
                    print("Using mlnx nic devices:", mlnx_init)
            return to_be_init
            
        to_be_init = get_to_be_init()
        if len(to_be_init) > 0:
            print("binding ", to_be_init)
            dpdk_device_bind(local, s, to_be_init)
        if len(get_mlnx_eth_device_list(local)) > 0:
            print("Excluded mlnx nic devices:", get_mlnx_eth_device_list(local))
        current_to_be_init = get_to_be_init(logout = False)
        if len(to_be_init) > 0  and len(current_to_be_init) > 0:
            print("Fail to bind device", s, to_be_init,current_to_be_init,  "to dpdk_drivers", " using", Pktgen_Running["dpdk_device_bind"]) 
            exit(1)
        get_cpu_nodes_info()
        get_port_mapping()

class Pktgen():
    def __init__(self, name, ip="", auto_delete=True, cores="60-75", pkt_size=512, port_num=1, lunch_cmd=""):
        self.name = name
        self.ssh_ip = ip
        self.cores = cores
        self.auto_delete = auto_delete
        self.pkt_size = pkt_size
        self.port_num = port_num
        
        self.tmux = Tmux_CMD(name, auto_delete=False, ssh_ip=self.ssh_ip)
        self.tmux.export_env(Pktgen_env_settings)
        self.lunch_cmd=lunch_cmd
        if self.lunch_cmd == "":
            self.lunch_cmd = self.generate_lunch_cmd()
    def generate_lunch_cmd():
        return ""
        #self.start()
    def __del__(self):
        if self.auto_delete:
            self.stop()
            
    def stop_bench(self):
        self.tmux.send_cmd("stop all ")
        self.tmux.send_cmd("quit")
            
    def start(self, log_file=""):
        lunch_cmd_s = self.lunch_cmd
        if log_file != "":
            lunch_cmd_s += " " + log_file
        r = self.tmux.send_cmd(lunch_cmd_s)
        print(r)


    def run(self, pkt_size=0):
        if pkt_size==0:
            pkt_size=self.pkt_size
        for i in range(self.port_num):
            pkt_size_cmd = "set " + str(i) + " size " + str(pkt_size)
            r = self.tmux.send_cmd(pkt_size_cmd)
        self.tmux.send_cmd("str")

    def switch_page(self, page):
        self.tmux.send_cmd("page  " + str(page) )
        
    def stop(self):
        self.tmux.send_cmd("quit ")
        time.sleep(5)
        self.tmux.stop()
        
        
def get_cores(local=True, cn=2):

    p_mapping = Pktgen_Running["ports_mapping_local"] if local else Pktgen_Running["ports_mapping_remote"] 
    c_available = Pktgen_Running["cores_available_local"] if local else Pktgen_Running["cores_available_remote"] 
    #print(p_mapping, c_available)
    idx = 0
    core_m_s = ""
    total_s=""
    port_idx = 0
    reserved = False

    
    for p in p_mapping:
        ca = c_available[idx]
        idx += 1
        ca_start_ = int(ca.split("-")[0])
        if not reserved:
            ca_start = ca_start_ + 1 
            reserved = True
        else:
            ca_start = ca_start_
        
        ca_end = int(ca.split("-")[1])
        last = ca_start
        for pp in range(p):
            s = "[" + str(ca_start) + "-" + str(ca_start+cn - 1) + "]." + str(port_idx) + ","
            port_idx +=1
            last = ca_start + cn -1
            ca_start += cn
            core_m_s += s
        total_s += str(ca_start_) + "-" + str(last) + ","
        
    total_s = total_s[:-1]   
    cs = core_m_s[:-1]
    return total_s, cs

    

def  Pktgen_Single_Run(duration_seconds=60, pkt_size=512, cn=4, port_num=6, log_file=""):

    totol_s_local, cs_local =  get_cores(local=True, cn=cn)
    local_launch_cmd=Pktgen_Running["launch_cmd"] + " "  + totol_s_local + " " + cs_local 
    if len(Pktgen_Running["local_mlnx_eth_devices"]) > 0:
        excluded = "Xb".join(Pktgen_Running["local_mlnx_eth_devices"])
        if len(Pktgen_Running["local_mlnx_eth_devices"]) >= 1:
            excluded = "Xb" + excluded
    else:
        excluded = "NA"
    local_launch_cmd = local_launch_cmd + " " + excluded + " "
    pktgen_local = Pktgen("pktgen_local", port_num=port_num, auto_delete=False, pkt_size=pkt_size, lunch_cmd=local_launch_cmd)
    
    if Pktgen_Running["with_remote_server"]:
        totol_s_remote, cs_remote =  get_cores(local=False, cn=cn)
        remote_launch_cmd=Pktgen_Running["launch_cmd"] + " "  + totol_s_remote + " " + cs_remote 
        print(remote_launch_cmd)
        pktgen_remote = Pktgen("pktgen_remote", Pktgen_Running["remote_ip"], port_num=port_num,auto_delete=False, pkt_size=pkt_size, lunch_cmd=remote_launch_cmd)
    try:
        pktgen_local.start(log_file=log_file)
        if Pktgen_Running["with_remote_server"]:
            pktgen_remote.start()
        time.sleep(Pktgen_Running["Pktgen_startup_up_time"])
        
        pktgen_local.run()
        if Pktgen_Running["with_remote_server"]:
            pktgen_remote.run()            
        time.sleep(Pktgen_Running["Pktgen_warming_up_time"])

        if port_num > 6:
            pktgen_local.switch_page(1)
            if Pktgen_Running["with_remote_server"]:
                pktgen_remote.switch_page(1)            
            time.sleep(Pktgen_Running["Pktgen_warming_up_time"])
        
            pktgen_local.switch_page(0)
            if Pktgen_Running["with_remote_server"]:
                pktgen_remote.switch_page(0)        
            time.sleep(duration_seconds)
        else:
            time.sleep(Pktgen_Running["Pktgen_warming_up_time"])

        pktgen_local.stop()
        if Pktgen_Running["with_remote_server"]:
            pktgen_remote.stop()  

    except KeyboardInterrupt:
        print("Keyboard interrputed, waiting for clean up")
        time.sleep(Pktgen_Running["Pktgen_startup_up_time"])
        pktgen_local.stop()
        if Pktgen_Running["with_remote_server"]:
            pktgen_remote.stop()  
        
    return

    
    def stop_power_monitor():
        if len(Pktgen_Running["local_power_monitor_cmds"]) > 1:
            print("Stopping local_power_monitoring")    
            if Pktgen_Running["local_power_monitor_cmds"][1] != "":
                r = Q_Cmd(Pktgen_Running["local_power_monitor_cmds"][1])
    try:
        if len(Pktgen_Running["local_power_monitor_cmds"]) != 0:
            if Pktgen_Running["local_power_monitor_cmds"][0] != "":
                power_monitor_log_file = log_file + "_rapl.log"
                print("Starting local_power_monitoring, saving to", power_monitor_log_file)
                r = Q_Cmd(Pktgen_Running["local_power_monitor_cmds"][0] + " " + power_monitor_log_file)
                #print(r)
        if Pktgen_Running["with_remote_server"]:
            t_remote = Pktgen_Remote()
            t_remote.start_server()
        Pktgen_s = Pktgen_Server("Pktgen_ss", auto_delete=True, core_num=cn, with_log=True, log_file=log_file)
        time.sleep(5)
        if Pktgen_Running["with_remote_server"]:
            t_remote.start_client(pkt_size=pkt_size)
        Pktgen_c = Pktgen_Client("Pktgen_client", auto_delete=True)
        Pktgen_c.start_bench(pkt_size=pkt_size)
        time.sleep(duration_seconds)    

        if Pktgen_Running["with_remote_server"]:
            t_remote.stop()
    except KeyboardInterrupt:
        print("Keyboard interrputed")
        stop_power_monitor();
        if Pktgen_Running["with_remote_server"]:
            print("Stopping Remote server!")
            t_remote.stop()
            time.sleep(2)
        exit(1)
    stop_power_monitor();

def Pktgen_Parsing_Single_Result(log_fn, warming_up=Pktgen_Running["Pktgen_warming_up_time"], shutdown=Pktgen_Running["Pktgen_shutdown_time"]):
    if not exists(log_fn):
        print("Pktgen_Parsing_Single_Result error, file does not exists", log_fn)
        return None
    print(log_fn)

    def replacing_1B_2_0D0A(input_fn, output_fn):
        with open(input_fn,'rb') as in_f:
            with open(output_fn,'w') as out_f:
                line_len = 128
                buff =in_f.read(line_len)
                
                
                while len(buff) > 0:
                    outb=""
                    for i in range(len(buff)):
                        #:
                        outb = outb + "\n" if buff[i] == 0x1B else outb +  str(chr(buff[i]))
                        #else:
                           
                    out_f.write(outb)
                    buff =in_f.read(line_len)
    def interested_line(fn, ln_char):
        interested = "'\[" + str(ln_char) + ";'"
        txl_cmd = "cat " + tmp_f + " | grep " + interested     
        txl = Q_Cmd_Ext(txl_cmd)
        return txl
    def get_overal_throughputs(sl):
        all_throuphputs = {}
        for l in sl:
            x = l.split("H")
            if len(x) > 1:
                if x[0] not in all_throuphputs.keys():
                    all_throuphputs[x[0]] = [x[1]]
                else:
                    all_throuphputs[x[0]].append(x[1])
        wanted = 0
        wanted_k = ""
        for key in all_throuphputs.keys():
            v = key.split(";")
            if len(v) > 1:
                if int(v[1]) > wanted:
                    wanted = int(v[1])
                    wanted_k = key
        tvl = []
        for t in all_throuphputs[wanted_k]:
            v = t.split("/")
            if len(v) > 1:
                recv_througput = int(v[0].replace(",", ""))
                send_througput  = int(v[1].replace(",", ""))
                tvl.append([send_througput, recv_througput])
        return tvl
        
    tmp_f = "/tmp/pktgen_log_tmp.txt"  
    replacing_1B_2_0D0A(log_fn, tmp_f)
    throuphputs = interested_line(tmp_f, 6)
    overall = get_overal_throughputs(throuphputs)
    start_point = len(overall) - Pktgen_Running["Pktgen_shutdown_time"] - Pktgen_Running["test_time"] + Pktgen_Running["Pktgen_warming_up_time"]
    if start_point < 0 or start_point > len(overall):
        start_point = 0
    needed = overall[start_point:-Pktgen_Running["Pktgen_shutdown_time"]] if not Pktgen_Running["Pktgen_shutdown_time"] > len((overall)) else overall
    n = np.array(needed) 
    receive_v = n[:, 0]
    send_v = n[:, 1]
    receive_statics = get_statistics(receive_v)
    send_statics = get_statistics(send_v)
    ov =  send_statics + receive_statics
    return ov


def Get_Pktgen_Result_FN(pkt_size, cn, no):
    if Pktgen_Running["naming_with_no"] :
        fn = Pktgen_Running["ext_fn"] + "_no._" + str(no) + "_pkt_" + str(pkt_size) + "_c_" + str(cn) + "_log.txt"
    else:
        fn = Pktgen_Running["ext_fn"] + "_" + "_pkt_" + str(pkt_size) + "_c_" + str(cn) + "_log.txt"
    log_fn = Pktgen_Running["result_folder"] + fn
    return log_fn, fn
    
def Parsing_Pktgen_Result():
    result_all = []
    no = 1
    for pkt_size in Pktgen_Running["pkt_size_range"]:
        for cn in Pktgen_Running["core_num_range"]:
            log_fn, fn = Get_Pktgen_Result_FN(pkt_size, cn, no)
            pr = Pktgen_Parsing_Single_Result(log_fn)
            if pr is not None:
                xr = [fn] + [pkt_size] +  [cn] +list(pr)
                result_all.append(xr)
            no = no + 1
    result_file=Pktgen_Running["result_folder"] + "./Pktgen_result.xls"
    header = ["fn", "pkt_size", "core_num", "tx _mean(Mbps)", "tx_std_v(Mbps)", "tx_min(Mbps)", "tx_max(Mbps)", "tx_p95(Mbps)", \
                                                        "rx _mean(Gbps)", "rx_std_v(Gbps)", "rx_min(Mbps)", "rx_max(Mbps)", "rx_p95(Mbps)"]

    brief_header = ["core_num"]
    breif_items = ["tx(Mbps)",  "rx(Mbps)"]

    for pkt_s in Pktgen_Running["pkt_size_range"]:
        for item in breif_items:
            b_i = str(pkt_s) + "_" + item
            brief_header.append(b_i)

    def get_result_of_pktgen_cn(all_rows, pkts, cn):
        for r_ in all_rows:
            if r_[1] == pkts and r_[2] == cn:
                return r_
        print("Not found in get_result_of_pkt_cn for ", pkts, cn)
        exit(1)

    if 1:
        brief_list = []
        for cn in Pktgen_Running["core_num_range"]:
            b_r = [cn]
            for pkt_s in Pktgen_Running["pkt_size_range"]:
                row = get_result_of_pktgen_cn(result_all, pkt_s, cn)
                b_r.append(row[3])
                b_r.append(row[8])
            brief_list.append(b_r)

    print(result_all)
    writer = save_array_2_xls(result_file, Pktgen_Running["ext_fn"] + "_detail", result_all, head=header, Final=False, writer=None)
    save_array_2_xls(result_file, Pktgen_Running["ext_fn"]+ "_brief", brief_list, head=brief_header, Final=True, writer=writer)
    print("Result is saved to ", result_file)
    ls_result = "ls -lh " + result_file
    print(Q_Cmd(ls_result))
def Pktgen_Multiple_Run():

    duration = Pktgen_Running["test_time"]
    r_c = "mkdir -p " + Pktgen_Running["result_folder"]
    Q_Cmd(r_c)
    total = len(Pktgen_Running["pkt_size_range"]) * len(Pktgen_Running["core_num_range"])
    no = 1
    for pkt_size in Pktgen_Running["pkt_size_range"]:
        for cn in Pktgen_Running["core_num_range"]:
            if no >= _args.run_from:
                if  Pktgen_Running["run_cases"] != []:
                    if not str(no) in Pktgen_Running["run_cases"] :
                        no = no + 1
                        continue;
                print("\n\nPktgen_Single_Run, pkt_size ", pkt_size, "core_num:", cn, "   ", no, "of", total)
                log_fn, _ = Get_Pktgen_Result_FN(pkt_size, cn, no)
                Pktgen_Single_Run(duration_seconds = duration, pkt_size = pkt_size, cn = cn, log_file = log_fn, port_num=get_ports_number())
            no = no + 1

    
if __name__ == '__main__':
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--parsing_only', type=str2bool,help='parsing test result only: True/False', default=False)
    parser.add_argument('--run_from', type=int,help='run cases from the row specified: int', default=0)
    parser.add_argument('--run_cases', type=str,help='run cases from the row specified: str, seperated by ,', default="")
    parser.add_argument('--cfg', type=str,help='vm cfg in json format  ', default=Pktgen_Running["cfg"])
    parser.add_argument('--with_setting_up', type=str2bool,help='parsing test result only: True/False', default=Pktgen_Running["with_setting_up"])
    
    _args = parser.parse_args()
    print("\n")
    print(_args)
    Pktgen_Running["cfg"] = _args.cfg  
    Pktgen_Running["with_setting_up"] = _args.with_setting_up  
    Pktgen_Running["run_from"] = _args.run_from      
    Pktgen_Running["run_cases"] = []      
    if _args.run_cases != "":
        Pktgen_Running["run_cases"] = _args.run_cases.split(",")
    
    if Pktgen_Running["cfg"] != "":
        if not exists(Pktgen_Running["cfg"]):
            print("Fail to load cfg ", Pktgen_Running["cfg"])
            generate_default_cfg()
            exit(1)
        Pktgen_Running["cfg_settings"] = load_json(Pktgen_Running["cfg"])
        if type(Pktgen_Running["cfg_settings"]) != type(None):            
            print("Loaded cfg from ", Pktgen_Running["cfg"])
            for key in Pktgen_Running["cfg_settings"]:
                Pktgen_Running[key] = Pktgen_Running["cfg_settings"][key]
            print(Pktgen_Running["cfg_settings"])
    print("\n")

    
    t_p = 0
    for ele in range(0, len(Pktgen_Running["ports_mapping_local"] )):
        t_p = t_p + Pktgen_Running["ports_mapping_local"] [ele]
    Pktgen_Running["ports_num"] = t_p

    
    r_c = "mkdir -p " + Pktgen_Running["result_folder"]
    Q_Cmd(r_c)

    Pktgen_Running["ports_local"].replace(",", " ")
    Pktgen_Running["ports_local"].replace(";", " ")
    

    if not _args.parsing_only:
        if Pktgen_Running["with_setting_up"]:
            pktgen_setting_up()
        Pktgen_Multiple_Run()
    Parsing_Pktgen_Result()

    exit()
    
        
