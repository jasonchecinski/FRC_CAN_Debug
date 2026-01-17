import sys
import os
import csv
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QLineEdit, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QComboBox
)
from PyQt5.QtCore import Qt, QTimer

from bin.formats.gui_formats import GUI_CONFIG, DARK_STYLE
from bin.funcs.global_functions import get_global_logger
import bin.funcs.can_functions as cf
from bin.classes.can_classes import Live_CAN_System, CAN_log

class InputScreen(QWidget):
    def __init__(self, main, config):
        super().__init__()
        self.main = main
        self.config = config
        self.fields = []   # stores (type, widget)

        layout = QVBoxLayout()

        # Title
        title = QLabel(config.get("title", ""))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title)

        # Build fields
        for field in config["fields"]:
            ftype = field["type"]
            flabel = field["label"]

            row = QHBoxLayout()
            label = QLabel(flabel + ":")
            row.addWidget(label)

            if ftype == "text":
                widget = QLineEdit()
                row.addWidget(widget)

            elif ftype == "dropdown":
                widget = QComboBox()
                widget.addItems(field["options"])
                row.addWidget(widget)

            elif ftype == "file":
                file_label = QLabel("No file selected")
                file_label.setStyleSheet("color: #aaaaaa;")

                browse_btn = QPushButton("Browse...")
                browse_btn.clicked.connect(lambda _, lbl=file_label: self.pick_file(lbl))

                row.addWidget(browse_btn)
                row.addWidget(file_label)

                widget = file_label


            self.fields.append((ftype, widget))
            layout.addLayout(row)

        # Buttons
        btn_run = QPushButton("Run")
        btn_back = QPushButton("Back")

        btn_run.clicked.connect(self.run_action)
        btn_back.clicked.connect(self.go_back)

        bottom = QHBoxLayout()
        bottom.addWidget(btn_back)
        bottom.addWidget(btn_run)

        layout.addStretch(1)
        layout.addLayout(bottom)

        self.setLayout(layout)

    def pick_file(self, label_widget):
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")
        if path:
            label_widget.setText(path)

    def go_back(self):
        action = self.config["back_action"]
        self.main.log.info(action)
        getattr(self.main, action)()

    def run_action(self):
        values = []
        for ftype, widget in self.fields:
            if ftype == "text":
                values.append(widget.text())
            elif ftype == "dropdown":
                values.append(widget.currentText())
            elif ftype == "file":
                values.append(widget.text())  # absolute path

        action = self.config["run_action"]
        self.main.log.info(action)
        getattr(self.main, action)(values)

