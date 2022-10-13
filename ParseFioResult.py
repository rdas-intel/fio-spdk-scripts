import json
import os
import argparse
import FioResultDecoder
from dateutil.parser import parse
from Record import C_Record


__runing={
    "input_path": "/media/data/ml/storage_io/Storage/_result/",
    "interesting_keys_list": [],
    "interesting_keys_str": ["r_jobname", "fn_file_name", "fn_bs", "fn_jobs", "fn_io_deepth", "fn_rw", "fn_name", "usr_cpu", "sys_cpu","read_bw","write_bw",\
                                    "read_io_bytes","read_io_kbytes","read_iops",\
                                    "write_io_bytes","write_io_kbytes","write_iops",\
                                    "read_lat_ns_min", "read_lat_ns_max", "read_lat_ns_mean", "read_lat_ns_stddev",  "read_bw_min", "read_bw_max", "read_bw_agg", "read_bw_mean", "read_bw_dev", "read_bw_samples", "read_iops_min", "read_iops_max", "read_iops_mean","read_iops_stddev",\
                                    "write_bw_min", "write_bw_max", "write_bw_agg", "write_bw_mean", "write_bw_dev", "write_bw_samples", "write_iops_min", "write_iops_max", "write_iops_mean", "write_iops_stddev", "write_iops_samples"],
    }


def get_filePath_fileName_fileExt(filename):
  (filepath,tempfilename) = os.path.split(filename);
  (shotname,extension) = os.path.splitext(tempfilename);
  return filepath,shotname,extension
  
def is_date(string):
    try:
        parse(string)
        return True
    except ValueError:
        return False

def print_schema_def(key, value):
    typestr = value.__class__.__name__
    if typestr == 'str' or typestr == 'unicode':
        if (is_date(value)):
            typestr = "datetime"
        else:
            typestr = "varchar(256)"
    return ",\n  `{}` {} NOT NULL".format(key, typestr)
    
def parser_fio_json(file_name):
    
    json_data = open(file_name)
    try:
        data = json.load(json_data, cls=FioResultDecoder.FioResultDecoder)
    except:
        print("Error on processing ", file_name)
        return None
#print(data)
    _, json_fn, _ = get_filePath_fileName_fileExt(file_name)

    job = data['jobs'][0]
    job["r_jobname"]=json_fn
    #print(type(job))
    #for key,value in job.items():
    #    print(key, value)
    fnl = json_fn.split("_")

    def bs_k_2_bytes(bs):
        if "k" in bs:
            nkbs = bs.replace("k", "").strip()
            new_bs = str(int(nkbs) * 1024)
            return new_bs
        else:
            return bs
    
    job["fn_file_name"] = fnl[0].replace("-", "/")
    job["fn_bs"] = bs_k_2_bytes(fnl[1])
    job["fn_jobs"] = fnl[2]    
    job["fn_io_deepth"] = fnl[3]        
    job["fn_rw"] = fnl[4]        
    job["fn_name"] = fnl[5]        


    return job

def get_all_json_files(folder_name):

    f_list = os.listdir(folder_name)
    j_files = []
    for i in range(0, len(f_list)):
        if ".json" in f_list[i]:
            path = os.path.join(folder_name, f_list[i])
            print(path)
            j_files.append(path)
    return j_files


def fio_parser():
    
    folder_name= __runing["input_path"] 
    json_file_list = get_all_json_files(folder_name)

    job_data_list = []
    error_file_list = []
    for jf in json_file_list:
        print("Processing ", jf)
        jd = parser_fio_json(jf)
        if jd is not None:
            job_data_list.append(jd)
        else:
            error_file_list.append(jf)
        
    keys = list(job_data_list[0].keys())
#print(len(keys))

    interesting_keys =  __runing["interesting_keys_list"] 

    cr = C_Record("fio_result.csv", folder_name=folder_name, delete_old=True)
    header = ";".join(keys)
    cr.add_node(header)

    cr_interesting = C_Record("fio_result_interesting.csv", folder_name=folder_name, delete_old=True)
    header = ";".join(interesting_keys)
    cr_interesting.add_node(header)


    for jd in job_data_list:
        json_val_list = []
        for k in keys:
            json_val_list.append(str(jd[k]))
        s_value =  ";".join(json_val_list)
        cr.add_node(s_value)

        json_val_list = []
        for k in interesting_keys:
            json_val_list.append(str(jd[k]))
        s_value =  ";".join(json_val_list)
        cr_interesting.add_node(s_value)    


    if len(error_file_list) > 0:
        print("Error files:")
        print(error_file_list)
        
def main():
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--input_path', type=str,help='input path where the fio json result puth.', default=__runing["input_path"])    
    parser.add_argument('--interesting_keys', type=str,help='keys that will be added for intereresting csv file.', default=",".join(__runing["interesting_keys_str"]))
    args = parser.parse_args()
    print(args)
    __runing["interesting_keys_list"] = args.interesting_keys.split(",")
    __runing["input_path"] = args.input_path
    
    fio_parser()

if __name__ == '__main__':
    main()
        

    
