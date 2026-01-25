# bin/funcs/gui_functions.py
import sys
from PyQt5.QtWidgets import QApplication

from bin.classes.gui_classes import MainWindow
from bin.funcs.global_functions import get_global_logger


def run():
    """
    Initializes QApplication, sets up global logging, and launches the GUI.
    """
    app = QApplication(sys.argv)

    logger = get_global_logger()

    window = MainWindow()
    window.log = logger

    logger.info("GUI started")
    window.show()

    sys.exit(app.exec_())