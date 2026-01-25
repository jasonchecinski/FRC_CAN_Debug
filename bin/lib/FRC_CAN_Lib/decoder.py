import os
import yaml
from struct import unpack

# ------------------------------------------------------------
# Global registry: {(manufacturer, device_type): {api: message_def}}
# ------------------------------------------------------------
DECODER_REGISTRY = {}

# ------------------------------------------------------------
# Load all YAML files under FRC_CAN_Lib recursively
# ------------------------------------------------------------
def load_all_decoders(base_path=None):
    """
    Recursively loads all YAML decoder files under FRC_CAN_Lib.
    """
    global DECODER_REGISTRY

    if base_path is None:
        base_path = os.path.join("bin", "lib", "FRC_CAN_Lib")

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".yaml"):
                full_path = os.path.join(root, file)
                with open(full_path, "r") as f:
                    data = yaml.safe_load(f)

                mfg = data["device"]["manufacturer"]
                dtype = data["device"]["device_type"]
                messages = data.get("messages", {})

                key = (mfg, dtype)
                if key not in DECODER_REGISTRY:
                    DECODER_REGISTRY[key] = {}

                # Merge API definitions
                for api, msg_def in messages.items():
                    DECODER_REGISTRY[key][int(api)] = msg_def


# ------------------------------------------------------------
# Helper: extract integer from bytes
# ------------------------------------------------------------
def extract_value(data, start, length, signed=False):
    """
    Extracts an integer from the CAN data payload.
    """
    raw = data[start:start+length]

    if length == 1:
        return raw[0]

    if length == 2:
        return unpack("<h" if signed else "<H", raw)[0]

    if length == 4:
        return unpack("<i" if signed else "<I", raw)[0]

    # fallback: return raw bytes
    return int.from_bytes(raw, byteorder="little", signed=signed)


# ------------------------------------------------------------
# Main decode function
# ------------------------------------------------------------
def decode_frame(manufacturer, device_type, api, data_bytes):
    """
    Decodes a CAN frame using the loaded YAML definitions.

    manufacturer: string ("CTRE")
    device_type: string ("MotorController")
    api: integer (e.g., 287)
    data_bytes: bytes object of length 8
    """

    key = (manufacturer, device_type)

    if key not in DECODER_REGISTRY:
        return {"error": "Unknown device type", "raw": list(data_bytes)}

    device_messages = DECODER_REGISTRY[key]

    if api not in device_messages:
        return {"error": "Unknown API for this device", "raw": list(data_bytes)}

    msg_def = device_messages[api]
    fields = msg_def.get("fields", [])

    decoded = {
        "message_name": msg_def.get("name", f"API_{api}"),
        "fields": {}
    }

    for field in fields:
        name = field["name"]
        start = field["start"]
        length = field["length"]
        ftype = field.get("type", "uint")
        scale = field.get("scale", 1)
        unit = field.get("unit", None)

        signed = ftype.startswith("int")

        value = extract_value(data_bytes, start, length, signed=signed)

        # Apply scaling
        if isinstance(scale, str) and "/" in scale:
            # e.g., "1/32767"
            num, den = scale.split("/")
            scale = float(num) / float(den)

        value = value * scale

        # Store result
        if unit:
            decoded["fields"][name] = f"{value} {unit}"
        else:
            decoded["fields"][name] = value

    return decoded


# ------------------------------------------------------------
# Initialize registry on import
# ------------------------------------------------------------
load_all_decoders()