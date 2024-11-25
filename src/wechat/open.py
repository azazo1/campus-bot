import ctypes
import io
import os
import re
import time

import psutil
import pyautogui
import uiautomation as automation
import win32clipboard
from PIL import Image
from pywinauto import Application
from pywinauto.keyboard import send_keys

from src.config import logger, requires_init


class Window:
    def __init__(self, title):
        self.title = title
        self.hwnd = None

    @staticmethod
    def _get_we_chat_pid(name: str) -> int:
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
        self._connect()

    def _connect(self):
        self.PID = self._get_we_chat_pid('WeChat.exe')
        self.app = Application(backend="uia").connect(process=self.PID)
        # 使用 UI Automation 技术，而不是使用传统的 Win32 API
        self.wechat_window = self.app[u"微信"]  # 使用 Unicode 字符处理

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
                logger.error("WeChat taskbar icon not found!")
        except Exception as e:
            logger.error(f"Failed to click taskbar icon: {e}")

    @requires_init
    def show_main_window(self, retry_count=3):
        """
        显示微信主窗口并最大化, 保证每一台电脑运行时均能够成功点击.

        .. note:
            这种方式是最好的, 因为即使你已经打开了微信, 或拖动了微信，都能够保证最后处于打开状态.
            先采取直接连接 PID 的形式, 如果失败, 再采取点击任务栏图标的方式.
            重新获得了 PID 之后, 再次尝试连接 PID.
        """
        try:
            self._connect()
            self.wechat_window.maximize()
        except Exception as e:
            logger.error(f"Failed to show main window, Error: {e}")

            # 如果没有成功打开微信, 就点击任务栏来打开
            try:
                self.click_taskbar_icon()
                # 因为之前没有打开 WeChat.exe 获得 PID, 所以这里再获取一次
                # 这里递归调用, 但不会无限循环, 因为 retry_count 会递减
                self.PID = self._get_we_chat_pid('WeChat.exe')
                self.show_main_window(retry_count - 1)
            except Exception as e:
                logger.error(f"Failed to click taskbar icon: {e}")

    @requires_init
    def close_main_window(self):
        """
        关闭微信主窗口
        """
        try:
            self._connect()
            self.wechat_window.close()
        except Exception as e:
            logger.error(f"Failed to close main window, Error: {e}")

    @requires_init
    def locate_search_box(self) -> tuple or None:
        """
        定位微信左上角的搜索框, 并返回其坐标, 以便后续操作

        Tips:
        此操作只在程序第一次运行时执行, 加入了一个 temp.ini 文件, 以便下次运行时直接读取坐标, 而不用再次定位, 节省时间
        这是因为每个人电脑的分辨率不一致, 所以需要定位搜索框的位置

        :return: 搜索框的坐标
        """
        if os.path.exists("temp.ini"):
            return None
        else:
            try:
                self._connect()
                search_box = self.wechat_window.child_window(title=u"搜索", control_type="Edit")
                search_box.draw_outline()  # 描边
                box_location = search_box.rectangle()  # 返回位置信息
                logger.info(box_location)

                with open("temp.ini", "w") as f:
                    f.write(str(box_location))

                return box_location

            except Exception as e:
                logger.error(f"Failed to locate search box, Error: {e}")
                return None

    @requires_init
    def show_identifiers(self):
        """
        输出微信窗口的全部控件的属性
        """
        self._connect()
        self.wechat_window.print_control_identifiers()

    @staticmethod
    def _parse_coordinates(coors_str: str) -> tuple:
        """
        使用正则表达式提取 temp.ini 中的数字, 并转换为坐标元组
        :param coors_str:
        :return: 坐标元组
        """
        numbers = re.findall(r'\d+', coors_str)
        if len(numbers) == 4:
            return tuple(map(int, numbers))
        raise ValueError("Invalid coordinate format")

    @requires_init
    def click_search_box(self):
        """
        点击搜索框, 输入名称, 并按 Enter 键
        """
        if not os.path.exists("temp.ini"):
            self.locate_search_box()
        else:
            with open("temp.ini", "r") as f:
                coors_str = f.read().strip()

            coors = Wechat._parse_coordinates(coors_str)
            search_box_center_x = (coors[0] + coors[2]) // 2  # (L + R) / 2
            search_box_center_y = (coors[1] + coors[3]) // 2  # (T + B) / 2
            pyautogui.moveTo(search_box_center_x, search_box_center_y)
            pyautogui.click()
            logger.info("Clicked on search box.")

    @requires_init
    def content_enter(self, content: str):
        """
        输入内容, 并按回车键
        :param content: 输入的内容
        """
        automation.SendKeys(content)
        time.sleep(0.05)  # Add a delay to ensure the content is inputted correctly
        automation.SendKeys("{ENTER}")
        logger.info(f"Input content: {content}, then press enter key.")

    @requires_init
    def _copy_image_to_clipboard(self, file_path):
        """
        将图片复制到剪贴板
        :param file_path: 图片文件路径
        """
        try:
            image = Image.open(file_path)
            output = io.BytesIO()
            image.convert("RGB").save(output, "BMP")
            bmp_data = output.getvalue()[14:]  # BMP 数据需要跳过 14 字节的文件头
            output.close()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
            win32clipboard.CloseClipboard()

            logger.info("Successfully copy the file into clipboard.")
        except Exception as e:
            logger.error(f"Failed to copy the file into clipboard: {e}")

    @requires_init
    def _copy_file_to_clipboard(self, file_path):
        """
        将文件复制到剪贴板
        :param file_path: 文件路径
        """
        try:
            buffer = ctypes.create_unicode_buffer(file_path)

            # 将文件路径数据设置到剪贴板
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_HDROP, buffer)
            win32clipboard.CloseClipboard()

            logger.info("Successfully copy the file into clipboard.")
        except Exception as e:
            logger.error(f"Failed to copy the file into clipboard: {e}")

    @requires_init
    def send_message(self, name: str, content: str):
        """
        这里是全部封装好的接口, 直接对某一个人发送消息
        :param name: 发送对象的名称
        :param content: 发送的内容
        """
        self.show_main_window()
        self.click_search_box()
        self.content_enter(name)
        self.content_enter(content)
        logger.info(f"Send message to {name}: {content}")

    @requires_init
    def send_image(self, name: str, path: str):
        """
        封装好的接口, 直接向某个人发送图片或文件
        :param name: 发送对象的名称
        :param path: 图片路径
        """
        self.show_main_window()
        self.click_search_box()
        self.content_enter(name)
        self._copy_image_to_clipboard(path)
        send_keys("^v")
        send_keys("{ENTER}")
