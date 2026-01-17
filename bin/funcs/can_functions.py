import pandas as pd
import bin.classes.can_classes as cc
import bin.funcs.global_functions as gf
import bin.formats.vars as vars
import bin.formats.tables as tables
import os


# ---------------------------------------------------------
# Load CAN data from Excel or CSV depending on logging source
# ---------------------------------------------------------
def get_can_from_xlsx(filename: str, logging_source: str):
    """
    Loads CAN data from either:
    - Innomaker Excel logs
    - GUI CSV Output logs

    Returns a CAN_log object.
    """
    if os.path.isabs(filename) and os.path.exists(filename):
        path = filename
    else:
        # fallback to your helper
        path = gf.find_file_path(filename)

    if path is None:
        raise ValueError(f"File not found: {filename}")

    # -----------------------------
    # Innomaker Excel Log
    # -----------------------------
    if logging_source == "Innomaker":
        file_pd = pd.read_excel(path)
        can_data = file_pd[vars.innoMakerCANlogColumns].values.tolist()

        # Format: [timestamp, frameid, data_string]
        # CAN_log will interpret this correctly
        return cc.CAN_log(can_data, "Innomaker")

    # -----------------------------
    # GUI CSV Output Log
    # -----------------------------
    elif logging_source == "GUI CSV Output":
        file_pd = pd.read_csv(path)

        # Expect columns: timestamp, id, data
        can_data = []
        for _, row in file_pd.iterrows():
            timestamp = row["timestamp"]
            frameid = row["id"]

            # Convert "11 22 33" → [0x11, 0x22, 0x33]
            data_str = str(row["data"]).strip()
            data_bytes = []
            if data_str:
                try:
                    data_bytes = [int(b, 16) for b in data_str.split()]
                except:
                    data_bytes = []

            can_data.append([timestamp, frameid, data_bytes])

        return cc.CAN_log(can_data, "GUI CSV Output")

    else:
        raise ValueError(f"Unknown logging source: {logging_source}")


# ---------------------------------------------------------
# Print controller table (PP screen)
# ---------------------------------------------------------
def get_can_table(filename: str, logging_source: str):
    """
    Loads a CAN log and prints the controller table.
    """
    can_log = get_can_from_xlsx(filename, logging_source)
    table = can_log.get_cntr_table()

    print("\n=== Controller Table ===")
    for row in table:
        print(row)
    print("========================\n")


# ---------------------------------------------------------
# Replay CAN Bus (used by Replay Log screen)
# ---------------------------------------------------------
def replay_can_bus(filename: str, logging_source: str):
    """
    Replays CAN messages from a log file onto the CAN bus.
    """
    running = True
    can_log = get_can_from_xlsx(filename, logging_source)

    start_time = gf.get_time("utc")
    prev_time = start_time

    live_can_system = cc.Live_CAN_System()

    try:
        while running:
            msgs = can_log.get_msgs(start_time, prev_time)
            live_can_system.send_can_msgs(msgs)
            live_can_system.read_can_msgs()

            if gf.get_time("utc") - start_time > can_log.ts_end:
                running = False

            prev_time = gf.get_time("utc")
            gf.wait(vars.can_ds)

    except KeyboardInterrupt:
        live_can_system.end_live_CAN_system()


# ---------------------------------------------------------
# Read CAN Bus (live mode)
# ---------------------------------------------------------
def read_can_bus():
    """
    Continuously reads from the CAN bus and processes frames.
    """
    running = True
    start_time = gf.get_time("utc")
    live_can_system = cc.Live_CAN_System()

    try:
        while running:
            live_can_system.read_can_msgs()
            prev_time = gf.get_time("utc")
            gf.wait(vars.can_ds)

    except KeyboardInterrupt:
        live_can_system.end_live_CAN_system()


# ---------------------------------------------------------
# Frame ID decoding
# ---------------------------------------------------------
def get_frameid_info(frameid: int | str):
    """
    Extracts:
    - device_type (5 bits)
    - manufacturer (8 bits)
    - API (10 bits)
    - device_number (6 bits)
    """

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


# ---------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------
def get_device_type(device_type: int, format: str):
    if format == "int":
        return device_type
    elif format == "hex":
        return hex(device_type)
    elif format == "str":
        return tables.device_types_lookup[device_type]
    return "Format not recognized"


def get_mfg(mfg: int, format: str):
    if format == "int":
        return mfg
    elif format == "hex":
        return hex(mfg)
    elif format == "str":
        return tables.mfg_lookup[mfg]
    return "Format not recognized"


def get_id(id: int, format: str):
    if format == "int":
        return id
    elif format == "hex":
        return hex(id)
    elif format == "str":
        return str(id)
    return "Format not recognized"


# ---------------------------------------------------------
# Data conversion
# ---------------------------------------------------------
def convert_data(input_val, system, output_type: str, data_format: str):
    """
    Normalizes data into either:
    - list of ints
    - single int
    """
    # GUI CSV Output already passes list[int]
    if isinstance(input_val, list):
        if output_type == "Single":
            return int.from_bytes(bytes(input_val), "big")
        return input_val

    # Innomaker Excel logs
    if system.time_type == "Log" and system.mfg == "Innomaker":
        if isinstance(input_val, str) and input_val.startswith("0X|"):
            hex_str = input_val[3:].replace(" ", "")
            data_int = int(hex_str, 16)
        else:
            data_int = 0
    else:
        data_int = input_val

    if output_type == "List":
        hex_str = format(data_int, "016X")
        bytes_list = [int(hex_str[i:i+2], 16) for i in range(0, 16, 2)]
        return bytes_list

    if output_type == "Single":
        return data_int

    return None


# ---------------------------------------------------------
# Frame ID conversion
# ---------------------------------------------------------
def convert_frameid(input_val, system, output_type: str):
    """
    Converts frame ID into int, hex string, or bytes.
    """

    if isinstance(input_val, int):
        frameid_int = input_val

    elif isinstance(input_val, str) and input_val.startswith("0x"):
        frameid_int = int(input_val[2:], 16)

    else:
        frameid_int = int(input_val)

    if output_type == "Int":
        return frameid_int
    elif output_type == "Hex":
        return bytes([frameid_int & 0xFF])
    elif output_type == "Hex String":
        return format(frameid_int, "016X")

    return None