class NavigationScreen(QWidget):
    def __init__(self, main, config):
        super().__init__()
        self.main = main
        layout = QVBoxLayout()

        if "message" in config:
            msg = QLabel(config["message"])
            msg.setAlignment(Qt.AlignCenter)
            msg.setStyleSheet("font-size: 20px;")
            layout.addWidget(msg)

        h = QHBoxLayout()
        h.addStretch(1)

        for btn in config["buttons"]:
            b = QPushButton(btn["label"])
            b.clicked.connect(lambda _, a=btn["action"]: self.handle_action(a))
            h.addWidget(b)

        h.addStretch(1)

        layout.addStretch(1)
        layout.addLayout(h)
        layout.addStretch(1)

        bottom_cfg = config["bottom_button"]
        bottom = QPushButton(bottom_cfg["label"])
        bottom.clicked.connect(lambda _, a=bottom_cfg["action"]: self.handle_action(a))
        layout.addWidget(bottom, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def handle_action(self, action):
        if action == "exit":
            sys.exit()
        if hasattr(self.main, action):
            self.main.log.info(action)
            getattr(self.main, action)()

class LiveCANScreen(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        self.can_system = None
        self.paused = False
        self.replay_mode = False
        self.replay_log = None
        self.replay_start = 0
        self.replay_prev = 0

        main_layout = QVBoxLayout()

        title = QLabel("Live CAN Monitor")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold;")
        main_layout.addWidget(title)

        self.filter_layout = QHBoxLayout()
        self.filter_edits = []
        column_names = ["Timestamp", "ID"] + [f"Byte{i}" for i in range(8)]

        for name in column_names:
            edit = QLineEdit()
            edit.setPlaceholderText(name)
            edit.textChanged.connect(self.apply_filters)
            self.filter_layout.addWidget(edit)
            self.filter_edits.append(edit)

        main_layout.addLayout(self.filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(len(column_names))
        self.table.setHorizontalHeaderLabels(column_names)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.table)

        controls = QHBoxLayout()

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.clicked.connect(self.toggle_pause)
        controls.addWidget(self.btn_pause)

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.clear_output)
        controls.addWidget(btn_clear)

        btn_save = QPushButton("Save CSV")
        btn_save.clicked.connect(self.save_csv)
        controls.addWidget(btn_save)

        btn_back = QPushButton("Back")
        btn_back.clicked.connect(self.go_back)
        controls.addWidget(btn_back)

        main_layout.addLayout(controls)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_can_data)

        self.setLayout(main_layout)

    # -------------------------
    # Live CAN Mode
    # -------------------------
    def start_monitor(self, can_id, baud, timeout):
        self.main.log.info("start_monitor")
        self.replay_mode = False
        self.can_system = Live_CAN_System()
        self.can_id = can_id
        self.table.setRowCount(0)
        self.paused = False
        self.btn_pause.setText("Pause")
        self.timer.start(100)

    # -------------------------
    # Replay Log Mode
    # -------------------------
    def start_replay(self, can_log):
        self.main.log.info("start_replay")
        self.replay_mode = True
        self.replay_log = can_log
        self.replay_start = datetime.now().timestamp()
        self.replay_prev = self.replay_start
        self.table.setRowCount(0)
        self.paused = False
        self.btn_pause.setText("Pause")
        self.timer.start(100)

    # -------------------------
    # Update Loop
    # -------------------------
    def update_can_data(self):
        if self.paused:
            return

        if self.replay_mode:
            self.update_replay_data()
        else:
            self.update_live_data()

    def update_live_data(self):
        msgs = self.can_system.read_can_msgs()
        if not msgs:
            return

        for msg in msgs:
            self.add_row(
                datetime.fromtimestamp(msg.timestamp).strftime("%H:%M:%S.%f")[:-3],
                msg.arbitration_id,
                list(msg.data)
            )

        self.apply_filters()

    def update_replay_data(self):
        now = datetime.now().timestamp()
        msgs = self.replay_log.get_msgs(self.replay_start, self.replay_prev)
        self.replay_prev = now

        for frame in msgs:
            self.add_row(
                datetime.fromtimestamp(frame.ts).strftime("%H:%M:%S.%f")[:-3],
                frame.frameid,
                frame.data if isinstance(frame.data, list) else []
            )

        self.apply_filters()

    # -------------------------
    # Helpers
    # -------------------------
    def add_row(self, timestamp, frameid, data_bytes):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(timestamp))
        self.table.setItem(row, 1, QTableWidgetItem(f"0x{frameid:03X}"))

        for i in range(8):
            val = f"{data_bytes[i]:02X}" if i < len(data_bytes) else ""
            self.table.setItem(row, 2 + i, QTableWidgetItem(val))

    def toggle_pause(self):
        if self.paused:
            self.main.log.info("resume")
            self.btn_pause.setText("Pause")
            self.paused = False
        else:
            self.main.log.info("pause")
            self.btn_pause.setText("Resume")
            self.paused = True

    def clear_output(self):
        self.main.log.info("clear_output")
        self.table.setRowCount(0)

    def go_back(self):
        self.main.log.info("go_rt_menu")
        self.timer.stop()
        self.main.go_rt_menu()

    def apply_filters(self):
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        filters = [edit.text().strip().lower() for edit in self.filter_edits]

        for row in range(rows):
            show = True
            for col in range(cols):
                flt = filters[col]
                if not flt:
                    continue
                item = self.table.item(row, col)
                cell = (item.text() if item else "").lower()
                if flt not in cell:
                    show = False
                    break
            self.table.setRowHidden(row, not show)

    def save_csv(self):
        self.main.log.info("save_csv")

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_dir = os.path.join(base_dir, "output_files", "csv_logs")
        os.makedirs(csv_dir, exist_ok=True)

        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(csv_dir, f"live_can_{timestamp_str}.csv")

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "id", "data"])

            rows = self.table.rowCount()
            for row in range(rows):
                ts = self.table.item(row, 0).text()
                cid = self.table.item(row, 1).text()

                data_vals = []
                for col in range(2, 10):
                    item = self.table.item(row, col)
                    if item and item.text():
                        data_vals.append(item.text())

                writer.writerow([ts, cid, " ".join(data_vals)])

