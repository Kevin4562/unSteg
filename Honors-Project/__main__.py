import sys
from PyQt5.QtWidgets import *
from gui import UnveilGUI


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    sys.excepthook = except_hook
    app = QApplication([])
    unveil = UnveilGUI()
    sys.exit(app.exec_())