import time
import os
from pathlib import Path
import argparse
from Cmd import C_CMD, Q_Cmd, Q_Cmd_Ext, T_Q_CMD, Tmux_CMD, Q_Remote_Cmd
from utils import get_statistics, save_array_2_xls
from os.path import exists

#precommand:
"""
    fw for intel 810e
        mkdir -p  /lib/firmware/updates/intel/ice/ddp/
        cp $e810_driver_folder/ice_comms-1.3.30.0.pkg  /lib/firmware/updates/intel/ice/ddp/
        cp $e810_driver_folder/ice.pkg /lib/firmware/updates/intel/ice/ddp/


    huge_page clean:
        dpdk_hugepage_reset.sh
        modprobe ice
        modprobe vfio
        modprobe vfio-pci
        dpdk_device_bind_vfio-pci.sh 38:00.0 38:00.1

    dpdk build:

    trex:

    #Set up dpdk devices and update /etc/trex_cfg.yaml before running
    - bind devices to dpdk in both side 
        SPR1:
            $WS_ROOT/22_ww07_spr_1_trex_nic_bind_98_9b_a8_ab_b8_bb.sh
             Unbind:   $WS_ROOT/22_ww07_spr_1_trex_nic_unbind_98_9b_a8_ab_b8_bb.sh 
        SPR2:
            $WS_ROOT/spr_2_ww07_trex_nic_bind.sh
            cp
    - cp the cfg.yaml to /etc/trex.cfg or
        try trex server in spr1,  then stop, 
            cd $WS_ROOT ; trex_server.sh spr1_trex_ww14_6_ports.yaml  
        spr2:  
            cd $WS_ROOT ; spr2_trex_s_ww07_6_ports.sh
    - update remote_ip  remote_server_cmd, remote_client_cmd
    - run : 
            cd $WS_ROOT/Storage; rm -rf ./_result ; python CTrex_DPDK.py
    
    
"""
_args = None

t_remote = None

Trex_env_settings = {
    "PYTHONPATH": "automation/trex_control_plane/interactive",
    
}

Trex_Remote_Setting = {
    "remote_ip":"10.112.227.150",
    #"remote_server_cmd":"/media/data/ml/storage_io/spr2_trex_s_ww01_6_ports.sh",
    "remote_server_cmd":"/media/data/ml/storage_io/spr2_trex_s_ww07_6_ports.sh",
    "remote_client_cmd":"/media/data/ml/storage_io/spr2_trex_c.sh",
    "remote_folder":"/media/data/ml/storage_io",
    "wait_time_server":10,
    "wait_time_client":2,
    }

Trex_Running = {
    #"work_folder": "/media/data/ml/storage_io/trex/v2.89", #for BA
    "work_folder": "/media/data/ml/storage_io/trex/v2.91", #for BA
    #"work_folder": "/media/data/ml/storage_io/trex/trex-core/scripts",  #for SHA
    "local_power_monitor_cmds": ["sys_start_power_monitor.sh", "sys_stop_power_monitor.sh"],
    "naming_with_no": True, 
    #"trex_test_time": 120,
    "trex_test_time": 200,
    #"trex_test_time": 20,
    "trex_warming_up_time": 20,
    #"trex_warming_up_time": 2,
    "trex_shutdown_time": 20,
    #"trex_shutdown_time": 2,
    #"client_bench": "start -f stl/bench.py  -m 100%  -t size=",
    "client_bench": "start --force -m 100% -f stl/bench.py -t  size=",
    "client_bench_size": 1000,
    "server_cmd": "./t-rex-64 -i   --queue-drop -c ",
    "server_core": 24,
    "result_folder":os.path.abspath(os.path.dirname(__file__)) + "/_result/",
    "with_remote_server": True,
    #"with_remote_server": False,
}

