import threading
from threading import Thread
import subprocess
import signal
import os
from os.path import exists
from pathlib import Path
from datetime import datetime
import time
import random
__ERROR_FLOAT=float(0.0000000001)
__ERROR_INT=int(0xffff)
#>/dev/null
#2>/dev/null
__local_host_="127.127.127.0"
# A remote ssh tmux 
#_with_detail_log=True

_with_detail_log=False
def Q_Remote_Tmux_Cmd(ssh_ip, session_name, cmd_str, silent_mode=False):
        r_s = "tmux new-session -d -s " + session_name + ' "' + cmd_str + '"' 
        Q_Remote_Cmd(ssh_ip, r_s)
        if not silent_mode:
            print(ssh_ip + " " + r_s)
def Q_Remote_Tmux_Stop(ssh_ip, session_name, silent_mode=False):
        r_s  = "tmux kill-session -t  " + session_name 
        Q_Remote_Cmd(ssh_ip, r_s)
        if not silent_mode:
            print(self.ssh_ip + " " + r_s)

def Q_Remote_Cmd_with_Paras(ssh_ip, cmd_str, silent_mode=False):
    if 1:
        actual_cmd = cmd_str.strip().split(" ")[4:-1]
        header =  " ".join(cmd_str.strip().split(" ")[:4])
        for s in actual_cmd:
            if s.count('"')%2 != 0:
                s = s.replace('"', '')
            s_cmd = header + " " + s 
            Real_Q_Remote_Cmd(ssh_ip, s_cmd)
            s_cmd = header + " " + "Space" 
            Real_Q_Remote_Cmd(ssh_ip, s_cmd)
        s_cmd = header + " " + "Enter" 
        return Real_Q_Remote_Cmd(ssh_ip, s_cmd)
def Real_Q_Remote_Cmd(ssh_ip, cmd_str, silent_mode=False, log_result=False):
    tmp_f="/tmp/q_remote_cmd.sh"
    if log_result:
        remote_log_f = "/tmp/q_resut.txt "
        result_s = "rm -f "+ remote_log_f + " 2>/dev/null"
        Q_Cmd(result_s)
        
        cmd_str = cmd_str + " |&  tee   "  + remote_log_f
    tmp_s="echo '" + cmd_str + "' > " + tmp_f + " 2>/dev/null"
    Q_Cmd(tmp_s)
    cmd="ssh -T " + ssh_ip + " < " + tmp_f
    #print("Q_Cmd", cmd)
    if silent_mode:
        cmd = cmd + " |&  tee  /tmp/tmp.txt " + " 2>/dev/null"
    #print(cmd)
    result=Q_Cmd(cmd)
    tmp_s="rm -f " + tmp_f # + " 2>/dev/null"
    Q_Cmd(tmp_s)

    if log_result:
        result_s = "scp " + ssh_ip + ":" + remote_log_f + "/tmp/"
        Q_Cmd(result_s)
        return remote_log_f
    return result

def check_expected(r, expected):
    r_t = []
    for l in r:
        if l is not "":
            l = l.replace("\t", "")
            r_t.append(l)
    r_e = []
    if expected != []:
        for l in r_t:
            for e in expected:
                if e in l:
                    r_e.append(l)
                    break
        r_t = r_e           
    return r_t
        
# A remote exe with ssh
def Q_Remote_Cmd_Ext(ssh_ip, cmd_str, silent_mode=False, expected=[]):
    if "send-keys" in cmd_str and len(cmd_str.strip().split(" ")) > 6:
        r = Q_Remote_Cmd_with_Paras(ssh_ip, cmd_str, silent_mode=silent_mode)
        return r
    else:
        r = Real_Q_Remote_Cmd(ssh_ip, cmd_str, silent_mode=silent_mode, log_result=True)
        if expected != []:
            es = "|".join(expected)
            cmd_s = "grep -E '" + es + "' " + r 
        else:
            cmd_s = "cat  " + r 
        r = Q_Cmd(cmd_s)
        
        return (r.split("\n"))
     
def Q_Remote_Cmd(ssh_ip, cmd_str, silent_mode=False, log_result=False):
    if "send-keys" in cmd_str and len(cmd_str.strip().split(" ")) > 6:
        return Q_Remote_Cmd_with_Paras(ssh_ip, cmd_str, silent_mode=silent_mode)
    #ssh -t     
    return Real_Q_Remote_Cmd(ssh_ip, cmd_str, silent_mode=silent_mode, log_result=log_result)
def Q_Remote_S_Result():
    tmp_s="cat  /tmp/tmp.txt "
    return Q_Cmd_Ext(tmp_s)
    


