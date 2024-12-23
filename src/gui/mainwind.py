import sys
from pathlib import Path

from PySide6.QtCore import QTranslator, QCoreApplication
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QApplication, QSystemTrayIcon, QMessageBox, QPushButton

from src.config import requires_init
from src.gui.ui_mainwindow import Ui_MainWindow


class UIException(Exception):
    pass


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(self, "任务栏托盘不存在",
                                 "没有任务栏托盘将会导致应用无法在后台运行")
            self.close()
            raise UIException()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(QIcon("assets/icon.png"))
        self.tray_icon.show()


@requires_init
def main():
    app = QApplication(sys.argv)
    try:
        window = MainWindow()
        window.show()
    except UIException:
        pass
    sys.exit(app.exec())
