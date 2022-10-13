import json
import os
from pathlib import Path
import argparse
import os
import socket,fcntl,struct
import argparse

from copy import deepcopy
import time
from Cmd import Q_Cmd_Ext, Q_Remote_Cmd, Q_Remote_S_Result




def get_ip_address(ifname):
    s= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inet= fcntl.ioctl(s.fileno(),0x8915, struct.pack('256s', ifname))
    return socket.inet_ntoa(inet[20:24])

def get_ip_socket():
    s= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8',80))
    _ip= s.getsockname()[0]
    s.close()
    return _ip
    
    
def get_remote_time(server_ip):
#    cmd='date +"%Y-%m-%d %H:%M.%S" '

    
    ds_= str(year) + "-" +  str(month) + "-" + str(day) + " " + str(hour) + ":"  +str(minute)
    return ds_
def update_date_time(s):
    cmd='date  -s  ' + '"' + s + '"'
    
    return Q_Cmd_Ext(cmd)

def Send_host_ip(server_ip, hostname, ipadd):
    cmd='python /media/data/ml/storage_io/Storage/send_mail.py  --hostname ' + hostname + " --ipaddr " + ipadd

    dt = Q_Remote_Cmd(server_ip, cmd, silent_mode=True)
    
def main():
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--hostname', type=str,help='hostname', default=socket.gethostname())
    parser.add_argument('--ipaddr', type=str,help='ipaddress', default=get_ip_socket())
    args = parser.parse_args()
    print(args)
    Send_host_ip("10.239.89.154", args.hostname, args.ipaddr)

    
if __name__ == '__main__':
    main()

