import time
import os
from pathlib import Path
import argparse
from Cmd import  Q_Cmd, Q_Cmd_Ext
from utils import  save_array_2_xls, load_json, save_json, LogOut, Enable_Log
from os.path import exists
from pathlib import Path
#precommand:
"""
pip install pcicrawler
yum -y install   nvme-cli
"""



_nvme_devices_running = {
                    "work_folder":  os.path.abspath(os.path.dirname(__file__)), 
                    "excluded_nvmes": "", #"nvme2", 
                    "ex_devs": [], 
                    "output":"./nvme_infor_env.sh", 
                    "running_ini": "./nvme_running_ini.json"
}




_sys_info_settings = {
    "cmd_run_error_msg": "Error when running ", 

}
nvme_device_info = {
    "dev_name":"",
    "domain_bus_slot_func":"",
    "root_device_pcie":"",
    #"root_device":"",
    "with_logical_device": False,
    "node": "",
}
nv_infor={
    "excluded":[],
    "with_logical":[],
    "single":{},
    "grouped":{}
    }
def get_filename(xls_fn):
    return _nvme_devices_running["work_folder"] + "/" +xls_fn

def is_excepted(dev):
    #if  
    for e in _nvme_devices_running["ex_devs"]:
        if dev in e or e in dev:
            return True
    return False  

def generat_env_sh(out_f=_nvme_devices_running["output"]):
    rm_s = 'rm -rf ' + out_f + " 2>/dev/null"
    Q_Cmd(rm_s) 
    rm_s = 'rm -rf ' + _nvme_devices_running["running_ini"] + " 2>/dev/null"
    Q_Cmd(rm_s)

    single_s = ",".join(list(nv_infor["single"].keys()))
    echo_s = 'echo  export single_nvmes="' + single_s + '" > ' + out_f
    Q_Cmd(echo_s) 
    h_g=[]
    for r in nv_infor["grouped"].keys():
        g_d = []
        for d in nv_infor["grouped"][r]:
            g_d = g_d + [d['dev_name']+"n1"]
        if len(g_d) > 1:
            g_d_s = "_".join(g_d)
            h_g = h_g + [g_d_s]
    h_g_s = ",".join(h_g)
    echo_s = 'echo  export group_nvmes="' + h_g_s + '" >> ' + out_f
    Q_Cmd(echo_s

    ) 
    pcie_d = [nv_infor["single"][d]['domain_bus_slot_func']   for d in  nv_infor["single"].keys()]
    pcie_d_s = ",".join(pcie_d)
    #print(pcie_d_s)
    echo_s = 'echo  export nvmes_pcie_address="' + pcie_d_s + '" >> ' + out_f
    Q_Cmd(echo_s) 

    _node = [nv_infor["single"][d]['node']   for d in  nv_infor["single"].keys()]
    _node_s = ",".join(_node)
    echo_s = 'echo  export nvmes_node="' + _node_s + '" >> ' + out_f
    Q_Cmd(echo_s) 

    nodes_nvmes = {}
    LogOut(nv_infor["single"])

    for d in  nv_infor["single"].keys():
        nd = nv_infor["single"][d]
        if nd['node'] in nodes_nvmes.keys():
            nodes_nvmes[nd['node']].append(d)
        else:
            nodes_nvmes[nd['node']] = [d]
    
    LogOut(nodes_nvmes)
    nodes_nvmes_s_l = []
    for n in nodes_nvmes.keys():
        n_s = n + ":" + "_".join(nodes_nvmes[n])
        LogOut(n_s)
        nodes_nvmes_s_l.append(n_s)
    node_nvme_s = ",".join(nodes_nvmes_s_l)
    echo_s = 'echo  export nodes_nvmes="' + node_nvme_s + '" >> ' + out_f
    Q_Cmd(echo_s) 

    nodes_l = list(nodes_nvmes.keys())
    echo_s = 'echo  export nodes_list="' + ",".join(nodes_l) + '" >> ' + out_f
    Q_Cmd(echo_s) 

    #single_s_pcie = ",".join(list(nv_infor["single"].keys()))

    echo_s ='ls -lh ' + out_f +  '; cat ' + out_f
    print(Q_Cmd(echo_s) )

    
       
