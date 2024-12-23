import sys
from pathlib import Path

from PySide6.QtCore import QTranslator, QCoreApplication, QTimer, QStringListModel, Qt
from PySide6.QtGui import QIcon, QImage
from PySide6.QtWidgets import QWidget, QApplication, QSystemTrayIcon, QMessageBox, QPushButton, \
    QLabel, QMenu, QAbstractItemView
from werkzeug.serving import select_address_family

from src.config import requires_init
from src.gui.ui_mainwindow import Ui_MainWindow
from src.gui.ui_home_page import Ui_HomePage
from src.gui.ui_plugin_page import Ui_PluginPage
from src.plugin import PluginLoader


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
        self.ui_home_page = Ui_HomePage()
        self.ui_plugin_page = Ui_PluginPage()
        self.ui.setupUi(self)
        self.ui_home_page.setupUi(self.ui.pageContainer.widget(0))
        self.ui_plugin_page.setupUi(self.ui.pageContainer.widget(1))
        # ---
        self.alive = True
        self.raw_title = self.windowTitle()
        self.icon = QIcon("assets/icon.png")

        self.plugin_timer = QTimer()
        self.plugin_loader = PluginLoader()
        self.plugin_list_model = QStringListModel()

        self.status_timer = QTimer()

        self.tray_icon = QSystemTrayIcon()
        # ---
        self.ui_plugin_page.pluginNameList.setModel(self.plugin_list_model)

        self.actions_setup()

        self.init_plugin_loader()
        self.init_tray_icon()
        self.init_status_timer()
        # ---
        self.setWindowIcon(self.icon)

    def request_focus(self):
        self.show()
        self.activateWindow()
        self.setFocus()
        if self.windowHandle():
            self.windowHandle().requestActivate()

    def init_tray_icon(self):
        def on_tray_icon_activated(reason: QSystemTrayIcon.ActivationReason):
            if reason == QSystemTrayIcon.ActivationReason.Trigger:
                self.request_focus()

        self.tray_icon.setIcon(self.icon)
        self.tray_icon.activated.connect(on_tray_icon_activated)
        menu = QMenu()
        # 不明原因, 有时候右键图标会直接弹出主窗口而不是先显示菜单.
        # showMainWindow = menu.addAction("显示主窗口")
        # showMainWindow.triggered.connect(self.request_focus)
        quitApp = menu.addAction("退出")
        quitApp.triggered.connect(self.close)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.setToolTip(self.windowTitle())
        self.tray_icon.show()

    def notify_login(self):
        """提示用户进行 uia 登录操作"""
        rst = QMessageBox.question(self, "UIA 登录",
                                   "即将进行 ECNU 统一认证登录操作,\n"
                                   "如果配置了 login_info.toml 则会自动登录, 请不要手动操作,\n"
                                   "如果没有配置, 请手动进行登录操作.\n"
                                   "是否继续?",
                                   QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if rst == QMessageBox.StandardButton.Yes:
            self.hide()
            self.plugin_loader.ecnu_uia_login()
            self.show()
            if self.plugin_loader.cache_valid:
                QMessageBox.information(self, "登录成功", "登录成功.")
            else:
                QMessageBox.warning(self, "登录失败", "需要重新登录.")

    def actions_setup(self):
        self.ui.homePageBtn.clicked.connect(lambda: self.ui.pageContainer.setCurrentIndex(0))
        self.ui.pluginPageBtn.clicked.connect(lambda: self.ui.pageContainer.setCurrentIndex(1))

        self.ui_home_page.quitBtn.clicked.connect(self.close)
        self.ui_home_page.uiaLoginBtn.clicked.connect(self.notify_login)

    def init_plugin_loader(self):
        self.plugin_loader.import_plugins()
        self.plugin_loader.load_config()
        self.plugin_loader.load_all()  # todo 保存是否加载插件.
        # 配置插件加载器的定时轮询.
        self.plugin_timer.setInterval(100)
        self.plugin_timer.timeout.connect(self.plugin_loader.poll)
        self.plugin_timer.start()
        # 插件添加到列表组件.
        self.plugin_list_model.setStringList(
            self.plugin_loader.get_imported_plugins()
        )  # 应该不会自动随列表的值变化而自动响应.

    def init_status_timer(self):
        def update():
            self.setWindowTitle(
                self.raw_title
                + ("" if self.plugin_loader.cache_valid else " (未登录)")
            )
            self.tray_icon.setToolTip(self.windowTitle())

        self.status_timer.setInterval(1000)
        self.status_timer.timeout.connect(update)
        self.status_timer.start()

    def close(self):
        """退出应用"""
        self.alive = False
        self.plugin_timer.stop()
        self.status_timer.stop()
        self.plugin_loader.close()
        self.show()  # show 了之后才能正常关闭.
        super().close()

    def closeEvent(self, event):
        if not self.alive:
            event.accept()  # 允许关闭窗口
        else:
            event.ignore()
            self.hide()  # 隐藏到后台, 通过任务栏窗口重新唤出.


@requires_init
def main():
    app = QApplication(sys.argv)
    try:
        window = MainWindow()
        window.show()
    except UIException:
        pass
    sys.exit(app.exec())