class Trex_Remote():
    def __init__(self, name="Trex_remote", settings = {}, auto_delete=True):
        self.name = name
        self.server_name = name + "_server"
        self.client_name = name + "_client"
        self.server = None
        self.auto_delete = auto_delete
        self.cfg = Trex_Remote_Setting.copy() if settings=={} else settings.copy()
        self.server_stopped = True
        self.client_stopped = True

    def __del__(self):
        pass
        #if self.auto_delete:
            #self.stop_client()
            #self.stop_server()
    def start_server(self):
        self.server = Tmux_CMD(self.server_name, ssh_ip=self.cfg["remote_ip"],auto_delete=False,silent_mode=True)
        self.server.send_cmd(self.cfg["remote_server_cmd"])
        time.sleep(5)
        self.server_stopped = False
        #time.sleep(self.cfg["wait_time_server"])
    def stop_server(self):
        if not self.server_stopped:
            self.server.exe_remote_cmds(["C-c "],self.cfg["remote_folder"])
            time.sleep(3)
            self.server.stop()
            self.server_stopped = True

    def start_client(self, pkt_size=0):
        self.client = Tmux_CMD(self.client_name, ssh_ip=self.cfg["remote_ip"],auto_delete=False,silent_mode=True)
        self.client.send_cmd(self.cfg["remote_client_cmd"])
        time.sleep(self.cfg["wait_time_client"])
        if pkt_size == 0:
            pkt_size = Trex_Running["client_bench_size"]
        bench_cmd = Trex_Running["client_bench"] + str(pkt_size )
        self.client.exe_remote_cmds([bench_cmd],self.cfg["remote_folder"])
        self.client_stopped = False

        
    def stop_client(self):
        if not self.client_stopped:
            self.client.exe_remote_cmds(["stop"],self.cfg["remote_folder"])
            time.sleep(1)
            self.client.exe_remote_cmds(["C-c "],self.cfg["remote_folder"])
            time.sleep(3)
            self.client.stop()
            self.client_stopped = True
           
    def start(self,pkt_size=0):
        self.start_server()
        self.start_client(pkt_size=pkt_size)
    def stop(self):
        self.stop_client()
        self.stop_server()


class Trex_Client():
    def __init__(self, name, auto_delete=True):
        self.name = name
        self.auto_delete = auto_delete
        self.tmux = Tmux_CMD(name, auto_delete=False)
        self.tmux.export_env(Trex_env_settings)
        self.start()
    def __del__(self):
        if self.auto_delete:
            self.stop()
            
    def start_bench(self, pkt_size=0):
        if pkt_size == 0:
            pkt_size = Trex_Running["client_bench_size"]
        bench_cmd = Trex_Running["client_bench"] + str(pkt_size )
        self.tmux.send_cmd(bench_cmd)
        
    def stop_bench(self):
        self.tmux.send_cmd("stop")
            
    def start(self):
        self.tmux.send_cmd("cd " + Trex_Running["work_folder"])
        self.tmux.send_cmd("python -m trex.console.trex_console ")

    def stop(self):
        self.tmux.send_cmd("quit ")
        self.tmux.stop()
        
class Trex_Server():
    def __init__(self, name, auto_delete=True, core_num=0, with_log=False, log_file=""):
        self.name = name
        self.core_num = core_num
        if core_num == 0:
            self.core_num = Trex_Running["server_core"]
        self.auto_delete = auto_delete
        self.with_log = with_log
        self.tmux = Tmux_CMD(name, auto_delete=False)
        self.tmux.export_env(Trex_env_settings)
        self.start(core_num=self.core_num, log_file=log_file)
        
    def __del__(self):
        if self.auto_delete:
            self.stop()
            
    def start_bench(self, core_num=0, log_file=""):
        if core_num != 0:
            self.core_num = core_num
        bench_cmd = Trex_Running["server_cmd"] + str(self.core_num )
        if self.with_log:
            if log_file == "":
                log_file = Trex_Running["result_folder"] + self.name + "_log.txt"
            self.tmux.send_cmd("rm -rf " + log_file + " > dev/null")
            bench_cmd += " |& tee " +  log_file
        self.tmux.send_cmd(bench_cmd)
        
            
    def start(self,core_num=0, log_file=""):
        self.tmux.send_cmd("cd " + Trex_Running["work_folder"])
        self.start_bench(core_num, log_file=log_file)

    def stop(self):
        self.tmux.send_special_cmd("C-c ")
        self.tmux.stop()
        