# A simple shell command interface, return with stdout contents
def Q_Cmd(cmd_str):
    #print("Q_Cmd:",cmd_str)
    if _with_detail_log:
        print(cmd_str)
    cmd = os.popen(cmd_str)
    content=cmd.read()
    cmd.close()
    return content
def Q_Cmd_Ext(cmd_str, expected=[]):
    r = Q_Cmd(cmd_str).split("\n")
    return check_expected(r, expected)
    '''
    r_t = []
    for l in r:
        if l is not "":
            r_t.append(l.replace("\t", ""))
    r_e = []
    if expected != []:
        for l in r_t:
            for e in expected:
                if e in l:
                    r_e.append(l)
                    break
        r_t = r_e           
    return r_t
'''
cmd_running_={
    "sn" : 0,
}
def get_uni_fn():
     t = time.time()
     #ts=str(int(t)+random.randint(1,1000))
     ts=str(int(t))+"_" + str(cmd_running_["sn"]) 
     cmd_running_["sn"] = cmd_running_["sn"] + 1
     return ts
    
# Command under tmux
class Tmux_CMD():
    def __init__(self, name, start_cmd_str="", close_after_run=False, overwright=True, auto_delete=True, ssh_ip="", silent_mode=False):
        self.name = name
        self.auto_delete = auto_delete
        self.ssh_ip = ssh_ip
        self.silent_mode = silent_mode
        s_cmd = "tmux new-session -d -s " + self.name
        if self.ssh_ip == "":
            self.ssh_ip = "127.127.127.0" 
            r = Q_Cmd(s_cmd)
        else:
            r = Q_Remote_Cmd(self.ssh_ip, s_cmd,self.silent_mode)
        if not self.silent_mode and r != "":
            print(r)

    def __del__(self):
        if self.auto_delete:
            self.stop()
            
    def export_env(self, envs):
        for e in envs.keys():
            env_s = "export " + e + "=" + envs[e]
            self.send_cmd(env_s)
            
    def is_exist(self):
        s_cmd = "tmux has-session -t  " + self.name
        r = Q_Cmd(s_cmd) if self.ssh_ip == "" else Q_Remote_Cmd(self.ssh_ip, s_cmd,self.silent_mode)
        if not self.silent_mode and r != "":
            print(r)

    def send_cmd(self, cmd_str):
        s_cmd = "tmux send-keys -t " + '"' +self.name +  ":0" + '"' + " " + '"' +  cmd_str + '"' + " Enter "
        print("ip:", self.ssh_ip, "cmd:", s_cmd)
        r = Q_Cmd(s_cmd)  if self.ssh_ip == "127.127.127.0"  else Q_Remote_Cmd(self.ssh_ip, s_cmd, self.silent_mode)
        if not self.silent_mode and r != "":
            print(r)
        return r
    def exe_remote_cmd(self, cmd, remote_folder="/tmp", s_name=""):
        if s_name == "":
            s_name = self.name
        #print("===============exe_remote_cmd>", cmd)
        return self.exe_remote_cmds([cmd], remote_folder="/tmp", s_name=s_name)

    def exe_remote_cmds(self, cmds, remote_folder="/tmp", s_name=""):
        if s_name == "":
            s_name = self.name
        ts=get_uni_fn()
        #tmp_sh_file= "/tmp/tmp_session.sh"
        tmp_sh_file= "/tmp/"+ts+"_session.sh"
        with open(tmp_sh_file, "w") as f:
            for cmd_str in cmds:
                xx_cmd = "tmux send-keys -t " + '"' + s_name +  ":0" + '"' + " " + '"' +  cmd_str + '"' + " Enter " + "\n"
                if _with_detail_log:
                    print("wrinting to file ",tmp_sh_file,  xx_cmd)
                f.write(xx_cmd)
            f.close()
        q_s = "chmod +x " + tmp_sh_file
        r = Q_Cmd(q_s)  
        #q_s = "cat " + tmp_sh_file
        #r = Q_Cmd(q_s)  
        scp_cmd = "scp -r " + tmp_sh_file + " " + self.ssh_ip + ":" +  remote_folder  
        #print(scp_cmd)
        r = Q_Cmd(scp_cmd)  
        if not self.silent_mode and r != "":
            print(r)
        #s_cmd = remote_folder+ "/tmp_session.sh"  
        s_cmd = remote_folder+ "/" + ts+"_session.sh"
        r = Q_Remote_Cmd(self.ssh_ip, s_cmd, self.silent_mode)
        s_cmd = "rm -f  "+tmp_sh_file + " 2>/dev/null"
        Q_Cmd(s_cmd) 
        return r

    def send_Ctrl_C_stop(self, sleep_time=0):
        self.send_special_cmd("C-c ")
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.stop()    
    def send_special_cmd(self, cmd_str, s_name=""):
        if s_name == "":
            s_name = self.name
        s_cmd = "tmux send-keys -t " + '"' + s_name +  ":0" + '"'+  " " + cmd_str  + " Enter "
        r = Q_Cmd(s_cmd) if self.ssh_ip == "" else Q_Remote_Cmd(self.ssh_ip, s_cmd,self.silent_mode)
        if not self.silent_mode and r != "":
            print(r)

    def send_cmds(self, cmd_str_list):
        pass
        
    def send_cmd_get_output(self, cmd_str):
        pass
        
    def send_cmds_get_output(self, cmd_str_list):
        pass

    def stop(self, s_name=""):
        if s_name == "":
            s_name = self.name
        s_cmd = "tmux kill-session -t  " + s_name
        r = Q_Cmd(s_cmd) if self.ssh_ip == "" else Q_Remote_Cmd(self.ssh_ip, s_cmd,self.silent_mode)
        if not self.silent_mode and r != "":
            print(r)
        
