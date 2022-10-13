import time
import os
from pathlib import Path
import argparse
from Cmd import  Q_Cmd, Q_Cmd_Ext
from utils import  save_array_2_xls, load_add_cfg
from os.path import exists
from pathlib import Path
#precommand:
"""
    
"""

_sys_infor_running = {
                    "cmd_ws": "./",
                    "cfg_file": "sys_info_cfg.json", 
                    "output_xls":"./_result/Sys_info.xls", 
                    "output_sheet":"sys_info", 
}

_sys_infor_cmd_ = []
_sys_infor_cmd_default_= [
                 {"name": "bios_info",  "cmd":"dmidecode -t 0", "expected": ["Version: "] },                  
                 {"name":  "OS",  "cmd":"lsb_release -a 2>&1 |  grep Description",  "expected": ["Description"]},                  
                 {"name":  "nvme_list" ,   "cmd":"nvme list",   "expected": ["/dev/"]  },                 
                 {"name": "pcicrawler_t",   "cmd": "pcicrawler -t", "expected": [":"]  } 
]


_sys_info_settings = {
    "cmd_run_error_msg": "Error when running ", 

}

def Collect_Sys_Info(writer=None):
    if not exists(_sys_infor_running["cfg_file"]):
        print(_sys_infor_running["cfg_file"], "does not exist. ")
        exit(1)
    s_cfg = load_add_cfg(_sys_infor_running["cfg_file"])
    print(s_cfg)
    if not s_cfg is  None:
        _sys_infor_cmd_=s_cfg["sys_info_cmd"]
    else:
        print("Fail on loading ",_sys_infor_running["cfg_file"])
        _sys_infor_cmd_=_sys_infor_cmd_default_
        
    for cfg in _sys_infor_cmd_:
        expected = cfg["expected"] if "expected" in cfg.keys() else []
        r = Q_Cmd_Ext(cfg['cmd'], expected) 
        cfg["result"] = r
    a_r = []
    print("")
    print("")
    for cfg in _sys_infor_cmd_:
        c = cfg["name"] if "name" in cfg.keys() else cfg['cmd']
        srs = "\n".join(cfg["result"])
        print(c + "\n",srs)
        ar =  [c, srs]
        a_r.append(ar)
    header=["item", "data"]
    p= os.path.dirname(os.path.realpath(_sys_infor_running["output_xls"]))
    ps = "mkdir -p " + p + " >/dev/null"
    Q_Cmd(ps)
    ps = "rm -f " + _sys_infor_running["output_xls"] + " >/dev/null"
    Q_Cmd(ps)
    save_array_2_xls(_sys_infor_running["output_xls"], _sys_infor_running["output_sheet"], a_r, header,writer=writer)
    print("System info is saved to ",  _sys_infor_running["output_xls"], "sheet", _sys_infor_running["output_sheet"])


if __name__ == '__main__':
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--cfg_file', type=str,help='Sys info config file in json format.', default=_sys_infor_running["cfg_file"])

    args = parser.parse_args()
    print(args)    
    _sys_infor_running["cfg_file"]=args.cfg_file
    Collect_Sys_Info()
    

        
