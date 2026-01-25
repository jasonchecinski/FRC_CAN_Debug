import os
import yaml

ALL_DEVICE_DEFINITIONS = []

def load_all_device_definitions(base_path=None):
    """
    Loads all YAML device definition files from the FRC_CAN_Lib folder.
    """
    global ALL_DEVICE_DEFINITIONS

    if base_path is None:
        base_path = os.path.join("bin", "lib", "FRC_CAN_Lib")

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".yaml"):
                full_path = os.path.join(root, file)
                with open(full_path, "r") as f:
                    data = yaml.safe_load(f)

                # Validate structure
                if "device" not in data or "api_usage" not in data:
                    print(f"Warning: YAML missing required fields: {full_path}")
                    continue

                ALL_DEVICE_DEFINITIONS.append(data)

def identify_device(cntr):

    candidates = []

    for device_yaml in ALL_DEVICE_DEFINITIONS:
        dev = device_yaml["device"]

        if dev["manufacturer"] != cntr.get_mfg("str"): continue
        #if dev["device_type"] != cntr.get_device_type("str"): continue

        always_used = device_yaml["api_usage"].get("always_used", [])
        sometimes_used = device_yaml["api_usage"].get("sometimes_used", [])
        never_used = device_yaml["api_usage"].get("never_used", [])

        if any(api in never_used for api in cntr.apis):continue
        if not all(api in cntr.apis for api in always_used):continue
        score = sum(api in cntr.apis for api in sometimes_used)

        candidates.append((score, dev["name"]))

    if not candidates: return "Unknown"
    candidates.sort(reverse=True)
    return candidates[0][1]

load_all_device_definitions()