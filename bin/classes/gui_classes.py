import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QStackedWidget, QTableWidgetItem)
from PyQt5.QtCore import QTimer

from bin.classes.screen_classes import (NavigationScreen,InputScreen,PPResultsScreen,LiveCANScreen,LiveDetectScreen)
from bin.formats.gui_formats import GUI_CONFIG, DARK_STYLE
from bin.funcs.global_functions import get_global_logger
import bin.funcs.can_functions as cf
from bin.classes.can_classes import Live_CAN_System


# ============================================================
# Live CAN Controller
# ============================================================
class LiveCANScreenClass(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        self.live_can = None  # created on start_monitor/start_replay

        self.ui = LiveCANScreen(main)
        # use the layout already set on ui
        self.setLayout(self.ui.layout())

        self.timer = QTimer()
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.update_live_data)

        self.ui.pause_btn.clicked.connect(self.toggle_pause)
        self.ui.clear_btn.clicked.connect(self.clear_table)
        self.ui.back_btn.clicked.connect(self.go_back)

        self.paused = False
        self.current_mode = "Standard CAN"

    def start_monitor(self, can_id, mode, timeout):
        self.current_mode = mode
        self.configure_table()

        self.live_can = Live_CAN_System()
        #self.live_can.start_live_CAN_system(can_id, mode, timeout)

        self.paused = False
        self.timer.start()

    def start_replay(self, can_log, mode):
        self.current_mode = mode
        self.configure_table()

        self.live_can = Live_CAN_System()
        self.live_can.start_replay(can_log)

        self.paused = False
        self.timer.start()

    def configure_table(self):
        cfg = GUI_CONFIG["auto_detect"]["column_configs"][self.current_mode]
        table = self.ui.table
        table.setColumnCount(cfg["count"])
        table.setHorizontalHeaderLabels(cfg["columns"])

    def update_live_data(self):
        if self.paused or self.live_can is None:
            return

        self.live_can.read_can_msgs()
        frames = self.live_can.can_frames
        table = self.ui.table

        if self.current_mode == "Standard CAN":
            table.setRowCount(len(frames))
            for row, f in enumerate(frames):
                table.setItem(row, 0, QTableWidgetItem(str(f.timestamp)))
                table.setItem(row, 1, QTableWidgetItem(hex(f.frameid)))
                table.setItem(row, 2, QTableWidgetItem(f.data_hex))
        else:
            cntrs = self.live_can.cntrs_obj
            table.setRowCount(len(cntrs))
            for row, cntr in enumerate(cntrs):
                table.setItem(row, 0, QTableWidgetItem(cntr.get_model()))
                table.setItem(row, 1, QTableWidgetItem(cntr.get_mfg("str")))
                table.setItem(row, 2, QTableWidgetItem(str(cntr.get_id("str"))))
                table.setItem(row, 3, QTableWidgetItem(str(cntr.api)))
                for i, b in enumerate(cntr.data_bytes):
                    table.setItem(row, 4 + i, QTableWidgetItem(str(b)))

    def toggle_pause(self):
        self.paused = not self.paused
        self.ui.pause_btn.setText("Resume" if self.paused else "Pause")

    def clear_table(self):
        if self.live_can:
            self.live_can.can_frames = []
            self.live_can.cntrs_obj = []
            self.live_can.cntrs_global_ids = []
        self.ui.table.setRowCount(0)

    def go_back(self):
        self.timer.stop()
        if self.live_can:
            self.live_can.end_live_CAN_system()
        self.main.go_rt_menu()

