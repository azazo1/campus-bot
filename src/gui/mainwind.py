import datetime
import sys
import traceback
from typing import Callable

from PySide6.QtCore import QTimer, QStringListModel, Qt, QModelIndex, \
    QDate, QTime, QDateTime, QThreadPool
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QApplication, QSystemTrayIcon, QMessageBox, QPushButton, \
    QLabel, QMenu, QSpacerItem, QSizePolicy, QLayout, \
    QSpinBox, QLineEdit, QCalendarWidget, QDateEdit, QTimeEdit, QDateTimeEdit, QHBoxLayout

from src import Throttler
from src.log import requires_init, project_logger
from src.gui.ui_mainwindow import Ui_MainWindow
from src.gui.ui_home_page import Ui_HomePage
from src.gui.ui_plugin_page import Ui_PluginPage
from src.gui.ui_config_item_row import Ui_configItemRow
from src.plugin import PluginLoader, ConfigItem, NumberItem, TextItem, DateItem, TimeItem, \
    DatetimeItem, Task
from src.plugin.config import PasswordItem


def to_qdate(date: datetime.date) -> QDate:
    return QDate(date.year, date.month, date.day)


def from_qdate(qdate: QDate) -> datetime.date:
    return datetime.date(qdate.year(), qdate.month(), qdate.day())


def to_qtime(dtime: datetime.time) -> QTime:
    return QTime(dtime.hour, dtime.minute, dtime.second, dtime.microsecond)


def from_qtime(qtime: QTime) -> datetime.time:
    return datetime.time(qtime.hour(), qtime.minute(), qtime.second(), qtime.msec())


def to_qdatetime(ddatetime: datetime.datetime) -> QDateTime:
    return QDateTime(to_qdate(ddatetime.date()), to_qtime(ddatetime.time()))