def Trex_Try():
    print("Trex_Try")
    #trex_c.stop()
    trex_s = Trex_Server("trex_ss", auto_delete=True, with_log=True)
    time.sleep(5)
    trex_c = Trex_Client("trex_client", auto_delete=True)
    trex_c.start_bench()
    time.sleep(60)

def Trex_Single_Run(duration_seconds=60, pkt_size=512, cn=16, log_file=""):
    #print("Trex_Single_Run, pkt_size ", pkt_size, "core_num:", cn)
    #trex_c.stop()
    def stop_power_monitor():
        if len(Trex_Running["local_power_monitor_cmds"]) > 1:
            print("Stopping local_power_monitoring")    
            if Trex_Running["local_power_monitor_cmds"][1] != "":
                r = Q_Cmd(Trex_Running["local_power_monitor_cmds"][1])
    try:
        if len(Trex_Running["local_power_monitor_cmds"]) != 0:
            if Trex_Running["local_power_monitor_cmds"][0] != "":
                #power_monitor_log_file = IPerf_Running["result_folder"]  + "row_" + str(iperf_cmds[0]. xls_row) + "_rapl.log"
                power_monitor_log_file = log_file + "_rapl.log"
                print("Starting local_power_monitoring, saving to", power_monitor_log_file)
                r = Q_Cmd(Trex_Running["local_power_monitor_cmds"][0] + " " + power_monitor_log_file)
                #print(r)
        if Trex_Running["with_remote_server"]:
            t_remote = Trex_Remote()
            t_remote.start_server()
        trex_s = Trex_Server("trex_ss", auto_delete=True, core_num=cn, with_log=True, log_file=log_file)
        time.sleep(5)
        if Trex_Running["with_remote_server"]:
            t_remote.start_client(pkt_size=pkt_size)
        trex_c = Trex_Client("trex_client", auto_delete=True)
        trex_c.start_bench(pkt_size=pkt_size)
        time.sleep(duration_seconds)    

        if Trex_Running["with_remote_server"]:
            t_remote.stop()
            #t_remote = None
    except KeyboardInterrupt:
        print("Keyboard interrputed")
        stop_power_monitor();
        if Trex_Running["with_remote_server"]:
            print("Stopping Remote server!")
            t_remote.stop()
            time.sleep(2)
        exit(1)
    stop_power_monitor();

    #trex_s.stop()
