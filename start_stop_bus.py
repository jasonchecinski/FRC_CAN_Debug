#Run this if you get a "Bus didnt shutdown error"

import can
bus = can.interface.Bus(interface='gs_usb',channel='1',bitrate=1000000)
bus.shutdown()