import ctypes
import time
from ctypes import wintypes

import psutil
import subprocess
import win32gui
import uiautomation as automation
from pywinauto import Application

from src.config import logger, requires_init


class Window:
    def __init__(self, title):
        self.title = title
        self.hwnd = None

    @staticmethod
    def GetWeChatPID(name: str) -> int:
        """
        获取微信在系统中的进程 PID
        :param name:
        :return pid:
        """
        pids = psutil.process_iter()  # 获得全部进程的 PID
        for pid in pids:
            if (pid.name() == name):
                return pid.pid

        # 若最后仍未找到，则返回零
        logger.info("Find no process named Wechat.exe.")
        return 0

    @staticmethod
    def get_screen_scale() -> tuple:
        """
        获取屏幕分辨率
        """
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        return screen_width, screen_height

    def find_window(self):
        """
        根据窗口标题查找窗口
        """
        hwnd = ctypes.windll.user32.FindWindowW(None, self.title)  # 查找窗口句柄
        if hwnd:
            self.hwnd = hwnd
            return True
        return False


class Wechat(Window):
    def __init__(self):
        super().__init__(u"微信")  # 微信窗口的标题为“微信”

    @requires_init
    def click_taskbar_icon(self):
        """
        点击任务栏上的微信图标, 以这种方式来打开微信
        """
        taskbar = automation.ControlFromHandle(ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None))
        wechat_icon = taskbar.ButtonControl(Name="微信")
        try:
            if wechat_icon.Exists(0, 0):
                logger.info("Clicking on WeChat taskbar icon...")
                wechat_icon.Click(simulateMove=False)
            else:
                logger.info("WeChat taskbar icon not found!")
        except Exception as e:
            logger.info(f"Failed to click taskbar icon: {e}")

    def close_window(self, uia=None):
        """
        关闭当前已打开的聊天窗口, 确保打开目标聊天框之前, 没有干扰的聊天窗口.
        :param uia: UI 自动化库实例
        """
        while win32gui.FindWindow('ChatWnd', None):
            if not uia:
                raise ValueError("UI Automation instance (uia) is required.")
            uia.WindowControl(ClassName='ChatWnd').SwitchToThisWindow()
            uia.WindowControl(ClassName='ChatWnd').ButtonControl(Name='关闭').Click(simulateMove=False)

    @requires_init
    def show_main_window(self, PID: int, retry_count=3):
        """
        显示微信主窗口并最大化, 保证每一台电脑运行时均能够成功点击.

        :param PID: 微信进程的 PID

        .. note:
            这种方式是最好的, 因为即使你已经打开了微信, 或拖动了微信，都能够保证最后处于打开状态.
            先采取直接连接 PID 的形式, 如果失败, 再采取点击任务栏图标的方式.
            重新获得了 PID 之后, 再次尝试连接 PID.
        """
        try:
            app = Application(backend="uia").connect(process=PID)
            # 使用 UI Automation 技术，而不是使用传统的 Win32 API
            wechat_window = app[u"微信"]  # 使用 Unicode 字符处理
            wechat_window.maximize()
        except Exception as e:
            logger.info(f"Failed to show main window, Error: {e}")

            # 如果没有成功打开微信, 就点击任务栏来打开
            try:
                self.click_taskbar_icon()
                PID = self.GetWeChatPID('WeChat.exe')
                self.show_main_window(PID, retry_count - 1)
            except Exception as e:
                logger.info(f"Failed to click taskbar icon: {e}")

    @requires_init
    def close_main_window(self, PID: int):
        """
        关闭微信主窗口

        :param PID: 微信进程的 PID
        """
        try:
            app = Application(backend="uia").connect(process=PID)
            wechat_window = app[u"微信"]
            wechat_window.close()
        except Exception as e:
            logger.info(f"Failed to close main window, Error: {e}")
