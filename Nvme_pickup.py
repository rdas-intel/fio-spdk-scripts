import time
import os
from pathlib import Path
import argparse
from Cmd import  Q_Cmd, Q_Cmd_Ext
from utils import   load_json, save_json, LogOut, Enable_Log, Env_Read,Env_Set
from os.path import exists
from pathlib import Path
import random
#precommand:
"""
    - Save the history as json
    - Save for next list, sequencially or randomly
    - load env settings
    - return by env or print out
"""



_nvme_pickup_running = {
                    "work_folder":  os.path.abspath(os.path.dirname(__file__)), 
                    "excluded_nvmes": "", #"nvme2", 
                    "ex_devs": [], 
                    "env_file":"./nvme_infor_env.sh", 
                    "running_ini": "./nvme_running_ini.json"
}






_nvme_env_info = {
    "single_nvmes":[],
    "group_nvmes":[],
    "nvmes_node":[],
    "nodes_nvmes":[],
}

def load_env(env_file=None):
    def check_error(env_k, env_s):
        if env_s == "":
            print("Error! env setting '", env_k, "' is empty. Plese run 'source ./nvme_infor_env.sh' first!")
            exit(1)
    def read_env(env_k):
        s = Env_Read(env_k)
        check_error(env_k, s)
        return s
        
    for env_k in _nvme_env_info.keys():
        v = read_env(env_k)
        _nvme_env_info[env_k] = v.split(",")

    n_l = _nvme_env_info["nodes_nvmes"]
    n_d = {}
    for node_nvmes in n_l:
        n = node_nvmes.split(":")
        node = n[0]
        nvmes = n[1]
        n_d[node] = nvmes.split("_")
    _nvme_env_info["nodes_nvmes"] = n_d
    
    LogOut(_nvme_env_info)
def pickup():
    r_list = []
    n_list = []
    _running_ini = {
        "single_nvmes":[],
        "group_nvmes":[],
        "nodes_nvmes":{},
    }
    if os.path.exists(_nvme_pickup_running["running_ini"]):
        LogOut("Loading", _nvme_pickup_running["running_ini"])
        ini = load_json(_nvme_pickup_running["running_ini"])
        if type(None) != type(ini):
            _running_ini = ini
    LogOut(_running_ini)

    if args.socket.upper() == "RANDOM":
        try:
            to_checkout = int(args.nu)
        except:
            print("Erorr for parameter nu:", args.nu)
            exit(1)        

        nodes_list = list(_nvme_env_info["nodes_nvmes"].keys())
        nodes_nu = len(nodes_list)
        LogOut(nodes_list)
        if to_checkout > nodes_nu:
            nodes_list_to_add = (to_checkout -nodes_nu) * nodes_list
            random.shuffle(nodes_list_to_add)
        else:
            nodes_list_to_add = []
        nodes_list += nodes_list_to_add
        nl =  nodes_list[:to_checkout]
        random.shuffle(nl)
        LogOut(nodes_list_to_add, to_checkout, nodes_nu)
        nvds_l = [_nvme_env_info["nodes_nvmes"][s] for s in nl]
        nvds = [";".join(snv) for snv in nvds_l]
        print("random_sockets:" + ",".join(nl))
        print(" random_s_nvmes:" + ",".join(nvds))

        return 
            


    if args.single:
        if args.socket.upper() == "ANY":
            r_list = _running_ini["single_nvmes"]
            n_list = _nvme_env_info["single_nvmes"]
        else:
            if args.socket in _running_ini["nodes_nvmes"].keys():
                r_list = _running_ini["nodes_nvmes"][args.socket]
                n_list = _nvme_env_info["nodes_nvmes"][args.socket]
            else:
                if args.socket in _nvme_env_info["nodes_nvmes"].keys():
                    r_list = []
                    n_list = _nvme_env_info["nodes_nvmes"][args.socket]
                else:
                    print("Error! No nvme devices in socket", args.socket)
                    exit(1)
    if args.randomly:
        random.shuffle(n_list)
    for item in r_list:
        n_list.remove(item)
    if args.nu.upper() == "ALL":
        to_checkout = len(n_list) + len(r_list)
    else:
        try:
            to_checkout = int(args.nu)
        except:
            print("Erorr for parameter nu:", args.nu)
            exit(1)
    if to_checkout < 1:
        to_checkout = 1
    
    if len(r_list) < to_checkout:
        r_list = r_list + n_list
    checkouted_len = to_checkout if to_checkout < len(r_list) else len(r_list) 
    checkout = r_list[:checkouted_len]
    print("nvmes_checkedout:", " ".join(checkout))
    if args.single:
        if args.socket.upper() == "ANY":
            _running_ini["single_nvmes"] =  r_list[checkouted_len:]
        else:
           _running_ini["nodes_nvmes"][args.socket]=  r_list[checkouted_len:]
    LogOut("checkout:", checkout)
    LogOut(_running_ini)
    save_json(_nvme_pickup_running["running_ini"],_running_ini)
    return r_list
    
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
    parser.add_argument('--randomly', type=str2bool,help='random or sequential', default= True)
    parser.add_argument('--socket', type=str,help='which sockets', default="0")#"ANY")
    parser.add_argument('--single', type=str2bool,help='singel nvmes or groups in same root portl', default= True)
    #parser.add_argument('--nu', type=str,help='the env shell file name', default='ALL')#'3')
    parser.add_argument('--nu', type=str,help='the env shell file name', default='15')


    args = parser.parse_args()
    print(args)    
    load_env()
    pickup()
    

        
