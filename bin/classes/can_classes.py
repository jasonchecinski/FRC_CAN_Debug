import time
import can
import bin.formats.vars as vars
import bin.funcs.can_functions as cf
import bin.funcs.global_functions as gf

class CAN_bus:
    def __init__(self):
        self.bus = can.interface.Bus(
            interface=vars.innoMakerCANtool_interface,
            channel="1",
            bitrate=vars.can_baudrate,
        )
        self.reader = can.BufferedReader()
        self.notifier = can.Notifier(self.bus, [self.reader])

    def read_can_messages(self):
        msgs = []
        for _ in range(vars.max_can_read):
            msg = self.reader.get_message(timeout=0.0)
            if msg:
                msgs.append(msg)
            else:
                break
        return msgs

    def send_msg(self, msg):
        for _ in range(5):
            try:
                self.bus.send(msg)
                return
            except can.CanError:
                gf.wait(vars.can_ds)
        print("Message NOT sent")

    def stop_bus(self):
        self.bus.shutdown()

class Live_CAN_System:
    def __init__(self):
        self.time_type = "Live"
        self.mfg = "Innomaker"
        self.cb = CAN_bus()

        self.ts_start = 0
        self.can_frames = []
        self.cntrs_obj = []
        self.cntrs_global_ids = []

    def read_can_msgs(self):
        msgs = self.cb.read_can_messages()

        for msg in msgs:
            if self.ts_start == 0:
                self.ts_start = msg.timestamp

            self.can_frames.append(
                CAN_Frame(
                    self,
                    msg.timestamp,
                    msg.arbitration_id,
                    list(msg.data)
                )
            )

        return msgs

    def send_can_msgs(self, frames):
        if not frames:
            return

        for frame in frames:
            msg = can.Message(
                arbitration_id=frame.frameid,
                data=frame.data,
                is_extended_id=False
            )
            self.cb.send_msg(msg)

    def add_cntr(self, global_id):
        self.cntrs_global_ids.append(global_id)
        self.cntrs_obj.append(Controller(self, global_id))

    def end_live_CAN_system(self):
        self.cb.stop_bus()

class CAN_log:
    def __init__(self, can_data, logging_source):
        self.mfg = logging_source
        self.time_type = "Log"

        self.ts_start = float("inf")
        self.ts_end = 0

        self.can_frames = []
        self.cntrs_obj = []
        self.cntrs_global_ids = []

        for msg in can_data:
            timestamp = msg[0]
            frameid = msg[1]
            data = msg[2]

            frame = CAN_Frame(self, timestamp, frameid, data)
            self.can_frames.append(frame)

        for frame in self.can_frames:
            frame.rel_ts = frame.ts - self.ts_start

    def add_cntr(self, global_id):
        self.cntrs_global_ids.append(global_id)
        self.cntrs_obj.append(Controller(self, global_id))

    def get_cntr_table(self):
        table = []
        for cntr in self.cntrs_obj:
            table.append([
                cntr.get_device_type("str"),
                cntr.get_mfg("str"),
                cntr.get_id("str"),
                cntr.apis
            ])
        return table

    def get_msgs(self, start_time, prev_time):
        msgs = []
        start_rel = prev_time - start_time
        end_rel = gf.get_time("utc") - start_time

        if start_rel == 0:
            return [self.can_frames[0]]

        for frame in self.can_frames:
            if start_rel < frame.rel_ts <= end_rel:
                msgs.append(frame)

        return msgs

class CAN_Frame:
    def __init__(self, system, ts, frameid, data):
        self.system = system
        self.ts = gf.convert_time(ts, "utc")
        self.frameid = cf.convert_frameid(frameid, system, "Int")
        self.data = cf.convert_data(data, system, "List", "Int")
        self.global_id, self.api = cf.get_frameid_info(self.frameid)
        if self.api in vars.bad_apis: return
        self.find_cntr()
        if self.system.time_type == "Log": self.update_log()

    def find_cntr(self):
        if self.global_id not in self.system.cntrs_global_ids:
            self.system.add_cntr(self.global_id)

        for cntr in self.system.cntrs_obj:
            if cntr.global_id == self.global_id:
                self.cntr = cntr

    def update_log(self):
        if self.ts < self.system.ts_start:
            self.system.ts_start = self.ts
        if self.ts > self.system.ts_end:
            self.system.ts_end = self.ts

        if self.api not in self.cntr.apis:
            self.cntr.apis.append(self.api)

class Controller:
    def __init__(self, system, global_id):
        self.system = system
        self.global_id = global_id

        self.device_type = global_id[0]
        self.mfg = global_id[1]
        self.id = global_id[2]

        self.apis = []

        if self.system.time_type == "Live":
            self.detect_time = time.time()
            self.last_seen = time.time()
            self.latency = 0
            self.status = "Online"

    def device_seen(self):
        self.latency = time.time() - self.last_seen
        self.last_seen = time.time()
        self.status = "Online"

    def ping_device(self):
        if time.time() - self.last_seen > vars.cntr_offline_debounce:
            self.status = "Offline"

    def get_device_type(self, fmt): return cf.get_device_type(self.device_type, fmt)
    def get_mfg(self, fmt): return cf.get_mfg(self.mfg, fmt)
    def get_id(self, fmt): return cf.get_id(self.id, fmt)