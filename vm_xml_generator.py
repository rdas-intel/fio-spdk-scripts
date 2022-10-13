import os
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from pandas import Series, DataFrame   

from utils import df_2_csv, get_files_from_folder, load_json
from Cmd import Q_Cmd

with_log = True
with_log = False
vm_xml_running = {
               "cmd_ws": os.path.abspath(os.path.dirname(__file__)), 
               "work_folder": os.path.abspath(os.path.dirname(__file__)), 
               "output_folder":   "/media/data/ml/vms/",
#               "input_folder":   "./xiperf_6_ports_3vms_simple/",
#               "input_log":   "rapl.log",
               "vm_cfg":   "/media/data/ml/vms/vm_cfg.json",
               "vm_settings":{},
}


def generate_xml_cfg_str(idx=0):
    #print(vm_xml_running["vm_settings"])
    if idx < len(vm_xml_running["vm_settings"]["vms"]):
        #print(vm_xml_running["vm_settings"]['vms'][idx])
        vm_xml_running["xmls_output"] [vm_xml_running["vm_settings"]['vms'][idx]["name"]] = {}
        vm_xml_running["xmls_output"] [vm_xml_running["vm_settings"]['vms'][idx]["name"]]["file_name"] = vm_xml_running["vm_settings"]['vms'][idx]["name"] + "_cfg.sh"
        vm_xml_running["xmls_output"] [vm_xml_running["vm_settings"]['vms'][idx]["name"]]["output_str"]  = []
        vm_xml_running["xmls_output"] [vm_xml_running["vm_settings"]['vms'][idx]["name"]]["output_str"] .append ("xml_tmp_file=" + vm_xml_running["vm_settings"]["tmplate_file"] )
        vm_xml_running["xmls_output"] [vm_xml_running["vm_settings"]['vms'][idx]["name"]]["output_str"] .append ("xml_file_name=" + vm_xml_running["vm_settings"]['vms'][idx]["name"]  + ".xml")
        cpus = vm_xml_running["vm_settings"]['vms'][idx]["cpus"]
        vm_xml_running["xmls_output"] [vm_xml_running["vm_settings"]['vms'][idx]["name"]]["output_str"] .append ("xml_cpu_cores=" + cpus)
        cpu_num= vm_xml_running["vm_settings"]['vms'][idx]["cpu_num"]
        vm_xml_running["xmls_output"] [vm_xml_running["vm_settings"]['vms'][idx]["name"]]["output_str"] .append ("xml_cpu_num=" + str(cpu_num))
        nics = ",".join(vm_xml_running["vm_settings"]['vms'][idx]["nics"])
        vm_xml_running["xmls_output"] [vm_xml_running["vm_settings"]['vms'][idx]["name"]]["output_str"] .append ("xml_nics=" + nics)
        vm_xml_running["xmls_output"] [vm_xml_running["vm_settings"]['vms'][idx]["name"]]["output_str"] .append ("xml_vm_mac=" + vm_xml_running["vm_settings"]['vms'][idx]["mac"])
        vm_xml_running["xmls_output"] [vm_xml_running["vm_settings"]['vms'][idx]["name"]]["output_str"] .append ("xml_vm_name=" + vm_xml_running["vm_settings"]['vms'][idx]["name"] )
        vm_xml_running["xmls_output"] [vm_xml_running["vm_settings"]['vms'][idx]["name"]]["output_str"] .append ("xml_vm_image_name=" + vm_xml_running["vm_settings"]['vms'][idx]["name"] + ".raw")
        
    #print(vm_xml_running["xmls_output"] )
def generate_xmls():
    for xml in vm_xml_running["xmls_output"].keys():
        with open(vm_xml_running["xmls_output"][xml]["file_name"], "w") as fout:
            #print(vm_xml_running["xmls_output"][xml]["output_str"])
            for s in vm_xml_running["xmls_output"][xml]["output_str"]:
                print(str(s))
                fout.write(str(s))
                fout.write("\n")
            print("Geneated:", vm_xml_running["xmls_output"][xml]["file_name"], "\n")
            
def main():
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--vm_cfg', type=str,help='vm cfg in json format  ', default=vm_xml_running["vm_cfg"])
    parser.add_argument('--output_folder', type=str,help='The input folder to check power monitor logs. All *rapl.log under the folder will be parsed. ', default=vm_xml_running["output_folder"])

    args = parser.parse_args()
    print(args)

    vm_xml_running["vm_cfg"] = args.vm_cfg
    vm_xml_running["output_folder"] = args.output_folder

    vm_xml_running["vm_settings"] = load_json(vm_xml_running["vm_cfg"] )
    vm_xml_running["xmls_output"] = {} 
    #print(vm_xml_running["vm_settings"])
    for idx in range(len(vm_xml_running["vm_settings"]["vms"])):
        generate_xml_cfg_str(idx) 
    generate_xmls()
    exit()
    
if __name__ == '__main__':
    main()
        

    