def Trex_Parsing_Single_Result(log_fn, warming_up=Trex_Running["trex_warming_up_time"], shutdown=Trex_Running["trex_shutdown_time"]):
    if not exists(log_fn):
        print("Trex_Parsing_Single_Result error, file does not exists", log_fn)
        return None
    txl_cmd = "cat " + log_fn + " | grep Total-Tx | awk  '{print $3}' "
    txl = Q_Cmd_Ext(txl_cmd)
    txl_gm_cmd = "cat " + log_fn + " | grep Total-Tx | awk  '{print $4}' "
    txlgm = Q_Cmd_Ext(txl_gm_cmd)
    
    rxl_cmd = "cat " + log_fn + " | grep Total-Rx | awk  '{print $3}' "
    rxl = Q_Cmd_Ext(rxl_cmd)
    rxl_gm_cmd = "cat " + log_fn + " | grep Total-Rx | awk  '{print $4}' "
    rxlgm = Q_Cmd_Ext(rxl_gm_cmd)

    cpu_utiization_cmd = "cat " + log_fn + " | grep 'Cpu Utilization :' | awk  '{print  $4, $6, $7}' "
    cpu_utilization_l = Q_Cmd_Ext(cpu_utiization_cmd)

    _least = warming_up + shutdown
    
    def cpu_utilization_parsing(nvl):
        if len(nvl) < _least:
            print("Error on the length of result, ", len(nvl), "warming up: ", warming_up, "shutdown:", shutdown)
            exit(1)
        n1 = nvl[warming_up:]     
        n2 = n1[:-shutdown]     
        c_utilization = []
        t_per_core = []
        for v in n2:
            ev = v.split()
            if len(ev) < 2:
                print("cpu_utilization_parsing: Error on the ", len(ev), ev)
                exit(1)
            c = float(ev[0])
            t = float(ev[1])
            if ev[2] == 'Mb/core':
                t = t / 1024.0
            elif ev[2] == 'Kb/core':
                t = t / 1024.0 / 1024.0
            elif ev[2] == 'b/core':
                t = t / 1024.0 / 1024.0 / 1024.0
            c_utilization.append(c)
            t_per_core.append(t)
        return c_utilization, t_per_core
            

    def throughput_v(v_, t):
        v = float(v_)
        if t == "bps":
            v = v / 1024.0 / 1024.0 / 1024.0
        elif t == "Kbps": # for Kbps?
            v = v / 1024.0 / 1024.0
        elif t != "Gbps": # for Mbps?
            v = v / 1024.0
        return v
          
    def v2f(vl, vgps):
        nvl = []
        try:
            idx = 0
            for tx in vl:
                v = throughput_v(tx, vgps[idx])
                nvl.append(v)
                idx = idx + 1
        except:
            print("Error on v2f", vl)
        
        if len(nvl) < _least:
            print("Error on the length of result, ", len(nvl), "warming up: ", warming_up, "shutdown:", shutdown)
            exit(1)
        n1 = nvl[warming_up:]     
        n2 = n1[:-shutdown]     
        return nvl, n2

    tv, t2 = v2f(txl, txlgm)
    rv, r2 = v2f(rxl, rxlgm)
    cpu_u, throupth_per_core = cpu_utilization_parsing(cpu_utilization_l)
    
    tx = get_statistics(t2)
    rx = get_statistics(r2)
    cu = get_statistics(cpu_u)
    t_p_c = get_statistics(throupth_per_core)
    
    print("tx  _mean, std_v, _min, _max, p95", tx)
    print("rx  _mean, std_v, _min, _max, p95", rx)
    print("cpu_utilization   _mean, std_v, _min, _max, p95", cu)
    print("Gb/core   _mean, std_v, _min, _max, p95", t_p_c)
    return tx + rx + cu + t_p_c       

pkt_size_range = [128, 256, 512, 1024, 2048, 4000, 4096]
#pkt_size_range = [4096]
#core_num_range = [1, 2, 3, 4, 6, 8, 10, 12, 14, 16,18, 20, 22, 24]
#core_num_range = [1, 2, 3, 4, 6, 8, 10, 12, 14, 16]
core_num_range = [1, 2, 3, 4, 6, 8, 10, 12, 14]
#core_num_range = [16]
ext_fn = "trex_e810-c"

def Get_Trex_Result_FN(pkt_size, cn, no):
    if Trex_Running["naming_with_no"] :
        fn = ext_fn + "_no._" + str(no) + "_pkt_" + str(pkt_size) + "_c_" + str(cn) + "_log.txt"
    else:
        fn = ext_fn + "_" + "_pkt_" + str(pkt_size) + "_c_" + str(cn) + "_log.txt"
    log_fn = Trex_Running["result_folder"] + fn
    return log_fn, fn
    
