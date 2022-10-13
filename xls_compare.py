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

from utils import Save_ndarray_cases,  Update_Result_2_Xls,Xls_Read_Worksheet, Xls_Read_Row, Xls_Set_Value_BkgColor, Hide_colums_in_Xls
from Cmd import Q_Cmd

try_total=3
#with_log = True
with_log = False
xls_comparing_Running = {
               "cmd_ws": os.path.abspath(os.path.dirname(__file__)), 
               "setting_xls":  os.path.abspath(os.path.dirname(__file__)) + "/compare.xlsx",
               "setting_xls_row_offset":  0,
               "setting_xls_col_offset":  0,
               "setting_sheet": "setting",
               "output_xls": "compare_result.xls",
               "output_sheet": "",

               "baseline_xls": "", 
               "target_xls": "", 
               "baseline_sheet": "", 
               "target_sheet": "", 

               "baseline_workbook": None, 
               "baseline_worksheet": None, 
               "baseline_title_row": 0,
               "baseline_title": [],
               "baseline_header_item_pos": {}, 
               "baseline_index_item_replacement": [], 
               "baseline index item replacement": [], 

               "target_workbook": None, 
               "target_worksheet": None, 
               "items_minimum": 0, #to be compatible for error result
               "items_postive": {}, 
               "target_title_row": 0,
               "target_title": [],
               "target_header_item_pos": {}, 
               "target_index_item_replacement": [], 
               "target index item replacement": [], 
               
               "index_": [], 
               "string_index": True,
               "items_": [], 
               "poitive_items": [], 
               "delta_t_b": [], 
               "delta_b_t": [], 
               "delta": "_delta", 
               "target_ext_name": "", 
               "case_generating": False,

               "makes_scale": 10, 
}

index_item_replacement = {
            "index":"",
            "value":"",
            "replacement":"",
}

delta = {
            "baseline_item":{},
            "target_item":{},
            "delta":{},
}


def get_filename(xls_fn):
    #print("get_file", xls_fn, xls_comparing_Running["work_folder"])
    if xls_comparing_Running["work_folder"] != "":
        return xls_comparing_Running["work_folder"] + "/" +xls_fn
    else:
        return xls_fn

def Get_Config_From_Setting_Sheet():
    workbook_fn = xls_comparing_Running["setting_xls"]
 
    try:
        print("Opening", workbook_fn)
        workbook = xlrd.open_workbook(workbook_fn) 
    except:          
        print("Error! Fail to open workbook ", workbook_fn, ". Please provide right test_case_xls.")
        exit()
    
    case_sheet_name = xls_comparing_Running["setting_sheet"]
    try:
        cases_sheet = workbook.sheet_by_name(case_sheet_name)    
        case_sheet_id = workbook.sheet_names().index(case_sheet_name)
    except:          
        print("Fail to open sheet ", case_sheet_name, " in ", workbook_fn)
        exit()

    for row in range(xls_comparing_Running["setting_xls_row_offset"], cases_sheet.nrows):    
        r = cases_sheet.row_values(row)
        #print(r)
        if r[xls_comparing_Running["setting_xls_col_offset"]] is not "":
            xls_comparing_Running[r[xls_comparing_Running["setting_xls_col_offset"]]] = r[xls_comparing_Running["setting_xls_col_offset"] + 1]
            #for settings with multiple colums:
            if "index item replacement" in r[xls_comparing_Running["setting_xls_col_offset"]]:
                xls_comparing_Running[r[xls_comparing_Running["setting_xls_col_offset"]]] = r[xls_comparing_Running["setting_xls_col_offset"]+1:]

    def error_exit(msg):
        print(msg, "Please check settings in", xls_comparing_Running["setting_xls"], " sheet", xls_comparing_Running["setting_sheet"])
        exit()
    def file_exist(fn):
        full_fn = get_filename(xls_comparing_Running[fn])
        if not os.path.exists(full_fn):
            msg = full_fn + " "+ xls_comparing_Running[fn] + " does not exist."
            error_exit(msg)    
        
    if "work_folder" not in xls_comparing_Running.keys() or xls_comparing_Running["work_folder"].strip() == "":
        xls_comparing_Running["work_folder"] = ""
    if "index" in xls_comparing_Running.keys():
        xls_comparing_Running["index_"] = [x.strip() for x in xls_comparing_Running["index"].split(";")]
    else:
            msg = "Please provide compare index"
            error_exit(msg)    
    if "items" in xls_comparing_Running.keys():
        xls_comparing_Running["items_"] = [x.strip() for x in xls_comparing_Running["items"].split(";")]
    else:
            msg = "Please provide compare item"
            error_exit(msg) 
    if "poitive items" in xls_comparing_Running.keys():
        xls_comparing_Running["poitive_items"] = [x.strip() for x in xls_comparing_Running["poitive items"].split(";")]
    else:
            msg = "Please provide poitive items"
            error_exit(msg) 
            
    if "marks postive" in xls_comparing_Running.keys():
        xls_comparing_Running["marks_postive"] = [int(x.strip()) for x in xls_comparing_Running["marks postive"].split(";")]
    else:
            msg = "Please provide marks postive"
            error_exit(msg) 
    if "marks negitve" in xls_comparing_Running.keys():
        xls_comparing_Running["marks_negitve"] = [int(x.strip()) for x in xls_comparing_Running["marks negitve"].split(";")]
    else:
            msg = "Please provide marks negitve"
            error_exit(msg) 
            
    if "makes scale" in xls_comparing_Running.keys():
        try:
            xls_comparing_Running["makes_scale"] = int(xls_comparing_Running["makes_scale"]) 
        except:
            e_msg = "Error setting in makes scale "
            error_exit(e_msg)


    if "baseline title row" in xls_comparing_Running.keys():
        try:
            xls_comparing_Running["baseline_title_row"] = int(xls_comparing_Running["baseline title row"]) - 1
        except:
            e_msg = "Error setting in baseline title row "
            error_exit(e_msg)
    if "target title row" in xls_comparing_Running.keys():
        try:
            xls_comparing_Running["target_title_row"] = int(xls_comparing_Running["target title row"]) -1
        except:
            e_msg = "Error setting in target title row "
            error_exit(e_msg)

    if xls_comparing_Running['baseline_xls'] != "":
        xls_comparing_Running['baseline xls'] = xls_comparing_Running['baseline_xls'] 
        
    if xls_comparing_Running['target_xls'] != "":
        xls_comparing_Running['target xls'] = xls_comparing_Running['target_xls'] 
        
    if xls_comparing_Running['baseline_sheet'] != "":
        xls_comparing_Running['baseline sheet'] = xls_comparing_Running['baseline_sheet'] 
        
    if xls_comparing_Running['target_sheet'] != "":
        xls_comparing_Running['target sheet'] = xls_comparing_Running['target_sheet'] 
        
    file_exist("baseline xls")
    file_exist("target xls")

