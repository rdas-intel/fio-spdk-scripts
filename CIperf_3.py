
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

from Cmd import C_CMD, Q_Cmd, T_Q_CMD, __ERROR_FLOAT, __ERROR_INT, Q_Remote_Cmd #, CMD_Group, Export_Env, 
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
"""



with_log = True
#with_log = False
def LogOut(s=""):
    if with_log == False:
        return
    print(s)

IPerf_Running = {
    "ssh_ip": "10.112.227.155",
    #"ssh_ip": "10.239.85.52",
    #"ssh_ip": "192.168.122.61",
    "local_local_ips_cmd": {},
    "remote_local_ips_started": {},
    "report_interval": 20,
    "test_time":1,
    "parallel":2,
    "iperf_cmd":"/usr/bin/iperf",
    "result_folder":"",
    
}
iperf_server_cmd_cfg = {
     "cmd": IPerf_Running["iperf_cmd"] 
}
iperf_client_cmd_cfg = {
     "cmd": IPerf_Running["iperf_cmd"] ,
     "expected": ["sender", "receiver"]
}
xls_iperf_keys_offset = {
}

IPerf_Para = {
               #"work_type": "iperf",  #only for iperf type
               "case": 1,
               "server_ip": "",
               "client_ip":	"",              
               "bi-direction": True,              
}
IPerf_Para_Optional = {
               "parallel": 2,
               "report_interval":	 10,         
               "test_time":	 60,         
}
#For result itemes in xls: sender_bw_1	recv_bw_1	retry_1
IPerf_Result_Items = {'Retr': "retry_", 'sender': "sender_bw_", 'receiver': "receiver_bw_"}

IPerf_Para_With_Space = [ "numa_ctl", "additional_para"]

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
            v = v.replace(" ", "#") 
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
                
        iperf_p[key] = v
    iperf_p["row"] =  row + 1 #+ row_offset
    iperf_p["work_type"] = work_type
    #print(iperf_p)
    return  iperf_p
    
def New_Iperf_Cmd(para):
    bi_direction=True if para["bi-direction"]=="1" else False
    try:
        t = int(para["test_time"])
    except:
        t = IPerf_Running["test_time"]
    try:
        report_interval = int(para["test_time"])
    except:
        report_interval = int(t/30) *  10 if int(t/3) <= 60 else 60
    report_interval = report_interval if report_interval <= 60 else 60
    report_interval = report_interval if report_interval  >0  else IPerf_Running["report_interval"]
    ci_ = C_IPerf(local_ip = para["server_ip"], remote_ip = para["client_ip"], bi_direction=bi_direction, xls_row=para["row"],test_time=t, parallel=para["parallel"], report_interval=report_interval)
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
    update_result_(results["local_client"], "1")
    update_result_(results["remote_client"], "2")
    LogOut("Iperf_Update_Result_2_Xls " + str(results))
    
    if results["local_client"]  is None or results["remote_client"]  is None :
        return
    bw_1 = float(results["local_client"]["sender"]) if results["local_client"] is not None else float(0.0)
    bw_2 = float(results["remote_client"]["sender"]) if results["remote_client"] is not None else float(0.0)
    bw = bw_1 + bw_2
    
    both_bw_c = xls_iperf_keys_offset["both_bw"]
    Update_Result_2_Xls(xls_sheet, row, both_bw_c, bw)

    retry_1 = float(results["local_client"]["Retr"]) if results["local_client"] is not None else float(0.0)
    retry_2 = float(results["remote_client"]["Retr"]) if results["remote_client"] is not None else float(0.0)
    retry = retry_1 + retry_2

    both_retry_c = xls_iperf_keys_offset["both_retry"]
    Update_Result_2_Xls(xls_sheet, row, both_retry_c, retry)
    
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
        
def Start_Iperf_Cmds(iperf_cmds):
    if len(iperf_cmds) == 0:
        return
    for iperf in iperf_cmds:
        if iperf.bi_direction:
            iperf.iperf_start_bi_direction_no_block()
        else:
            iperf.iperf_start_one_direction_no_block()
            
    localtime = time.asctime( time.localtime(time.time()) )
    print("     \t==>Iperf case started at", localtime)

def Wait_Iperf_Cmds_Done(iperf_cmds):
    if len(iperf_cmds) == 0:
        return

    for iperf in iperf_cmds:
        if iperf.bi_direction:
            iperf.iperf_wait_bi_direction_done()
        else:
            iperf.iperf_wait_one_direction_done()
    localtime = time.asctime( time.localtime(time.time()) )
    print("     \t==>Iperf case done at", localtime)
    
class C_IPerf():
    def __init__(self, local_ip, remote_ip, ssh_ip=IPerf_Running["ssh_ip"], test_time=IPerf_Running["test_time"], parallel=IPerf_Running["parallel"], bi_direction=True, xls_row=-1, report_interval=-1):      
        self.remote_ip = remote_ip
        self.local_ip = local_ip
        self.ssh_ip = ssh_ip
        self.test_time = test_time
        self.report_interval= IPerf_Running["report_interval"] if report_interval == -1 else report_interval
        self.parallel = parallel
        self.ipv6 = True if ":" in local_ip else False
        self.s_cmd = None #for server cmd
        self.c_cmd = None #for client cmd
        self.remote_client = None
        self.log_file = None
        self.bi_direction = bi_direction
        self.start_time = None
        self.end = None
        self.log_file_name = ""
        self.log_file = None
        self.result_json_file = None
        if xls_row > 0:
            self.log_file_name = IPerf_Running["result_folder"] + "row_" + str(xls_row)
            

    #for local server, remote client
    def start_local_server(self):
        if self.s_cmd is None:
            self.s_cmd = C_CMD(iperf_server_cmd_cfg, block_mode=False)
            s_para = "-B " +  self.local_ip + " -s" + " -i " + str(self.report_interval)
            self.s_cmd.cmd_exe(paras=s_para)
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
        LogOut(c_cmd_s)
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
    def start_remote_server(self):
        LogOut("start_remote_server")
        if self.remote_ip in IPerf_Running["remote_local_ips_started"].keys():
            LogOut("Remote server has already been started. No need to run again.")
            return
        session_name =  self.remote_ip.replace(".", "_") if not self.ipv6 else self.remote_ip.replace(":", "_")
        #print(session_name)
        iperf_cmd_s = IPerf_Running["iperf_cmd"] + " -B " + self.remote_ip + " -s" + " -i " + str(self.report_interval)
        r_s = "tmux new-session -d -s " + session_name + ' "' + iperf_cmd_s + '"' 
        LogOut(self.ssh_ip + " " + r_s)
        Q_Remote_Cmd(self.ssh_ip, r_s)
        LogOut("====>remote_server started " + r_s)
        IPerf_Running["remote_local_ips_started"][self.remote_ip] = True
        
    def stop_remote_server(self):
        Stop_remote_iperf_server(self.ssh_ip, self.remote_ip)

    def run_local_client(self, block=True):
        iperf_client_para_s = " -t " + str(self.test_time) + " -P " + str(self.parallel) + " -i " + str(self.report_interval) 
        iperf_client_para_s += " -fg" # for Gbits/sec
        iperf_client_para_s += " -V" if self.ipv6 else ""
        iperf_client_para_s =  " -c " + self.remote_ip + " -B " + self.local_ip + iperf_client_para_s 

        if block:
            cmd_s =  iperf_client_cmd_cfg["cmd"] + iperf_client_para_s
            LogOut("run_local_client:" + cmd_s)
            r = Q_Cmd(cmd_s)
            return r
        else:
            local_client_cmd = {"cmd": IPerf_Running["iperf_cmd"] ,"expected": iperf_client_cmd_cfg["expected"]}
            self.c_cmd = C_CMD(local_client_cmd, block_mode=False)
            LogOut("run_local_client noblock:" + iperf_client_para_s)
            self.c_cmd.cmd_exe(paras=iperf_client_para_s)
            return None
    def get_local_client_result(self):
        if self.c_cmd is None:
           return None
        _, r = self.c_cmd.check_output()
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


    def iperf_start_one_direction_no_block(self):
        self.start_remote_server()
        self.run_local_client(block=False)
        
    def iperf_wait_one_direction_done(self,  exit_server_when_done=True):
        r = self.get_local_client_result()
        p_result_local = self.parsing_result(r)
        #print(pr)
        full_result = {"local_client": p_result_local, "remote_client":None}
        self.dump_result(full_result)

        if exit_server_when_done:
            self.stop_remote_server()    

        
    def iperf_start_bi_direction_no_block(self):
        LogOut("iperf_start_bi_direction_no_block")
        self.start_remote_server()
        self.run_local_client(block=False)
        exit(1)
        self.start_local_server()
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
        #[  4]   0.00-1.00   sec  2.09 GBytes  18.0 Gbits/sec  3150             sender
        #[  4]   0.00-1.00   sec  2.09 GBytes  18.0 Gbits/sec                  receiver
        #[SUM]   0.00-300.00 sec  0.00 (null)s  41.4 Gbits/sec  29686             sender
        #[SUM]   0.00-300.00 sec  0.00 (null)s  41.4 Gbits/sec                  receiver
        
        parsed_r = {}
        new_r = []
        if len(result) > 2:
            for line in result:
                if "SUM" in line:
                    new_r.append(line)
            result=new_r
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
        