def Collect_nvme_Info(out_f = "./nvme_info.json"):
    def count_sub_str(sl, sb):
        count = 0
        for s in sl:
            if sb in s:
                count = count + 1
        return count
    pcicrawler_output = "./pcicrawler_output.json"
    ps = 'pcicrawler  --json >' + pcicrawler_output
    Q_Cmd_Ext(ps)
    pcicrawler_j = load_json(pcicrawler_output)
    ps = 'ls /dev/nvme*n1 | cut -d "/" -f3'
    nvd = Q_Cmd_Ext(ps)

    lsblk_c = 'lsblk | grep nvme | cut -d " "  -f1'
    lsblk_s = Q_Cmd_Ext(lsblk_c)
    gdl = {}
    for nv in nvd:
        if is_excepted(nv):
            continue
        nv_d = nvme_device_info.copy()
        nvme_device = nv.split("n1")[0]
        if is_excepted(nvme_device):
            continue
        ps = 'nvme list-subsys  | grep ' + nv[:5] + " |  cut -d ' '  -f5"
        nvme_device_sub = Q_Cmd_Ext(ps)
        d_domain_bus_slot_func = nvme_device_sub[0]
        if len(nvme_device_sub) == 0:
            continue
        nv_detail = pcicrawler_j[d_domain_bus_slot_func]
        root_device_pcie = nv_detail['path'][0]
        r_d = root_device_pcie.split(":")[1]
        nv_d["dev_name"] = nvme_device
        nv_d["domain_bus_slot_func"] = d_domain_bus_slot_func
        nv_d["root_device_pcie"] = root_device_pcie
        bus_slot_l = nv_d["domain_bus_slot_func"].split(":")
        bus_slot = bus_slot_l[0] + "\:"+  bus_slot_l[1]
        node_cmd_s="cat /sys/class/pci_bus/" + bus_slot  + "/device/numa_node"
        node = Q_Cmd_Ext(node_cmd_s)[0]
        nv_d["node"] = node
        LogOut(nv_d)
        if count_sub_str(lsblk_s, nv) > 1:
            nv_d["with_logical_device"] = True
            nv_infor["with_logical"].append(nv)
        nv_infor["single"][nv] = nv_d
        if not r_d in gdl.keys():
            gdl[r_d] = [nv_d]
        else:
            gdl[r_d].append(nv_d)
    for gd in gdl.keys():
        if len(gdl[gd]) > 1:
            nv_infor["grouped"][gd] = gdl[gd]
    #print(nv_infor)
    
    print("all nvme:")
    for d in nv_infor["single"].keys():
        print("single:      ", d, nv_infor["single"][d]["dev_name"],nv_infor["single"][d]["domain_bus_slot_func"], nv_infor["single"][d]["root_device_pcie"], nv_infor["single"][d]["with_logical_device"])

    for g in nv_infor["grouped"].keys():
        print("grouped in same root", g, ":")
        for d in nv_infor["grouped"][g]:
            print("group: ",g, "    ", d["dev_name"]+"n1",d["domain_bus_slot_func"], d["root_device_pcie"])
    print("with logical:", nv_infor["with_logical"]) 
    #save_json(out_f,nv_infor)
    generat_env_sh()
    
if __name__ == '__main__':
    Enable_Log()
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--excluded_nvmes', type=str,help='the nvme dev as an exception. Seperated by ";". Example: --excluded_nvmes "nvme2;nvme3" or --excluded_nvmes nvme2', default=_nvme_devices_running["excluded_nvmes"])
    parser.add_argument('--output', type=str,help='the env shell file name', default=_nvme_devices_running["output"])


    args = parser.parse_args()
    print(args)    
    _nvme_devices_running["excluded_nvmes"]=args.excluded_nvmes
    _nvme_devices_running["output"]=args.output
    if _nvme_devices_running["excluded_nvmes"] == "":
        _nvme_devices_running["ex_devs"] =[]
    else:
        _nvme_devices_running["ex_devs"]=_nvme_devices_running["excluded_nvmes"].split(";") if ";" in _nvme_devices_running["excluded_nvmes"] else _nvme_devices_running["excluded_nvmes"].split(",")
    print("Excluded:", _nvme_devices_running["ex_devs"])
    Collect_nvme_Info()
    

        
