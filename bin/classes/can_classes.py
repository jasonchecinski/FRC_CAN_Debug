import time
import can
import bin.formats.vars as vars
import bin.funcs.can_functions as cf
import bin.funcs.global_functions as gf

class CAN_bus:

    def __init__(self): 
        self.bus = can.interface.Bus(interface = vars.innoMakerCANtool_interface,channel='1',bitrate=vars.can_baudrate)
        self.reader = can.BufferedReader()
        self.notifier = can.Notifier(self.bus, [self.reader])
    
    def read_can_messages(self): 
        msgs = []
        for _ in range(0,vars.max_can_read):
            msg = self.reader.get_message(timeout=0.0)
            if msg: msgs.append(msg)
            else: break
        return msgs

    def send_msg(self,msg):
        for i in range(0,5):
            try:
                self.bus.send(msg)
                return
            except can.CanError:
                gf.wait(vars.can_ds)
        print("Message NOT sent")

    def stop_bus(self): self.bus.shutdown()

class Live_CAN_System:

    def __init__(self):
        self.time_type = "Live"
        self.mfg = "InnoMaker"
        self.cb = CAN_bus()
        self.read_first_msg = False
        self.ts_start = 0
        self.can_frames = []
        self.cntrs_obj = []
        self.cntrs_global_ids = []
        self.online_cntrs = []
    
    def get_curr_cntrs(self, can_data):
        for msg in can_data:
            if msg in self.cntrs_ext_id:
                for cntr in self.cntrs_obj:
                    cntr.device_seen()
            else:
                self.cntrs_obj.append(Controller(msg))

    def send_can_msgs(self,can_frames):
        if not(can_frames in [None,[]]):        
            for can_frame in can_frames:
                #msg = can.Message(arbitration_id=0x204F954, data=[0x00,0x00,0x00] , is_extended_id=True)
                msg = can.Message(arbitration_id=0x123, data=[0x11, 0x22, 0x33, 0x44], is_extended_id=False)
                self.cb.send_msg(msg)

    def read_can_msgs(self):
        msgs = self.cb.read_can_messages()
        for msg in msgs:
            if self.ts_start == 0: self.ts_start = msg.timestamp
            self.can_frames.append(CAN_Frame(self, msg.timestamp, msg.arbitration_id, msg.data))
        print(len(self.cntrs_obj))

    def add_cntr(self,global_id : list[int]):
        self.cntrs_global_ids.append(global_id)
        self.cntrs_obj.append(Controller(self,global_id))

    def update_cntrs(self):
        for cntr in self.cntrs:
            cntr.ping_device()

    def end_live_CAN_system(self):
        self.cb.stop_bus()

class CAN_log:

    def __init__(self, can_data : list, mfg : str):
        self.mfg = "InnoMaker"
        self.time_type = "Log"
        self.ts_start = 1000
        self.ts_end = 0
        self.can_frames = []
        self.cntrs_obj = []
        self.cntrs_global_ids = []
        self.online_cntrs = []
        for msg in can_data:
            if mfg == "InnoMaker":
                self.can_frames.append(CAN_Frame(self, msg[0], msg[1], msg[2]))
        for frame in self.can_frames:
            frame.rel_ts = frame.ts - self.ts_start

    def add_cntr(self,global_id : list[int]):
        self.cntrs_global_ids.append(global_id)
        self.cntrs_obj.append(Controller(self,global_id))

    def get_cntr_table(self):
        table_data = []
        for cntr in self.cntrs_obj:
            table_data.append([cntr.get_device_type("str"),cntr.get_mfg("str"),cntr.get_id("str"),cntr.apis])
        return table_data

    def get_msgs(self, start_time : float, prev_time : float):
        msgs = []
        start_rel_t = prev_time - start_time
        end_rel_t = gf.get_time("utc") - start_time
        if start_rel_t == 0: return [self.can_frames[0]]
        else:
            for frame in self.can_frames:
                if frame.rel_ts > start_rel_t and frame.rel_ts <= end_rel_t:
                    msgs.append(frame)
        return msgs

class CAN_Frame:

    def __init__(self, system : Live_CAN_System | CAN_log,ts,frameid,data):
        self.system = system
        self.ts = gf.convert_time(ts,"utc")
        self.frameid = cf.convert_frameid(frameid,self.system,"Int")
        self.data = cf.convert_data(data,self.system,"Single","Int")
        self.global_id,self.api = cf.get_frameid_info(self.frameid)
        if self.api in vars.bad_apis: return
        self.find_cntr()
        if self.system.time_type == "Log": self.update_log()

    def find_cntr(self):

        if not(self.global_id in self.system.cntrs_global_ids): self.system.add_cntr(self.global_id)
        
        for cntr in self.system.cntrs_obj:
            if cntr.global_id == self.global_id:
                self.cntr = cntr
            
    def update_log(self):
        if self.ts < self.system.ts_start: self.system.ts_start = self.ts
        if self.ts > self.system.ts_end: self.system.ts_end = self.ts
        if self.api not in self.cntr.apis: self.cntr.apis.append(self.api)

class Controller:
    
    def __init__(self, system : Live_CAN_System | CAN_log, global_id: list [int]):
        self.system = system
        self.global_id = global_id
        self.device_type = global_id[0]
        self.mfg = global_id[1]
        self.id = global_id[2]
        self.apis = []

        if self.system.time_type == "live":
            self.detect_time = time.time()
            self.last_seen = time.time()
            self.latency = 0
            self.status = "Online"

    def device_seen(self):
        self.latency = time.time() - self.last_seen
        self.last_seen = time.time()
        self.status = "Online"

    def ping_device(self):
        self.curr_lat = time.time() - self.last_seen
        if self.curr_lat > vars.cntr_offline_debounce: self.status = "Offline"

    def get_device_type(self, format: str): return cf.get_device_type(self.device_type,format)
    def get_mfg(self, format: str): return cf.get_mfg(self.mfg,format)
    def get_id(self, format: str): return cf.get_id(self.id,format)