import pandas as pd
import bin.classes.can_classes as cc
import bin.funcs.global_functions as gf
import bin.formats.vars as vars
import bin.formats.tables as tables

def read_can_bus():
    
    running = True
    start_time = gf.get_time("utc")
    live_can_system = cc.Live_CAN_System()
    try:
        while running:
            live_can_system.read_can_msgs()
            prev_time = gf.get_time("utc")
            gf.wait(vars.can_ds)
    except KeyboardInterrupt: live_can_system.end_live_CAN_system()

def replay_can_bus(filename:str, log_type : str):

    running = True
    can_log = get_can_from_xlsx(filename,log_type)
    start_time = gf.get_time("utc")
    prev_time = start_time
    live_can_system = cc.Live_CAN_System()
    try:
        while running:
            live_can_system.send_can_msgs(can_log.get_msgs(start_time,prev_time))
            live_can_system.read_can_msgs()
            if gf.get_time("utc") - start_time > can_log.ts_end: running = False
            prev_time = gf.get_time("utc")
            gf.wait(vars.can_ds)
    except KeyboardInterrupt: live_can_system.end_live_CAN_system()

def get_can_table(filename:str, log_type : str):
    can_log = get_can_from_xlsx(filename,log_type)
    table = can_log.get_cntr_table()
    for row in table:
        print(row)

def get_can_from_xlsx(filename:str, log_type : str):
    
    file_pd = pd.read_excel(gf.find_file_path(filename))
    if log_type == "InnoMaker":
        can_data = file_pd[vars.innoMakerCANlogColumns].values.tolist()
    CL = cc.CAN_log(can_data, log_type)
    return CL

def get_frameid_info(frameid : int | hex | str):

    if type(frameid) == int: id = frameid
    elif type(frameid) == hex: id = int(frameid,16)
    elif type(frameid) == str:
        if frameid[0:2] == "0x": id = int(frameid[2:],16)

    id_bool = format(id,'029b')
    device_type = int(id_bool[0:5],2)
    mfg = int(id_bool[5:13],2)
    api = int(id_bool[13:23],2)
    device_number = int(id_bool[23:29],2)
    global_id = [device_type,mfg,device_number]

    return[global_id,api]

def get_device_type(device_type : int, format: str):
    if format == "int": return(device_type)
    elif format == "hex": return(hex(device_type))
    elif format == "str": return(tables.device_types_lookup[device_type])
    else: return("Format not Recongnized")

def get_mfg(mfg : int, format: str):
    if format == "int": return(mfg)
    elif format == "hex": return(hex(mfg))
    elif format == "str": return(tables.mfg_lookup[mfg])
    else: return("Format not Recongnized")

def get_id(id : int, format: str):
    if format == "int": return(id)
    elif format == "hex": return(hex(id))
    elif format == "str": return(str(id))
    else: return("Format not Recongnized")

def convert_data(input : str | int | float | hex, system, output_type : str["List","Single"], data_format : str["Hex","Hex String","Int"]):

    data_int = 0
    if system.time_type == "Log" and system.mfg == "InnoMaker" and input[0:3] == "0X|" and len(input[3:]) != 0: data_int = int(input[3:].replace(" ",""),16)
    elif system.time_type == "Live" and system.mfg == "InnoMaker":
        data_int = input

    if output_type == "List":
        data_list = []
        for i in range(0,16,2): 
            data_list.append(format(data_int,"016X")[i:i+2])
        output = []
        for i in range(0,8):
            if data_format == "Hex String": output.append(data_list[i])
            elif data_format == "Int": output.append(int(data_list[i],16))
            elif data_format == "Hex": output.append(bytes(int(data_list[i],16)))
    elif output_type == "Single":
        if data_format == "Hex String": output = format(data_int,"016X")
        elif data_format == "Int": output = data_int
        elif data_format == "Hex": output = bytes(data_int)
        else: output = None

    return output

def convert_frameid(input : str | int | float | hex, system, output_type : str["Hex","Hex String","Int"]):
    
    if system.time_type == "Log" and system.mfg == "InnoMaker"  and input[0:2] == "0x":
        frameid_int = int(input[2:],16)
    elif system.time_type == "Live" and system.mfg == "InnoMaker":
        frameid_int = input
    if output_type == "Int": return frameid_int
    elif output_type == "Hex": return bytes(frameid_int)
    elif output_type == "Hex String": return format(frameid_int,"016X")
    else: return None