import sys
from pathlib import Path

from PySide6.QtCore import QTranslator, QCoreApplication, QTimer, QStringListModel, Qt, QModelIndex
from PySide6.QtGui import QIcon, QImage
from PySide6.QtWidgets import QWidget, QApplication, QSystemTrayIcon, QMessageBox, QPushButton, \
    QLabel, QMenu, QAbstractItemView, QSpacerItem, QSizePolicy, QLayout, QHBoxLayout, QCheckBox

from src.config import requires_init
from src.gui.ui_mainwindow import Ui_MainWindow
from src.gui.ui_home_page import Ui_HomePage
from src.gui.ui_plugin_page import Ui_PluginPage
from src.gui.ui_config_item_row import Ui_configItemRow
from src.plugin import PluginLoader, ConfigItem, NumberItem


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
        self.plugin_config_modified = False  # 编辑插件配置的时候, 如果修改了配置项但是没有保存.
        # todo 修改配置内容时标记 modified 为 True.

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

    @property
    def plugin_config_modified(self):
        return self._plugin_config_modified

    @plugin_config_modified.setter
    def plugin_config_modified(self, value):
        if value:
            self.ui_plugin_page.saveConfigBtn.show()
        else:
            self.ui_plugin_page.saveConfigBtn.hide()
        self._plugin_config_modified = value

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

    def notify_plugin_config_save(self):
        self.plugin_loader.save_config()
        self.plugin_config_modified = False
        QMessageBox.information(self, "插件配置保存", "插件配置已生效并保存")

    def actions_setup(self):
        self.ui.homePageBtn.clicked.connect(lambda: self.ui.pageContainer.setCurrentIndex(0))
        self.ui.pluginPageBtn.clicked.connect(lambda: self.ui.pageContainer.setCurrentIndex(1))

        self.ui_home_page.quitBtn.clicked.connect(self.close)
        self.ui_home_page.uiaLoginBtn.clicked.connect(self.notify_login)

        self.ui_plugin_page.saveConfigBtn.clicked.connect(self.notify_plugin_config_save)

        self.ui_plugin_page.pluginNameList.clicked.connect(self.on_plugin_item_clicked)

    def on_plugin_item_clicked(self, idx: QModelIndex):
        plugin_name = idx.data()
        self.build_plugin_config_page(plugin_name)

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
                + (" (插件配置未保存生效)" if self.plugin_config_modified else "")
            )
            self.tray_icon.setToolTip(self.windowTitle())

        self.status_timer.setInterval(1000)
        self.status_timer.timeout.connect(update)
        self.status_timer.start()

    def close(self):
        """退出应用"""
        if self.plugin_config_modified:
            rst = QMessageBox.warning(self, "插件配置将丢失",
                                      "插件配置已被修改, 但是没有生效也没有保存, 退出将导致修改内容丢失.\n是否退出?",
                                      QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            if rst != QMessageBox.StandardButton.Yes:
                return
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

    def build_plugin_config_page(self, plugin_name: str):
        # 插件配置在用户点击控件时就同步 plugin_loader 中的配置修改, 及时切换插件配置界面也会暂存在内存中.
        # 但是这些配置没有生效, 需要点击保存按钮才能生效.
        config = self.plugin_loader.get_plugin_config(plugin_name)
        v_layout = self.ui_plugin_page.pluginConfigContent
        while v_layout.count():
            item = v_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        def get_switch_text(load_it=None):
            if load_it is None:
                load_it = not self.plugin_loader.is_plugin_loaded(plugin_name)
            return "加载" if load_it else "停止"

        def switch_load():
            text = get_switch_text() + "成功"
            if self.plugin_loader.is_plugin_loaded(plugin_name):
                self.plugin_loader.unload_plugin(plugin_name)
            else:
                self.plugin_loader.load_plugin(plugin_name)
            whether_load_btn.setText(get_switch_text())
            QMessageBox.information(self, text, text)

        title = QLabel(plugin_name)
        title.setStyleSheet("""font: bold 30px;""")
        whether_load_btn = QPushButton(get_switch_text())
        whether_load_btn.clicked.connect(switch_load)

        v_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        v_layout.addWidget(whether_load_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        for cfg_item in config:
            self.add_config_item(v_layout, cfg_item)
        v_layout.addSpacerItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        ))
        # todo 添加加载和取消加载按钮.

    @staticmethod
    def add_config_item(layout: QLayout, cfg_item: ConfigItem):
        widget = QWidget()
        ui = Ui_configItemRow()
        ui.setupUi(widget)
        ui.itemName.setText(cfg_item.name)
        ui.itemDesc.setText(cfg_item.description or "[无说明]")
        if isinstance(cfg_item, NumberItem):
            ui.inlineContent.addWidget(QCheckBox("lskdfj"))
        else:
            raise TypeError("Unknown config item type.")
        layout.addWidget(widget)


@requires_init
def main():
    app = QApplication(sys.argv)
    try:
        window = MainWindow()
        window.show()
    except UIException:
        pass
    sys.exit(app.exec())