def from_qdatetime(qdatetime: QDateTime) -> datetime.datetime:
    qdate = qdatetime.date()
    qtime = qdatetime.time()
    return datetime.datetime(qdate.year(), qdate.month(), qdate.day(),
                             qtime.hour(), qtime.minute(), qtime.second(), qtime.msec())


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

        self.raw_title = self.windowTitle()
        self.icon = QIcon("assets/icon.png")  # ecnu icon

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

        # ---
        self.performing_login = False
        self.notifying_login = False
        self.notifying_timeout_msgbox: QMessageBox | None = None
        self.notifying_login_msgbox: QMessageBox | None = None
        self.notify_login_throttler = Throttler(
            datetime.timedelta(minutes=10)
        )  # 如果未登录, 每个一段时间提醒一次自动登录.
        self.notify_login_timeout = datetime.timedelta(seconds=10)  # notify_timeout_login 的超时时间

        self.current_config_page = ""  # 当前配置界面的插件名称

    @property
    def plugin_config_modified(self):
        return self._plugin_config_modified

    @plugin_config_modified.setter
    def plugin_config_modified(self, value):
        if value:
            self.ui_plugin_page.saveConfigBtn.show()
            self.ui_plugin_page.disposeModifiedConfigBtn.show()
        else:
            self.ui_plugin_page.saveConfigBtn.hide()
            self.ui_plugin_page.disposeModifiedConfigBtn.hide()
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

    def perform_login(self, post_info=True):
        """
        进行 uia 登录(调出浏览器窗口).

        非阻塞, 在子线程中执行登录操作 (为了不阻止 poll 的进行).
        """
        if self.performing_login:
            return
        self.performing_login = True
        self.hide()

        def parallel():
            try:
                self.plugin_loader.ecnu_uia_login()
            except Exception:
                project_logger.error(traceback.format_exc())

        def end():
            self.show()
            if post_info:
                if self.plugin_loader.cache_valid:
                    QMessageBox.information(self, "登录成功", "登录成功.")
                else:
                    QMessageBox.warning(self, "登录失败", "需要重新登录.")
            self.performing_login = False

        task = Task(parallel)
        task.signals.finished.connect(end)
        QThreadPool.globalInstance().start(task)

    def notify_timeout_login(self):
        """
        提醒一段时间, 如果用户没有进行取消操作, 那么自动登录.

        此方法不阻塞.
        """
        if self.notifying_login:
            return
        self.notifying_login = True
        self.show()
        start_time = datetime.datetime.now()

        def on_timeout():
            delta_time = datetime.datetime.now() - start_time
            self.notifying_timeout_msgbox.setWindowTitle("即将自动登录")
            self.notifying_timeout_msgbox.setText(
                f"{(start_time + self.notify_login_timeout - datetime.datetime.now()).total_seconds():.0f} 秒后登录 UIA,\n"
                f"点击 Apply 按钮立即登录,\n"
                f"点击 Cancel 按钮或关闭窗口取消自动登录.")
            if delta_time > self.notify_login_timeout:
                timer.stop()
                self.notifying_timeout_msgbox.destroy()
                self.perform_login(False)
                self.notifying_login = False

        def btn_clicked(apply: bool):
            timer.stop()
            self.notifying_timeout_msgbox.destroy()
            if apply:
                self.perform_login(True)  # 用户主动点的则有登录结果提示
            self.notifying_login = False

        def box_closing(evt):
            evt.ignore()
            timer.stop()
            self.notifying_timeout_msgbox.destroy()
            self.notifying_login = False

        timer = QTimer()
        timer.setInterval(1000)
        timer.setSingleShot(False)
        timer.timeout.connect(on_timeout)
        timer.start()

        self.notifying_timeout_msgbox = QMessageBox(icon=QMessageBox.Icon.Information)
        self.notifying_timeout_msgbox.setWindowIcon(self.icon)
        self.notifying_timeout_msgbox.addButton(
            QMessageBox.StandardButton.Apply
        ).clicked.connect(
            lambda *args: btn_clicked(True)
        )
        self.notifying_timeout_msgbox.addButton(
            QMessageBox.StandardButton.Cancel
        ).clicked.connect(
            lambda *args: btn_clicked(False)
        )
        self.notifying_timeout_msgbox.closeEvent = box_closing

        on_timeout()
        self.notifying_timeout_msgbox.show()

    @requires_init
    def notify_login(self):
        """提示用户进行 uia 登录操作, 非阻塞"""
        if self.notifying_login:
            return
        self.notifying_login = True
        self.show()

        def end(whether_login: bool):
            if whether_login:
                self.perform_login()
            self.notifying_login = False

        self.notifying_login_msgbox = QMessageBox(icon=QMessageBox.Icon.Question)
        self.notifying_login_msgbox.setWindowIcon(self.icon)
        self.notifying_login_msgbox.setWindowTitle("UIA 登录")
        self.notifying_login_msgbox.setText(
            "即将进行 ECNU 统一认证登录操作,\n"
            "如果配置了 login_info.toml 则会自动登录, 请不要手动操作,\n"
            "如果没有配置, 请手动进行登录操作.\n"
            "是否继续?"
        )
        self.notifying_login_msgbox.addButton(
            QMessageBox.StandardButton.Yes
        ).clicked.connect(
            lambda *a: end(True)
        )
        self.notifying_login_msgbox.addButton(
            QMessageBox.StandardButton.No
        ).clicked.connect(
            lambda *a: end(False)
        )
        self.notifying_login_msgbox.show()

    def notify_plugin_config_save(self):
        self.plugin_loader.save_config()
        self.plugin_config_modified = False
        QMessageBox.information(self, "插件配置保存", "插件配置已生效并保存")

    def dispose_modified_config(self):
        self.plugin_loader.load_config()  # 从文件中重新加载插件配置
        # 刷新插件配置界面
        self.build_plugin_config_page()
        self.plugin_config_modified = False

    def actions_setup(self):
        self.ui.homePageBtn.clicked.connect(lambda: self.ui.pageContainer.setCurrentIndex(0))
        self.ui.pluginPageBtn.clicked.connect(lambda: self.ui.pageContainer.setCurrentIndex(1))

        self.ui_home_page.quitBtn.clicked.connect(self.close)
        self.ui_home_page.uiaLoginBtn.clicked.connect(self.notify_login)

        self.ui_plugin_page.saveConfigBtn.clicked.connect(self.notify_plugin_config_save)
        self.ui_plugin_page.disposeModifiedConfigBtn.clicked.connect(self.dispose_modified_config)

        self.ui_plugin_page.pluginNameList.clicked.connect(self.on_plugin_item_clicked)

    def on_plugin_item_clicked(self, idx: QModelIndex):
        plugin_name = idx.data()
        self.build_plugin_config_page(plugin_name)

    def init_plugin_loader(self):
        self.plugin_loader.import_plugins()
        self.plugin_loader.load_config()
        self.plugin_loader.load_all()
        # 配置插件加载器的定时轮询.
        self.plugin_timer.setInterval(100)
        self.plugin_timer.timeout.connect(self.poll)
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

    def build_plugin_config_page(self, plugin_name: str = ""):
        """
        构建插件配置界面.

        Parameters:
            plugin_name: 要显示配置界面的的插件名称, 如果填空则刷新当前配置界面.
        """
        plugin_name = plugin_name or self.current_config_page

        # 插件配置在用户点击控件时就同步 plugin_loader 中的配置修改, 及时切换插件配置界面也会暂存在内存中.
        # 但是这些配置没有生效, 需要点击保存按钮才能生效.
        config = self.plugin_loader.get_plugin_config(plugin_name)
        actions: dict[str, Callable[[], None]] = self.plugin_loader.get_plugin_actions(plugin_name)
        plugin_description = self.plugin_loader.get_plugin_description(plugin_name)

        self.current_config_page = plugin_name

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
            QMessageBox.information(self, text, text)
            self.build_plugin_config_page()  # 刷新插件插件配置界面, 这里不是递归.

        title = QLabel(plugin_name)
        title.setStyleSheet("""font: bold 30px;""")
        desc = QLabel(plugin_description)
        if plugin_description:  # 如果描述为空, 那么不改变样式
            desc.setStyleSheet("""
                font: italic 15px;
                padding: 10px 10px;
                border: 2px solid #404040;
                border-radius: 5px;
            """)
        desc.setWordWrap(True)

        action_row = QHBoxLayout()
        action_row_widget = QWidget()
        action_row_widget.setLayout(action_row)

        whether_load_btn = QPushButton(get_switch_text())
        whether_load_btn.clicked.connect(switch_load)
        action_row.addWidget(whether_load_btn)
        for action_text, action_callback in actions.items():  # 添加动作按钮
            btn = QPushButton()
            btn.setText(action_text)
            btn.clicked.connect(action_callback)
            action_row.addWidget(btn)

        v_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        v_layout.addWidget(desc, alignment=Qt.AlignmentFlag.AlignCenter)
        v_layout.addWidget(action_row_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        for cfg_item in config:
            self.add_config_item(v_layout, cfg_item)
        v_layout.addSpacerItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        ))

    def add_config_item(self, layout: QLayout, cfg_item: ConfigItem):
        widget = QWidget()
        ui = Ui_configItemRow()
        ui.setupUi(widget)
        ui.itemName.setText(cfg_item.name)
        ui.itemDesc.setText(cfg_item.description or "[无说明]")
        if isinstance(cfg_item, NumberItem):
            def vc(new_value: int):
                if not cfg_item.assert_value(new_value):
                    spin_box.setValue(cfg_item.current_value)
                else:
                    cfg_item.set_value(new_value)
                    self.plugin_config_modified = True

            spin_box = QSpinBox()
            spin_box.setMaximum(16777215)
            spin_box.setMinimum(-16777215)
            spin_box.setValue(cfg_item.current_value)
            spin_box.valueChanged.connect(vc)
            ui.inlineContent.addWidget(spin_box)
        elif isinstance(cfg_item, TextItem):
            def ef():
                line = pwd_edit.text()
                if not cfg_item.assert_value(line):
                    pwd_edit.setText(cfg_item.current_value)
                else:
                    cfg_item.set_value(line)
                    self.plugin_config_modified = True

            pwd_edit = QLineEdit()
            pwd_edit.editingFinished.connect(ef)
            pwd_edit.setText(cfg_item.current_value)
            ui.inlineContent.addWidget(pwd_edit)
        elif isinstance(cfg_item, DateItem):
            def set_date(new_date: QDate):
                ddate = from_qdate(new_date)
                if not cfg_item.assert_value(ddate):
                    new_date = to_qdate(cfg_item.current_value)
                else:
                    cfg_item.set_value(ddate)
                    self.plugin_config_modified = True
                date_edit.setDate(new_date)
                calendar.setSelectedDate(new_date)

            calendar = QCalendarWidget()
            date_edit = QDateEdit()
            qdate = to_qdate(cfg_item.current_value)
            calendar.setSelectedDate(qdate)
            calendar.clicked.connect(set_date)
            date_edit.editingFinished.connect(lambda: set_date(date_edit.date()))
            date_edit.setDate(qdate)
            ui.inlineContent.addWidget(date_edit)
            ui.largeContent.addWidget(calendar)
        elif isinstance(cfg_item, TimeItem):
            def set_time():
                new_time = time_edit.time()
                dtime = from_qtime(new_time)
                if not cfg_item.assert_value(dtime):
                    new_time = to_qtime(cfg_item.current_value)
                    time_edit.setTime(new_time)
                else:
                    cfg_item.set_value(dtime)
                    self.plugin_config_modified = True

            time_edit = QTimeEdit()
            time_edit.setTime(to_qtime(cfg_item.current_value))
            time_edit.editingFinished.connect(set_time)
            time_edit.setTime(cfg_item.current_value)
            ui.inlineContent.addWidget(time_edit)
        elif isinstance(cfg_item, DatetimeItem):
            def set_datetime(new_datetime: QDateTime):
                ddatetime = from_qdatetime(new_datetime)
                if not cfg_item.assert_value(ddatetime):
                    new_datetime = to_qdatetime(cfg_item.current_value)
                else:
                    cfg_item.set_value(ddatetime)
                    self.plugin_config_modified = True
                datetime_edit.setDateTime(new_datetime)
                calendar.setSelectedDate(new_datetime.date())

            def set_date(new_date: QDate):
                set_datetime(QDateTime(new_date, to_qtime(cfg_item.current_value.time())))

            datetime_edit = QDateTimeEdit()
            calendar = QCalendarWidget()
            calendar.setSelectedDate(to_qdate(cfg_item.current_value.date()))
            calendar.clicked.connect(set_date)
            datetime_edit.setDateTime(to_qdatetime(cfg_item.current_value))
            datetime_edit.editingFinished.connect(lambda: set_datetime(datetime_edit.dateTime()))
            ui.inlineContent.addWidget(datetime_edit)
            ui.largeContent.addWidget(calendar)
        elif isinstance(cfg_item, PasswordItem):
            def set_password():
                line = pwd_edit.text()
                if not cfg_item.assert_value(line):
                    pwd_edit.setText(cfg_item.current_value)
                else:
                    cfg_item.set_value(line)
                    self.plugin_config_modified = True

            pwd_edit = QLineEdit()
            pwd_edit.setEchoMode(QLineEdit.EchoMode.Password)
            pwd_edit.editingFinished.connect(set_password)
            pwd_edit.setText(cfg_item.current_value)
            ui.inlineContent.addWidget(pwd_edit)
        else:
            raise TypeError("Unknown log item type.")
        layout.addWidget(widget)

    def poll(self):
        """在非主线程调用可能会产生错误"""
        if not self.plugin_loader.cache_valid:
            self.notify_login_throttler.throttle(self.notify_timeout_login)
        self.plugin_loader.poll()


@requires_init
def main():
    app = QApplication(sys.argv)
    try:
        window = MainWindow()
        window.show()
    except UIException:
        pass
    rst = app.exec()
    QThreadPool.globalInstance().waitForDone()
    sys.exit(rst)