def Get_Base_And_Target_Sheet():
    baseline_xls = get_filename(xls_comparing_Running["baseline xls"])
    baseline_sheet = xls_comparing_Running["baseline sheet"]    
    if with_log:
        print("Get_Base_And_Target_Sheet", xls_comparing_Running["baseline xls"], baseline_xls)
    xls_comparing_Running["baseline_workbook"], xls_comparing_Running["baseline_worksheet"] = Xls_Read_Worksheet(baseline_xls, baseline_sheet)
    xls_comparing_Running["baseline_title"] = Xls_Read_Row( xls_comparing_Running["baseline_worksheet"], xls_comparing_Running["baseline_title_row"])
    
    target_xls = get_filename(xls_comparing_Running["target xls"])
    target_sheet = xls_comparing_Running["target sheet"]
    xls_comparing_Running["target_workbook"], xls_comparing_Running["target_worksheet"]= Xls_Read_Worksheet(target_xls, target_sheet)
    xls_comparing_Running["target_title"] = Xls_Read_Row( xls_comparing_Running["target_worksheet"], xls_comparing_Running["target_title_row"])

    for bi in xls_comparing_Running["baseline_title"]:
        xls_comparing_Running["baseline_header_item_pos"][bi] = xls_comparing_Running["baseline_title"].index(bi)
    for bi in xls_comparing_Running["target_title"]:
        xls_comparing_Running["target_header_item_pos"][bi] = xls_comparing_Running["target_title"].index(bi)
    xls_comparing_Running["items_minimum"]  = xls_comparing_Running["target_header_item_pos"][xls_comparing_Running["items_"] [0]]

    def ir_replace(iir, iir_t):
        for r_group in  xls_comparing_Running[iir]:
            if r_group is not "":
                rg = r_group.strip().split(";")
                if len(rg) == 3:
                    ir = index_item_replacement.copy()
                    ir["index"] = rg[0]
                    ir["value"] = rg[1]
                    ir["replacement"] = rg[2]
                    xls_comparing_Running[iir_t].append(ir)
    ir_replace("baseline index item replacement", "baseline_index_item_replacement")   
    ir_replace("target index item replacement", "target_index_item_replacement")   