class PPResultsScreen(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        layout = QVBoxLayout()

        title = QLabel("PP Results")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(title)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Device Type", "Manufacturer", "ID", "APIs"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Back button
        btn_back = QPushButton("Back")
        btn_back.clicked.connect(self.go_back)
        layout.addWidget(btn_back)

        self.setLayout(layout)

    def load_table(self, table_data):
        self.table.setRowCount(0)

        for row_data in table_data:
            row = self.table.rowCount()
            self.table.insertRow(row)

            for col, value in enumerate(row_data):
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                self.table.setItem(row, col, QTableWidgetItem(str(value)))

    def go_back(self):
        self.main.go_pp()

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
        self.auto_detect = NavigationScreen(self, cfg["auto_detect"])
        self.live_can_screen = LiveCANScreen(self)
        self.pp_results = PPResultsScreen(self)
        self.stack.addWidget(self.pp_results)

        for screen in [
            self.home,
            self.rt_setup,
            self.rt_menu,
            self.pp_input,
            self.live_can_input,
            self.replay_log_input,
            self.auto_detect,
            self.live_can_screen
        ]:
            self.stack.addWidget(screen)

        self.go_home()

    def go_home(self):
        self.log.info("go_home")
        self.stack.setCurrentWidget(self.home)

    def go_pp(self):
        self.log.info("go_pp")
        self.stack.setCurrentWidget(self.pp_input)

    def go_rt(self):
        self.log.info("go_rt_setup")
        self.stack.setCurrentWidget(self.rt_setup)

    def go_rt_menu(self):
        self.log.info("go_rt_menu")
        self.stack.setCurrentWidget(self.rt_menu)

    def go_live_can_input(self):
        self.log.info("go_live_can_input")
        self.stack.setCurrentWidget(self.live_can_input)

    def go_replay_log_input(self):
        self.log.info("go_replay_log_input")
        self.stack.setCurrentWidget(self.replay_log_input)

    def go_auto_detect(self):
        self.log.info("go_auto_detect")
        self.stack.setCurrentWidget(self.auto_detect)

    def run_pp(self, data):
        self.log.info("run_pp")
        file_path, logging_source = data
        can_log = cf.get_can_from_xlsx(file_path, logging_source)
        table = can_log.get_cntr_table()
        self.pp_results.load_table(table)
        self.stack.setCurrentWidget(self.pp_results)

    def run_live_can(self, data):
        self.log.info("run_live_can")
        can_id, baud, timeout = data
        self.live_can_screen.start_monitor(can_id, baud, timeout)
        self.stack.setCurrentWidget(self.live_can_screen)

    def run_replay_log(self, data):
        self.log.info("run_replay_log")
        file_path, logging_source = data
        can_log = cf.get_can_from_xlsx(file_path, logging_source)
        self.live_can_screen.start_replay(can_log)
        self.stack.setCurrentWidget(self.live_can_screen)

    def start_auto_detect(self):
        self.log.info("start_auto_detect")
        print("Auto detect started")