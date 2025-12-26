import sys
import bin.funcs.gui_functions as gui_funcs
import bin.formats.vars as vars
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,QMainWindow, QLCDNumber, QStackedWidget, QPushButton)
from PyQt5.QtCore import Qt, QTimer

class Gui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.create_pages()
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked)
        self.setLayout(main_layout)
        self.showFullScreen()

    def start_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    def create_pages(self):
        self.stacked = QStackedWidget()
        self.stacked.addWidget(Page("buttons"))
        self.stacked.setCurrentWidget(self.stacked.findChild(QWidget, "buttons"))



    def change_page(self,page:Page):
        widget = self.stacked.findChild(QWidget, page.name)
        if widget:
            self.stacked.setCurrentWidget(widget)
        self.setWindowTitle(page.name)

class Page(QWidget):

    def __init__(self,screen_type):
        super().__init__()
        #gui_funcs.create_cus_widget(self,gui,name,"V")
        self.setObjectName = screen_type
        layout = QVBoxLayout()
        if screen_type == "buttons":
            # Three centered buttons
            btn1 = QPushButton("Button 1")
            btn2 = QPushButton("Button 2")
            btn3 = QPushButton("Button 3")

            h_layout = QHBoxLayout()
            h_layout.addStretch(1)
            h_layout.addWidget(btn1)
            h_layout.addWidget(btn2)
            h_layout.addWidget(btn3)
            h_layout.addStretch(1)

            layout.addStretch(1)
            layout.addLayout(h_layout)
            layout.addStretch(1)

        elif screen_type == "settings":
            layout.addWidget(QLabel("Settings Screen"))
            layout.addWidget(QPushButton("Save Settings"))

        elif screen_type == "status":
            layout.addWidget(QLabel("System Status"))
            layout.addWidget(QPushButton("Refresh"))

        else:
            layout.addWidget(QLabel(f"Unknown screen type: {screen_type}"))

        self.setLayout(layout)

class Line:
    def __init__(self, minor_sec, name: str):
        gui_funcs.create_cus_widget(self,minor_sec,name,"H")
        self.label = custom_label(self,name)
        self.value = custom_value(self,"text")
        self.obj.setLayout(self.layout)
        self.parent.layout.addWidget(self.obj)

    def set_value(self,value):
        self.value.set_value(value)

    def hide_line(self):
        self.label.hide()
        self.value.hide()

    def show_line(self):
        self.label.show()
        self.value.show()

class custom_label():

    def __init__(self, parent : object, name : str):
        self.obj = QLabel(name)
        self.obj.setAlignment(Qt.AlignLeft)
        parent.layout.addWidget(self.obj)

    def hide(self): self.obj.hide()
    def show(self): self.obj.show()

class custom_value():

    def __init__(self, line : Line, type : str["text"|"lcd"]):
        
        self.type = type
        if self.type == "text": self.obj = QLabel()
        elif type == "lcd": self.obj = QLCDNumber()
        line.layout.addWidget(self.obj)

    def set_value(self,value):
        
        if self.type == "text": 
            if type(value) == str: self.obj.setText(str(value))
            else: self.obj.setText("N/A")
        elif self.type == "lcd": 
            if type(value) == float: self.obj.display(value)
            else: self.obj.display(32.767)

    def hide(self): self.obj.hide()
    def show(self): self.obj.show()

class Controller_Display():

    def __init__(self, cntr):
        self.cntr = cntr

class CAN_Frame_Line():

    def __init__(self,frame):
        self.frame = frame