#!/usr/bin/env python


import os
import socket,fcntl,struct
import argparse
#from Cmd import Q_Cmd_Ext,





  

from email.mime.text import MIMEText

from subprocess import Popen, PIPE

#import commands

  

import sys

#reload(sys)

#sys.setdefaultencoding('utf-8')



def getHostInfo():
    cmd= 'echo test'
    f= os.popen(cmd,'r')
    _ip= f.read().strip()
    f.close()
    return  (_ip,os.getlogin())

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

def send_mail(sender, recevier, subject, html_content):

        msg = MIMEText(html_content, 'html', 'utf-8')

        msg["From"] = sender

        msg["To"] = recevier

        msg["Subject"] = subject

        p = Popen(["/usr/sbin/sendmail", "-t"], stdin=PIPE)

        p.communicate(msg.as_string())
  

def test():
  
    ip = get_ip_socket()
    print(ip)
    host=socket.gethostname()
    print(host)
    sender = 'shide.dong@intel.com'

    recevier = 'shide.dong@intel.com'

    subject = 'ip_address of ' + host + ": " + ip 

    html_content = ''

    send_mail(sender, recevier, subject, html_content)

#_re_ = 'sebastien.lemarie@intel.com'
_re_ = 'shide.dong@intel.com'
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
    
    sender = 'shide.dong@intel.com'
    recevier = _re_
    subject = 'ip_address of ' + args.hostname + ": " + args.ipaddr 
    html_content = ''

    send_mail(sender, recevier, subject, html_content)
    recevier = 'sebastien.lemarie@intel.com'
    #recevier = 'shide.dong@intel.com'
    send_mail(sender, recevier, subject, html_content)

if __name__ == '__main__':
    main()
    