def Get_Items(sheet,   indexs, item_offset, r, replacement_item=[]):
        x = {}
        x ["row"] = r
        trv = Xls_Read_Row(sheet, r)
        for item in indexs:
            if xls_comparing_Running["string_index"] :
                v = trv[item_offset[item]]
                if type(v) == type(1.0) and v % 1 == 0.0: 
                        trv[item_offset[item]] = str(int(v))               
            x [item] = trv[item_offset[item]] 
        for item in xls_comparing_Running["items_"]:
            if len(trv) > xls_comparing_Running["items_minimum"] :
                x [item] = trv[item_offset[item]] 
            else:
                x [item] = ""

        for ri in replacement_item:
            if x[ri["index"]] == ri["value"]:
                x[ri["index"]] = ri["replacement"]
        return x
def Search_Item(b_items, t_item):
    indexs =  xls_comparing_Running["index_"]
    for item in b_items:
        match = True
        for c in indexs:
            if  t_item[c] != item[c]:
                match = False
                break
        if match:
            if with_log:
                print("Searching ",  t_item)
                print("===>found")
                print(item)
                print("")
                print("")
            return item
    if with_log:
        print("Searching ",  t_item)
        print("=***>Not found ....Error"  )      
    return None
                
def Compare_Items(bi, ti):
    d = delta.copy()
    d["baseline_item"] = bi
    d["target_item"] = ti
    di = {}
    items =  xls_comparing_Running["items_"]
    for i in items:
        ni = i + xls_comparing_Running["target_ext_name"]
        try:
            bv = float(bi[i])
            tv = float(ti[i])
            dv = (tv - bv) / bv
            di[ni] = dv
            #print(bv, tv, dv)
        except:
            di[ni] = ""
            
    d["delta"] = di
    return d
    
    
def Compare():
    baseline_items = []
    #Read bineline sheet items
    for row in range(1, xls_comparing_Running["baseline_worksheet"].nrows ):
        rv = Get_Items (xls_comparing_Running["baseline_worksheet"], xls_comparing_Running["index_"], xls_comparing_Running["baseline_header_item_pos"], row, xls_comparing_Running["baseline_index_item_replacement"])
        baseline_items.append(rv)  
    if with_log:
        print(len(baseline_items))
        print(baseline_items[1:2])
    target_items = []
    if with_log:
        print(xls_comparing_Running["baseline_index_item_replacement"])
        print(xls_comparing_Running["target_index_item_replacement"])
    #Read target sheet items
    for row in range(1, xls_comparing_Running["target_worksheet"].nrows ):
        rv = Get_Items (xls_comparing_Running["target_worksheet"], xls_comparing_Running["index_"], xls_comparing_Running["target_header_item_pos"], row, xls_comparing_Running["target_index_item_replacement"])
        target_items.append(rv)
    if with_log:
        print(len(target_items))
        print(target_items[1:2])
    #Generate delta items
    delta_items = []
    for t in target_items:
        b = Search_Item(baseline_items, t)
        if b is not None:
            d = Compare_Items(b, t)
            delta_items.append(d)
    xls_comparing_Running["delta_t_b"]  = delta_items
    if with_log:
        print(delta_items[:10])

def Get_BkgColor(delta_v, key):
    postive = False
    for pk in xls_comparing_Running["poitive_items"]:
        if pk in key:
            postive = True
    try:
        color_setting_neg = xls_comparing_Running["marks_negitve"]
        color_setting_pos = xls_comparing_Running["marks_postive"]
        scale = float(xls_comparing_Running["makes_scale"])
        scale_size = len(color_setting_neg)
        p = int(float(delta_v) * 100.0 /  scale)
        if postive is False:
            c_s = color_setting_pos if p > 0 else color_setting_neg
        else:
            c_s = color_setting_neg if p > 0 else color_setting_pos
        p = p if p > 0 else -p
        p = scale_size-1 if p >= scale_size   else p
        return c_s[p]
    except:
        return 1
    
