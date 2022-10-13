import os
from os.path import exists
from datetime import datetime


class C_Record():
    # mode="r"
    def __init__(self, record_file_name, folder_name="", delete_old = False, head_titile=None, mode = None):    
    
        if mode is None:
            if delete_old:
                mode = "w"
            else:
                mode = "a"
        if folder_name != "":
            logfile = os.path.join(folder_name, record_file_name)
        else:
            logfile = record_file_name
            

        self.r_file = open(logfile, mode)
        
        if self.r_file is None:
            error_msg = "=== \nError, fail to open {} ===\n".format(folder_name)
            print(error_msg)
        elif head_titile:
            self.add_record(head_titile)
            
    def exist(self):
        return False if self.r_file is None else True
        
    def __del__(self):
        self.close()
            
    def add_line(self, line_t):
        self.r_file.write(str(line_t))
        self.r_file.flush()          
        
    def add_record(self, line_t):
        self.r_file.writelines(str(line_t))
        self.r_file.flush()
    def read_whole_record(self):
        return self.r_file.readlines()
    def read_record(self):
        line = self.r_file.readline()
        if len(line) > 2:
            return line[:len(line) - 2]
        return None
    def read_line(self):
        nl = self.r_file.readline()
        while nl is not None and len(nl) == 0:
            print(nl)
            nl = self.r_file.readline()
        return nl

    def add_node(self, line_t):
        #node_line = '"{}",\n'.format(line_t)
        node_line = '{}\n'.format(line_t)
        self.r_file.writelines(str(node_line))
        #print(node_line)
        self.r_file.flush()        
    def close(self):
        if self.r_file:
            self.r_file.close()
            self.r_file = None