# Run a simple shell command in a single thread
class T_Q_CMD_V1():
    def __init__(self, cmd_str):
        self.thread = threading.Thread(target=Q_Cmd, args=[cmd_str])
        self.thread.start()
    def wait_till_finish(self):
        self.thread.join()
        return None

class T_Q_CMD(Thread):
    def __init__(self, cmd_str, start_to_run=True, expected=None, show_all=False):
        super(T_Q_CMD, self).__init__()
        self.func = Q_Cmd
        self.args=[cmd_str]
        self.show_all=show_all
        self.expected=expected
        
        if start_to_run:
            self.start()
    def run(self):
        self.start()
    def run(self):
        self.result = self.func(*self.args)        
    def get_result(self):
        try:
            return self.result
        except Exception:
            return None
    def stop(self, expected=None):
        pass
    def wait_till_finish(self, expected=None):
        print("Waiting...")
        self.join()
        result=self.get_result()
        if self.show_all:
            print(result)
        if expected is not None:
            self.expected = self.expected
        if self.expected is None:
            return result
        filter_result=[]
        result=result.split("\n")
        for line in result:
            for expected_str in self.expected:
                if expected_str in line:
                    expected_found = True
                    filter_result.append(line)   
        return filter_result

# Export env_settings dictory as shell env variants with "ENV_" added to each variant name 
def Export_Env(env_settings):
    ENV_ ="ENV_"
    for key in env_settings.keys():
        env_key = ENV_ + key
        os.environ[env_key] = str(env_settings[key])

