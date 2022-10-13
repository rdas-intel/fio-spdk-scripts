trimport os
from pathlib import Path
import argparse

from Cmd import Q_Cmd
from utils import get_files_from_folder
#with_log = True
with_log = False
nvme_fio_compare_Running = {
               "cmd_ws": os.path.abspath(os.path.dirname(__file__)), 
               "connection": "__c__",

}

def get_all_nvme_fio_result(path, ext=".xls"):
    files = get_files_from_folder(path, ext)
    n_f = {"single_files":[], "group_files":[]}
    
    for f in files:
        fn = os.path.basename(f)
        if nvme_fio_compare_Running["connection"]  in fn:
            continue
        if "nvme" in fn:
            if "_" in fn:
                n_f["group_files"].append(f)
            else:
                n_f["single_files"].append(f)
    return n_f
def compare(target_fn, target_sheet, base_fn, base_sheet, output_f, output_sheet):
    com_s = "python " + nvme_fio_compare_Running["cmd_ws"] +"/xls_compare.py --output_xls " + output_f + " --output_sheet " +  output_sheet \
        + " --baseline_xls " + base_fn + " --baseline_sheet " + base_sheet + " --xls " \
        + target_fn + " --sheet " + target_sheet
    r = Q_Cmd(com_s)
    if with_log:
        print(r)
    check_s = "ls -lh " + output_f
    print(Q_Cmd(check_s))
    
def main():
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')
            
            
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--folder', type=str,help='folder for comparing', default="./_k_result")

    args = parser.parse_args()
    nvme_fio_compare_Running["folder"] = args.folder
    print(args)
    wf = nvme_fio_compare_Running["folder"] 
    nf = get_all_nvme_fio_result(wf)
    if with_log:
        print(nf)
    sf_c = []
    for sf in nf["single_files"]:
        sfg = []
        sf_fn = os.path.basename(sf)
        nv_sf = sf_fn.replace("nvme", "").replace("n1.xls", "")
        for gf in nf["group_files"]:
            gf_fn = os.path.basename(gf)
            gf_nvmes = gf_fn.split("_")
            if nv_sf in gf_nvmes:
                t_s = sf_fn[:-len(".xls")]
                b_s = gf_fn[:-len(".xls")]
                out_f = sf[:-len(".xls")] + nvme_fio_compare_Running["connection"] + gf_fn
                out_s = t_s + nvme_fio_compare_Running["connection"] + b_s
                s_sfg = {"xls":sf, "sheet": t_s, "base_xls":gf, "base_sheet": b_s, "output_file": out_f, "output_sheet": out_s} 
                sfg.append(s_sfg)
        sf_c.append(sfg)
    for single_f_l in sf_c:
        for x in single_f_l:
            print(x["xls"], x["base_xls"], " ===> ", x["output_file"], x["output_sheet"])
            compare(x["xls"], x["sheet"], x["base_xls"],x["base_sheet"],x["output_file"], x["output_sheet"])
        if 0: # not implemeted, for all in one xls
                if len(single_f_l) == 1:
                    x = single_f_l[0]
                    print(x["xls"], x["base_xls"], " ===> ", x["output_file"], x["output_sheet"])
                    compare(x["xls"], x["sheet"], x["base_xls"],x["base_sheet"],x["output_file"], x["output_sheet"])
                else:    
                    idx = 0
                    for x in single_f_l:
                        idx += 1 
                        input_f = "/tmp/comp_" + str(idx -1) + ".xls" if idx != 1 else x["xls"]
                        if idx != len(single_f_l):
                            outputf_f = "/tmp/comp_" + str(idx) + ".xls"
                        else:
                            outputf_f =  x["xls"][:-len(".xls")] + nvme_fio_compare_Running["connection"]  +  ".xls"
                        print(input_f, x["base_xls"], " ===> ",outputf_f,x["sheet"])
                        compare(input_f, x["sheet"], x["base_xls"],x["base_sheet"],outputf_f, x["sheet"])
            com_s = "rm -f /tmp/comp_*.xls 2>/dev/null "
            Q_Cmd(com_s)
    exit()
    
if __name__ == '__main__':
    main()
        

    