def Generate_Report():
    target_xls_fn =  get_filename(xls_comparing_Running["target xls"])
    output_xls_fn =  get_filename(xls_comparing_Running["output_xls"])
    output_sheet = xls_comparing_Running["target sheet"]

    xls_comparing_Running["case_write_wb"] = copy(xls_comparing_Running["target_workbook"]) 
    case_sheet_id = xls_comparing_Running["target_workbook"].sheet_names().index(output_sheet)
    xls_comparing_Running["case_write_sheet"] = xls_comparing_Running["case_write_wb"].get_sheet(case_sheet_id)    

    # output title for delta
    output_title = xls_comparing_Running["target_title"].copy()
    ext_title = [ i + xls_comparing_Running["target_ext_name"] for i in xls_comparing_Running["items_"]]
    start_pos = len(output_title)
    ext_pos = {}
    i = 1
    for e in ext_title:
        ext_pos[e] = start_pos + i
        i = i + 1
    for t in ext_pos.keys():
        v = t.replace("@","vs")
        Update_Result_2_Xls(xls_comparing_Running["case_write_sheet"], 0, ext_pos[t], v, offset=0)

    # output title for value
    base_ext_title = [ i +  xls_comparing_Running["target_ext_name"]   for i in xls_comparing_Running["items_"]]
    start_pos = len(output_title) + len(ext_title) + 1
    base_ext_pos = {}
    i = 1
    for e in base_ext_title:
        base_ext_pos[e] = start_pos + i
        i = i + 1
    for t in base_ext_pos.keys():
        #remove "delta"
        v = t[:-len(xls_comparing_Running["delta"])]
        Update_Result_2_Xls(xls_comparing_Running["case_write_sheet"], 0, base_ext_pos[t], v, offset=0)

    
    for dv in xls_comparing_Running["delta_t_b"]:
        row = dv["target_item"]["row"]
        for delta_items in dv["delta"].keys():
            if dv["delta"][delta_items] is not "":
                c = Get_BkgColor(dv["delta"][delta_items], delta_items)
                Xls_Set_Value_BkgColor(xls_comparing_Running["case_write_sheet"], row, ext_pos[delta_items], dv["delta"][delta_items], offset=0, bkg_color=c)

        for base_item in xls_comparing_Running["items_"]:
            Update_Result_2_Xls(xls_comparing_Running["case_write_sheet"], row, base_ext_pos[base_item + xls_comparing_Running["target_ext_name"]], dv["baseline_item"][base_item], offset=0)

    if xls_comparing_Running["output_sheet"] != "":
        xls_comparing_Running["case_write_wb"].get_sheet(case_sheet_id).name = xls_comparing_Running["output_sheet"]
        output_sheet = xls_comparing_Running["output_sheet"]

    #For hidden items
    if "hidden items" in xls_comparing_Running.keys():
        h_c = []
        hide_items = xls_comparing_Running["hidden items"].split(";")
        for hi in hide_items:
            h_c.append(xls_comparing_Running["baseline_header_item_pos"][hi])
        Hide_colums_in_Xls(xls_comparing_Running["case_write_wb"].get_sheet(case_sheet_id),h_c)
    xls_comparing_Running["case_write_wb"].save(output_xls_fn)
    print("The result is saved to ", output_xls_fn, output_sheet)
    
def main():
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Unsupported value encountered.')

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--setting_xls', type=str,help='setting workbook in xls format: xxx.xls.', default=xls_comparing_Running["setting_xls"])
    parser.add_argument('--setting_sheet', type=str,help='setting worksheet in xls format: setting', default=xls_comparing_Running["setting_sheet"])
    parser.add_argument('--output_xls', type=str,help='output xls', default=xls_comparing_Running["output_xls"])
    parser.add_argument('--output_sheet', type=str,help='output sheet name.', default=xls_comparing_Running["output_sheet"])

    parser.add_argument('--baseline_xls', type=str,help='The xls file name to be compared with', default=xls_comparing_Running["baseline_xls"])
    parser.add_argument('--baseline_sheet', type=str,help='The sheet name of the xls file to be compared with', default=xls_comparing_Running["baseline_sheet"])
    parser.add_argument('--xls', type=str,help='xls name', default=xls_comparing_Running["target_xls"])
    parser.add_argument('--sheet', type=str,help='sheet name', default=xls_comparing_Running["target_sheet"])

    args = parser.parse_args()
    print(args)

    xls_comparing_Running["setting_xls"] = args.setting_xls
    xls_comparing_Running["setting_sheet"] = args.setting_sheet
    xls_comparing_Running["output_xls"] = args.output_xls
    xls_comparing_Running["output_sheet"] = args.output_sheet
    xls_comparing_Running["baseline_xls"] = args.baseline_xls
    xls_comparing_Running["target_xls"] = args.xls
    xls_comparing_Running["baseline_sheet"] = args.baseline_sheet
    xls_comparing_Running["target_sheet"] = args.sheet


    Get_Config_From_Setting_Sheet()
    Get_Base_And_Target_Sheet()
    xls_comparing_Running["target_ext_name"] = "_@_"  + xls_comparing_Running['baseline sheet'] + xls_comparing_Running["delta"] 
    Compare()
    Generate_Report()
    exit()
    
if __name__ == '__main__':
    main()
        

    