def Parsing_Trex_Result():
    result_all = []
    no = 1
    for pkt_size in pkt_size_range:
        for cn in core_num_range:
            log_fn, fn = Get_Trex_Result_FN(pkt_size, cn, no)
            pr = Trex_Parsing_Single_Result(log_fn)
            if pr is not None:
                xr = [fn] + [pkt_size] +  [cn] +list(pr)
                result_all.append(xr)
                print(xr)
            no = no + 1
    #print(r)
    #df = pd.dataframe(array)
    result_file=Trex_Running["result_folder"] + Trex_Running['output_file_name'] 
    header = ["fn", "pkt_size", "core_num", "tx _mean(Gbps)", "tx_std_v(Gbps)", "tx_min(Gbps)", "tx_max(Gbps)", "tx_p95(Gbps)", \
                                                        "rx _mean(Gbps)", "rx_std_v(Gbps)", "rx_min(Gbps)", "rx_max(Gbps)", "rx_p95(Gbps)", \
                                                        "cpu_usage _mean(%)", "cpu_usage_std_v(%)", "cpu_usage_min(%)", "cpu_usage_max(%)", "cpu_usage_p95(%)", \
                                                        "Gb/core _mean", "Gb/core_std_v", "Gb/core_min", "Gb/core_max", "Gb/core_p95"]

    brief_header = ["core_num"]
    breif_items = ["tx(Gbps)",  "rx(Gbps)",  "cpu_usage(%)", "Gb/core"]

    for pkt_s in pkt_size_range:
        for item in breif_items:
            b_i = str(pkt_s) + "_" + item
            brief_header.append(b_i)
    #print(brief_header)

    def get_result_of_pkt_cn(all_rows, pkts, cn):
        for r_ in all_rows:
            if r_[1] == pkts and r_[2] == cn:
                return r_
        print("Not found in get_result_of_pkt_cn for ", pkts, cn)
        exit(1)

    brief_list = []
    for cn in core_num_range:
        b_r = [cn]
        for pkt_s in pkt_size_range:
            row = get_result_of_pkt_cn(result_all, pkt_s, cn)
            b_r.append(row[3])
            b_r.append(row[8])
            b_r.append(row[13])
            b_r.append(row[18])
        brief_list.append(b_r)

        
    writer = save_array_2_xls(result_file, ext_fn + "_detail", result_all, head=header, Final=False, writer=None)
    save_array_2_xls(result_file, ext_fn+ "_brief", brief_list, head=brief_header, Final=True, writer=writer)
    print("Result is saved to ", result_file)
    ls_result = "ls -lh " + result_file
    print(Q_Cmd(ls_result))
def Trex_Multiple_Run():

    duration = Trex_Running["trex_test_time"]
    r_c = "mkdir -p " + Trex_Running["result_folder"]
    Q_Cmd(r_c)
    total = len(pkt_size_range) * len(core_num_range)
    no = 1
    for pkt_size in pkt_size_range:
        for cn in core_num_range:
            if no >= _args.run_from:
                print("Trex_Single_Run, pkt_size ", pkt_size, "core_num:", cn, "   ", no, "of", total)
                log_fn, _ = Get_Trex_Result_FN(pkt_size, cn, no)
                Trex_Single_Run(duration_seconds = duration, pkt_size = pkt_size, cn = cn, log_file = log_fn)
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
    parser.add_argument('--with_power_monitor', type=str2bool,help='with power monitor', default=True)
    parser.add_argument('--intput_folder', type=str,help='intput_folder', default=Trex_Running["result_folder"])
    parser.add_argument('--output_file_name', type=str,help='output_file_name', default="./trex_result.xls")

    _args = parser.parse_args()
    print(_args)

    Trex_Running["result_folder"] = _args.intput_folder
    Trex_Running["output_file_name"] = _args.output_file_name
    
    if not _args.with_power_monitor:
        Trex_Running["local_power_monitor_cmds"] = []    
    if 0:
        t_remote = Trex_Remote()
        t_remote.start()
        time.sleep(10)
        t_remote.stop()
    
    
    #exit()
    if not _args.parsing_only:
        Trex_Multiple_Run()
    fn = "/media/data/ml/storage_io/Storage/_result/trex_e810-c_2048_20_log.txt"
    #Trex_Parsing_Single_Result(fn)
    Parsing_Trex_Result()
        
