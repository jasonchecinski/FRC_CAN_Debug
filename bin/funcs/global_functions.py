import os
import time
import logging

def get_global_logger():
    """
    Returns a global logger instance.
    Creates bin/output_files/logs/app.log if missing.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, "output_files", "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "app.log")

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    logger = logging.getLogger("CANApp")
    logger.info("Global logger initialized")
    return logger




def find_file_path(filename : str):
    if os.path.isabs(filename) and os.path.exists(filename):
        return filename
    else:
        for root, dirs, files in os.walk(os.curdir):
            for file in files:
                if filename == file or file.split(".")[0] == filename:
                    return os.path.join(root, file)
    raise ValueError(f"File not found: {filename}")

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