# Shell command class
class C_CMD():
    def __init__(self, cfg, simulation = False, show_all=False, bash_added=False, dos_shell=False, block_mode = True, extra_paras={}, process_extra_paras=None, remote_server=None, sys_cmd=False):      
        self.cfg = cfg
        self.cfg["cmd"] = self.cfg["cmd"].strip()
        self.show_all = show_all
        self.bash_added = bash_added
        self.simulate_mode = simulation
        self.dos_shell_added = dos_shell
        self.block_mode = block_mode
        self.extra_paras = extra_paras
        self.process_extra_paras = process_extra_paras
        self.comand_s = ""
        if "default_para" in self.cfg.keys():
            self.default_para=  self.cfg["default_para"]
        else:
            self.default_para = None
        
        self.subprocess = None
        #self.returncode = p.returncode
        cmd_file = Path(self.cfg["cmd"])
        
        if sys_cmd is not True and cmd_file.exists() is not True:       
            print("Error: ", self.cfg["cmd"], "does not exist")
            exit(1)
            
    def update_cmd(self, cmd):
        self.cfg["cmd"] = cmd.strip()     
    
    def os_call(self, para = None):
        s = self.cfg["cmd"] + " " + para
        os.system(s)

    # check if the command is finished or not
    def finished(self):
        return self.subprocess.poll() is not None
        
    # block till finish 
    def wait_for_finished(self):
        return self.subprocess.wait()
        
    # Stop running cmd by sending Ctrl + C
    def stop(self):
        return self.subprocess.send_signal(signal.SIGINT)
        
    def check_output(self, print_expected=True):
        out_put_line=[]
        p = self.subprocess
        self.wait_for_finished()
        for line in iter(p.stdout.readline, ""):
            o_l = line.replace('\n', '').replace('\r', '')  
            if self.show_all:
                print (o_l)     #for info in p.communicate():
            out_put_line.append(o_l)
        expected_v = None
        if "expected" in self.cfg.keys():
            expected_v = self.cfg["expected"]
            
        expected_error_v = None
        if "expected_error" in self.cfg.keys():
            expected_error_v = self.cfg["expected_error"]    
        result = []
        if 1:
            #print("Checking expected_v: {}".format(str(expected_v)))
            expected_found = False
            #for line in p.stdout.readlines():        
            for line in out_put_line:        
                #if self.show_all:
                #    print(line)
                if expected_v is not None:
                    for expected_line in expected_v:
                        if expected_line in line:
                            expected_found = True
                            result.append(line)
            if expected_found:
                if print_expected:
                    print("expected check, expected_v {} ==> {}".format(str(expected_v), str(result)))
            else:
                print("No expected_v:{}, Not found".format(str(expected_v)))
                    
        return expected_found, result    

    # run command, block till finish
    def cmd_exe(self, paras = None, simulation=None, print_expected=True):
        if simulation is not None:
            self.simulate_mode= simulation
            
        command =[self.cfg["cmd"]]
        if self.default_para is not None:
            command = command + str(self.default_para).split(" ") 

        if paras is not None:
            command =  command + str(paras).split(" ")
                   
        #print(command)
        self.comand_s = " ".join(command)
        if self.bash_added:
            cmd_cb = ["bash"] +  command
        else:
            if self.dos_shell_added:
                cmd_cb = ["cmd", "/c"] +  command
            else:
                cmd_cb = command         
           
        print(self.comand_s)

        # for simulation
        if self.simulate_mode:
            error_found = False
            expected_found = False            
            if self.cfg["expected_example"]:
                expected_found = True
            if  self.cfg["expected_error_example"]:
                error_found = True
            return expected_found, self.cfg["expected_example"]

        if self.process_extra_paras is not None:
            self.process_extra_paras(self.extra_paras)

        #print(cmd_cb)
        p = subprocess.Popen(cmd_cb, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.subprocess = p

        if self.block_mode is False:
            return None, None

        return self.check_output(print_expected)   

    # get command return code
    def check_return_code(self):
        return self.subprocess.returncode 

    # check if the cmmand is finished or not
    def is_finished(self):
        status = self.subprocess.poll()
        if status == 0:
            return True
        return False

# Group shell command class                    
class CMD_Group():
    def __init__(self, cmds=None, cfgs=None, simulation = False, bash_added=False, dos_shell=False, pre_run=None, pre_run_para=[], post_run=None, post_run_para=[]):      
        self.cmds = []
        self.pre_run = pre_run
        self.pre_run_para = pre_run_para
        self.post_run = post_run  
        self.post_run_para = post_run_para
        self.start_time = None
        self.end_time = None
        
        if cmds is None:
            if cfgs is not None:
                for cfg in cfgs:
                    cmd = C_CMD(cfg, simulation = simulation, show_all=False, bash_added=bash_added, dos_shell=dos_shell, block_mode = True)
                    self.cmds.append(cmd)
        else:
            self.cmds = cmds
            
    # run cmd in group, and wait till if in block mode
    def group_exe(self, block_mode=True):
        if self.cmds == []:
            print("Error! Command group is not initialezed.")
            return None
        if self.pre_run is not None:
            self.pre_run(self, self.pre_run_para)
        for cmd in self.cmds:
            cmd.cmd_exe()
        self.start_time = time.localtime(time.time())
        if block_mode:
            self.wait_for_group_exe_done()
            if self.post_run is not None:
                self.post_run(self, self.post_run_para)
            return self.check_return_code()
        return None

    # Block if there is any cmd runing. Return when all finish.
    def wait_for_group_exe_done(self):
        for cmd in self.cmds:
            cmd.wait_for_finished()
            #print("cmd done:")
        if self.post_run is not None:
            self.post_run(self.post_run_para)
        self.end_time = time.localtime(time.time())
        return True

    # Poll command group's running state, retun list of finished commands
    def poll_run_state(self):
        finished_cmd_list = []
        for cmd in self.cmds:
            if cmd.is_finished():
                finished_cmd_list.append(cmd)
        return finished_cmd_list

    #return fail if there is any failed running
    def check_return_code(self):
        all_ok = True
        for cmd in self.cmds:
            if cmd.check_return_code() != 0:
                print("Error when running:", cmd.comand_s, "  with return code ", cmd.check_return_code())
                all_ok = False
        return all_ok
        
        
            
