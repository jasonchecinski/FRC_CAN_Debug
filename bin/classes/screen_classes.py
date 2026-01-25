from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox, QFileDialog, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt

class InputScreen(QWidget):
    def __init__(self, main, config):
        super().__init__()
        self.main = main
        self.config = config
        self.fields = []
        self.btn_run = None
        self.btn_back = None

        root = QVBoxLayout()

        # Title
        title = QLabel(config.get("title", ""))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        root.addWidget(title)

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
                browse_btn.clicked.connect(
                    lambda _, lbl=file_label: self.pick_file(lbl)
                )

                row.addWidget(browse_btn)
                row.addWidget(file_label)
                widget = file_label

            self.fields.append((ftype, widget))
            root.addLayout(row)

        # Buttons
        btn_run = QPushButton("Run")
        btn_back = QPushButton("Back")
        self.btn_run = btn_run
        self.btn_back = btn_back

        bottom = QHBoxLayout()
        bottom.addWidget(btn_back)
        bottom.addWidget(btn_run)

        root.addStretch(1)
        root.addLayout(bottom)

        self.setLayout(root)

    def pick_file(self, label_widget):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "All Files (*)"
        )
        if path:
            label_widget.setText(path)

class NavigationScreen(QWidget):
    def __init__(self, main, config):
        super().__init__()
        self.main = main
        self.buttons = []
        self.bottom_button = None

        root = QVBoxLayout()

        if "message" in config:
            msg = QLabel(config["message"])
            msg.setAlignment(Qt.AlignCenter)
            msg.setStyleSheet("font-size: 20px;")
            root.addWidget(msg)

        h = QHBoxLayout()
        h.addStretch(1)

        for btn in config["buttons"]:
            b = QPushButton(btn["label"])
            b.action = btn["action"]
            self.buttons.append(b)
            h.addWidget(b)

        h.addStretch(1)

        root.addStretch(1)
        root.addLayout(h)
        root.addStretch(1)

        bottom_cfg = config["bottom_button"]
        bottom = QPushButton(bottom_cfg["label"])
        bottom.action = bottom_cfg["action"]
        self.bottom_button = bottom

        root.addWidget(bottom, alignment=Qt.AlignCenter)

        self.setLayout(root)

class PPResultsScreen(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.btn_back = None

        root = QVBoxLayout()

        title = QLabel("PP Results")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold;")
        root.addWidget(title)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Device Type", "Manufacturer", "ID", "APIs"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        root.addWidget(self.table)

        # Back button
        btn_back = QPushButton("Back")
        self.btn_back = btn_back
        root.addWidget(btn_back)

        self.setLayout(root)

class LiveCANScreen(QWidget):
    def __init__(self, main=None):
        super().__init__()
        self.main = main

        root = QVBoxLayout()

        title = QLabel("Live CAN Monitor")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        root.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Timestamp", "ID", "Data"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        root.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.pause_btn = QPushButton("Pause")
        self.clear_btn = QPushButton("Clear")
        self.back_btn = QPushButton("Back")

        btn_row.addWidget(self.pause_btn)
        btn_row.addWidget(self.clear_btn)
        btn_row.addWidget(self.back_btn)

        root.addLayout(btn_row)
        self.setLayout(root)

class LiveDetectScreen(QWidget):
    def __init__(self, main=None):
        super().__init__()
        self.main = main

        root = QVBoxLayout()

        title = QLabel("Live Device Auto‑Detection")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        root.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Model", "Manufacturer", "ID",
            "APIs Seen", "Status", "Last Seen", "Latency"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        root.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.reset_btn = QPushButton("Reset")
        self.back_btn = QPushButton("Back")

        btn_row.addWidget(self.reset_btn)
        btn_row.addWidget(self.back_btn)

        root.addLayout(btn_row)
        self.setLayout(root)