class LiveDetectScreenClass(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        self.live_can = None  # created when auto-detect starts

        self.ui = LiveDetectScreen(main)
        self.setLayout(self.ui.layout())

        self.timer = QTimer()
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.update_live_data)

        self.ui.reset_btn.clicked.connect(self.reset_detection)
        self.ui.back_btn.clicked.connect(self.go_back)

    def start_auto_detect(self):
        self.live_can = Live_CAN_System()
        self.timer.start()

    def update_live_data(self):
        if self.live_can is None:
            return

        self.live_can.read_can_msgs()

        cntrs = self.live_can.cntrs_obj
        table = self.ui.table
        table.setRowCount(len(cntrs))

        for row, cntr in enumerate(cntrs):
            values = [
                cntr.get_model(),
                cntr.get_mfg("str"),
                cntr.get_id("str"),
                ", ".join(str(a) for a in sorted(cntr.apis)),
                cntr.status,
                f"{cntr.last_seen:.2f}",
                f"{cntr.latency:.3f}"
            ]
            for col, val in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(val))

    def reset_detection(self):
        if self.live_can:
            self.live_can.can_frames = []
            self.live_can.cntrs_obj = []
            self.live_can.cntrs_global_ids = []

    def go_back(self):
        self.timer.stop()
        if self.live_can:
            self.live_can.end_live_CAN_system()
        self.main.go_home()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.log = get_global_logger()
        self.setStyleSheet(DARK_STYLE)
        self.resize(1400, 900)

        cfg = GUI_CONFIG
        nav_cfg = cfg["navigation_screens"]
        input_cfg = cfg["input_screens"]

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Screens
        self.home = NavigationScreen(self, nav_cfg["home"])
        self.rt_setup = NavigationScreen(self, nav_cfg["rt_setup"])
        self.rt_menu = NavigationScreen(self, nav_cfg["rt_menu"])

        self.pp_input = InputScreen(self, input_cfg["pp_input"])
        self.live_can_input = InputScreen(self, input_cfg["live_can_input"])
        self.replay_log_input = InputScreen(self, input_cfg["replay_log_input"])

        self.live_can_screen = LiveCANScreenClass(self)
        self.auto_detect = LiveDetectScreenClass(self)

        self.pp_results = PPResultsScreen(self)

        for screen in [
            self.home,
            self.rt_setup,
            self.rt_menu,
            self.pp_input,
            self.live_can_input,
            self.replay_log_input,
            self.auto_detect,
            self.live_can_screen,
            self.pp_results,
        ]:
            self.stack.addWidget(screen)

        # Wire navigation buttons
        self._wire_navigation(self.home)
        self._wire_navigation(self.rt_setup)
        self._wire_navigation(self.rt_menu)

        # Wire input screens
        self._wire_inputs()

        # Wire PP results back
        self.pp_results.btn_back.clicked.connect(self.go_home)

        self.go_home()

    # ---------------- Navigation wiring ----------------
    def _wire_navigation(self, nav_screen):
        for b in nav_screen.buttons:
            b.clicked.connect(lambda _, a=b.action: self.handle_action(a))
        if nav_screen.bottom_button:
            nav_screen.bottom_button.clicked.connect(
                lambda _, a=nav_screen.bottom_button.action: self.handle_action(a)
            )

    def handle_action(self, action):
        if action == "exit":
            sys.exit(0)
        if hasattr(self, action):
            getattr(self, action)()

    # ---------------- Input wiring ----------------
    def _wire_inputs(self):
        # PP input
        self.pp_input.btn_run.clicked.connect(
            lambda: self.run_pp(self.get_input_values(self.pp_input))
        )
        self.pp_input.btn_back.clicked.connect(self.go_home)

        # Live CAN input
        self.live_can_input.btn_run.clicked.connect(
            lambda: self.run_live_can(self.get_input_values(self.live_can_input))
        )
        self.live_can_input.btn_back.clicked.connect(self.go_rt_menu)

        # Replay log input
        self.replay_log_input.btn_run.clicked.connect(
            lambda: self.run_replay_log(self.get_input_values(self.replay_log_input))
        )
        self.replay_log_input.btn_back.clicked.connect(self.go_rt_menu)

    def get_input_values(self, screen):
        values = []
        for ftype, widget in screen.fields:
            if ftype == "text":
                values.append(widget.text())
            elif ftype == "dropdown":
                values.append(widget.currentText())
            elif ftype == "file":
                values.append(widget.text())
        return values

    # ---------------- Navigation methods ----------------
    def go_home(self):
        self.stack.setCurrentWidget(self.home)

    def go_pp(self):
        self.stack.setCurrentWidget(self.pp_input)

    def go_rt(self):
        self.stack.setCurrentWidget(self.rt_setup)

    def go_rt_menu(self):
        self.stack.setCurrentWidget(self.rt_menu)

    def go_live_can_input(self):
        self.stack.setCurrentWidget(self.live_can_input)

    def go_replay_log_input(self):
        self.stack.setCurrentWidget(self.replay_log_input)

    def go_auto_detect(self):
        # start auto-detect when entering screen
        self.auto_detect.start_auto_detect()
        self.stack.setCurrentWidget(self.auto_detect)

    # ---------------- Run actions ----------------
    def run_pp(self, data):
        file_path, logging_source = data
        can_log = cf.get_can_from_xlsx(file_path, logging_source)
        table = can_log.get_cntr_table()

        self.pp_results.table.setRowCount(0)
        for row_data in table:
            row = self.pp_results.table.rowCount()
            self.pp_results.table.insertRow(row)
            for col, value in enumerate(row_data):
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                self.pp_results.table.setItem(row, col, QTableWidgetItem(str(value)))

        self.stack.setCurrentWidget(self.pp_results)

    def run_live_can(self, data):
        can_id, mode, timeout = data
        self.live_can_screen.start_monitor(can_id, mode, timeout)
        self.stack.setCurrentWidget(self.live_can_screen)

    def run_replay_log(self, data):
        file_path, logging_source, mode = data
        can_log = cf.get_can_from_xlsx(file_path, logging_source)
        cf.replay_can_bus(file_path, logging_source)
        self.live_can_screen.start_replay(can_log, mode)
        self.stack.setCurrentWidget(self.live_can_screen)