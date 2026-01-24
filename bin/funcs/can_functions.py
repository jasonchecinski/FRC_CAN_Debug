import pandas as pd
import bin.classes.can_classes as cc
import bin.funcs.global_functions as gf
import bin.formats.vars as vars
import bin.formats.tables as tables

def get_can_from_xlsx(filename: str, logging_source: str["Innomaker", "GUI CSV Output"]):

    #Find file path
    path = gf.find_file_path(filename)

    #Read file into pandas dataframe
    if logging_source == "Innomaker": file_pd = pd.read_excel(path)
    elif logging_source == "GUI CSV Output": file_pd = pd.read_csv(path)
    else: raise ValueError(f"Unknown logging source: {logging_source}")

    #Extract CAN data
    can_data = file_pd[vars.CANlogColumns[logging_source]].values.tolist()
    return cc.CAN_log(can_data, logging_source)

def get_can_table(filename: str, logging_source: str):
    can_log = get_can_from_xlsx(filename, logging_source)
    table = can_log.get_cntr_table()
    print("\n=== Controller Table ===")
    for row in table:
        print(row)
    print("========================\n")

def replay_can_bus(filename: str, logging_source: str):
    running = True
    can_log = get_can_from_xlsx(filename, logging_source)

    start_time = gf.get_time("epoch")
    prev_time = start_time

    live_can_system = cc.Live_CAN_System()

    try:
        while running:
            msgs = can_log.get_msgs(start_time, prev_time)
            live_can_system.send_can_msgs(msgs)
            live_can_system.read_can_msgs()

            if gf.get_time("epoch") - start_time > can_log.ts_end:
                running = False

            prev_time = gf.get_time("epoch")
            gf.wait(vars.can_ds)

    except KeyboardInterrupt:
        live_can_system.end_live_CAN_system()

def read_can_bus():
    running = True
    start_time = gf.get_time("epoch")
    live_can_system = cc.Live_CAN_System()

    try:
        while running:
            live_can_system.read_can_msgs()
            prev_time = gf.get_time("epoch")
            gf.wait(vars.can_ds)

    except KeyboardInterrupt:
        live_can_system.end_live_CAN_system()

def get_frameid_info(frameid: int | str):


    if isinstance(frameid, int):
        id_val = frameid
    elif isinstance(frameid, str) and frameid.startswith("0x"):
        id_val = int(frameid[2:], 16)
    else:
        id_val = int(frameid)

    id_bits = format(id_val, "029b")

    device_type = int(id_bits[0:5], 2)
    mfg = int(id_bits[5:13], 2)
    api = int(id_bits[13:23], 2)
    device_number = int(id_bits[23:29], 2)

    global_id = [device_type, mfg, device_number]

    return [global_id, api]

def get_device_type(device_type: int, format: str["int", "hex", "str"]):
    if format == "int": return device_type
    elif format == "hex": return hex(device_type)
    elif format == "str": return tables.device_types_lookup[device_type]
    return "Format not recognized"

def get_mfg(mfg: int, format: str["int", "hex", "str"]):
    if format == "int": return mfg
    elif format == "hex": return hex(mfg)
    elif format == "str": return tables.mfg_lookup[mfg]
    return "Format not recognized"

def get_id(id: int, format: str["int", "hex", "str"]):
    if format == "int": return id
    elif format == "hex":return hex(id)
    elif format == "str":return str(id)
    return "Format not recognized"

def convert_data(input_val: int | list[int], system, output_type: str["List", "Single"]):

    # Innomaker specific handling
    if system.logging_source == "Innomaker" and input_val.startswith("0X|"):
        input_val = input_val[3:]

    # Logs
    if isinstance(input_val, str):

        if len(input_val) > 0:
            hex_str = input_val.replace(" ", "")  
            data_int = int(hex_str, 16)
        else:
            data_int = 0

    elif isinstance(input_val, list):
        hex_str = ''.join([format(byte, '02X') for byte in input_val])
        data_int = int(hex_str, 16)

    if output_type == "List":
        hex_str = format(data_int, "016X")
        bytes_list = [int(hex_str[i:i+2], 16) for i in range(0, 16, 2)]
        return bytes_list

    elif output_type == "Single":
        return data_int

    return None

def convert_frameid(input_val, output_type: str["Int", "Hex", "Hex String"]):

    # Convert input to integer frameid
    if isinstance(input_val, int): frameid_int = input_val
    elif isinstance(input_val, str) and input_val.startswith("0x"): frameid_int = int(input_val[2:], 16)
    else: frameid_int = int(input_val)

    # Convert to desired output type
    if output_type == "Int": return frameid_int
    elif output_type == "Hex": return bytes([frameid_int & 0xFF])
    elif output_type == "Hex String":return format(frameid_int, "016X")

    return None