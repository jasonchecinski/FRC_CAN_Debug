import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout
import bin.classes.gui_classes as gc

def run():
    app = QApplication(sys.argv)
    window = gc.Gui()
    window.show()
    sys.exit(app.exec_())

def create_cus_widget(input_class, parent_class, name : str, type : str["H"|"V"]):
    input_class.parent = parent_class
    input_class.name = name
    input_class.sub_secs = []
    input_class.obj = QWidget()
    if type == "H": input_class.layout = QHBoxLayout()
    elif type == "V": input_class.layout = QVBoxLayout()
    input_class.layout.setContentsMargins(10, 10, 10, 10)