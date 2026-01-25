device_types_lookup = {
    0: "Broadcast Messages",
    1: "Robot Controller",
    2: "Motor Controller",
    3: "Relay Controller",
    4: "Gyro Sensor",
    5: "Accelerometer",
    6: "Distance Sensor",
    7: "Encoder",
    8: "Power Distribution Module",
    9: "Pneumatics Controller",
    10: "Miscellaneous",
    11: "IO Breakout",
    12: "Servo Controller",
    13: "Color Sensor",
    **{i: "Reserved" for i in range(14, 31)},
    31: "Firmware Update"
}

mfg_lookup = {
    0: "Broadcast",
    1: "NI",
    2: "Luminary Micro",
    3: "DEKA",
    4: "CTRE",
    5: "REV Robotics",
    6: "Grapple",
    7: "MindSensors",
    8: "Team Use",
    9: "Kauai Labs",
    10: "Copperforge",
    11: "Playing With Fusion",
    12: "Studica",
    13: "The Thrifty Bot",
    14: "Redux Robotics",
    15: "AndyMark",
    16: "Vivid Hosting",
    17: "Vertos Robotics",
    18: "SWYFT Robotics",
    19: "Lumyn Labs",
    20: "Brushland Labs",
    **{i: "Reserved" for i in range(21, 256)}
}

api_class = {
    0: "Voltage Control Mode",
    1: "Speed Control Mode",
    2: "Voltage Compensation Mode",
    3: "Position Control Mode",
    4: "Current Control Mode",
    5: "Status",
    6: "Periodic Status",
    7: "Configuration",
    8: "Ack"
}

api_index = {
    0: "Enable Control",
    1: "Disable Control",
    2: "Set Setpoint",
    3: "P Constant",
    4: "I Constant",
    5: "D Constant",
    6: "Set Reference",
    7: "Trusted Enable",
    8: "Trusted Set No Ack",
    10: "Trusted Set Setpoint No Ack",
    11: "Set Setpoint No Ack"
}