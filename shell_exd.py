import json
import os
from pathlib import Path
import argparse
from copy import deepcopy
from xlutils.copy import copy
import time
import math

from Cmd import C_CMD, Q_Cmd, T_Q_CMD, __ERROR_FLOAT, __ERROR_INT, Q_Remote_Cmd, Tmux_CMD #, CMD_Group, Export_Env, 

with_log = True
#with_log = False
def LogOut(s1="", s2="", s3="", s4="",s5="",s6="",s7="",s8="",s9="",s10=""):
    if with_log == False:
        return
    print(s1,s2,s3,s4,s5,s6,s7,s8,s9,s10)
    
shell_exd_Running = {
               "cmd":   {},
               "show_logs":   with_log,
}

def Cmd_Tmux_New_Local_Run():
    LogOut(shell_exd_Running["cmd"])
    session_name = shell_exd_Running["cmd"]["op_1"] 
    local_remote = shell_exd_Running["cmd"]["op_2"] 
    if local_remote.upper() == "LOCAL":
        local_remote = ""
    tmux = Tmux_CMD(session_name, ssh_ip=local_remote,auto_delete=False,silent_mode=not shell_exd_Running["show_logs"])
    cmds = shell_exd_Running["cmd"]["op_3"] 
    if cmds != "":
        cs = cmds.split(";")
        r = tmux.exe_remote_cmds(cs)
        print(r)

def Cmd_Tmux_Send_Cmd():
    LogOut(shell_exd_Running["cmd"])
    session_name = shell_exd_Running["cmd"]["op_1"] 
    local_remote = shell_exd_Running["cmd"]["op_2"] 
    if local_remote.upper() == "LOCAL":
        local_remote = ""
    cmd_send_session="xxxxxxx"
    tmux = Tmux_CMD(cmd_send_session, ssh_ip=local_remote,auto_delete=False,silent_mode=not shell_exd_Running["show_logs"])
    cmds = shell_exd_Running["cmd"]["op_3"] 
    if cmds != "":
        cs = cmds.split(";")
        r = tmux.exe_remote_cmds(cs,s_name=session_name)
        print(r)
    tmux.stop()

def Cmd_Tmux_Send_Ctl_C():
    LogOut(shell_exd_Running["cmd"])
    session_name = shell_exd_Running["cmd"]["op_1"] 
    local_remote = shell_exd_Running["cmd"]["op_2"] 
    if local_remote.upper() == "LOCAL":
        local_remote = ""
    cmd_send_session="xxxxxxx"
    tmux = Tmux_CMD(cmd_send_session, ssh_ip=local_remote,auto_delete=False,silent_mode=not shell_exd_Running["show_logs"])
    tmux.send_special_cmd("C-c ",s_name =session_name)
    tmux.stop()
    
def Cmd_SSH_Cmds():
    LogOut(shell_exd_Running["cmd"])
    ssh_ip = shell_exd_Running["cmd"]["op_1"] 
    cmds = shell_exd_Running["cmd"]["op_2"] 
    if cmds != "":
        cs = cmds.split(";")
        for c in cs:
            print(ssh_ip, c)
            r = Q_Remote_Cmd(ssh_ip, c)
            print(r)    
    

def shell_exd():
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--cmd', type=str,help='cmd', default= "")
    parser.add_argument('--show_logs', type=str2bool,help='show_logs', default= shell_exd_Running["show_logs"])
    parser.add_argument('--op_1', type=str,help='op_1 ', default="")
    parser.add_argument('--op_2', type=str,help="op_2", default="")
    parser.add_argument('--op_3', type=str,help='op_3', default="")
    parser.add_argument('--op_4', type=str,help="op_4", default="")

    args = parser.parse_args()
    print(args)

    shell_exd_Running["cmd"]["opt_0"]= args.cmd
    shell_exd_Running["cmd"]["op_1"] = args.op_1
    shell_exd_Running["cmd"]["op_2"] = args.op_2
    shell_exd_Running["cmd"]["op_3"] = args.op_3
    shell_exd_Running["cmd"]["op_4"] = args.op_4
    
    shell_exd_Running["show_logs"] = args.show_logs
    print(shell_exd_Running)
    if shell_exd_Running["cmd"]["opt_0"] == "Tmux_New_Local_Run":
        Cmd_Tmux_New_Local_Run()
    elif shell_exd_Running["cmd"]["opt_0"] == "Tmux_Send_Command":
        Cmd_Tmux_Send_Cmd()
    elif shell_exd_Running["cmd"]["opt_0"] == "SSH_Command":
        Cmd_SSH_Cmds()
    elif shell_exd_Running["cmd"]["opt_0"] == "Tmux_Send_Ctl_C":
        Cmd_Tmux_Send_Ctl_C()

if __name__ == '__main__':


    shell_exd()
        


