import os
import time

def find_file_path(filename : str):
    for root, dirs, files in os.walk(os.curdir):
        for file in files:
            if filename == file or file.split(".")[0] == filename:
                return os.path.join(root, file)
    return None

def get_time(output_type : str):

    utc = time.time()

    if output_type == "utc": return utc

def convert_time(input : str | int | float, output_type : str):

    if type(input) == str:
        if "." in input and len(input.split(".")) == 3:
            utc = float(input.split(".")[0]) + (float(input.split(".")[1]) / 1000) + (float(input.split(".")[2]) / 1_000_000)
    elif type(input) == float:
        utc = input

    if output_type == "utc": return utc

def wait_1s(): time.sleep(1)
def wait(t:float): time.sleep(t)