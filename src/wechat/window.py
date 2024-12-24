"""
微信窗口控制.
"""
from __future__ import annotations

import os.path
import tempfile
import typing

import uiautomation

from .pc import get_wechat_window_control, WeChatError, wechat_control, WAIT_TIME
from ..log import project_logger, requires_init


class FileIsEmptyError(Exception):
    pass


class WeChat:
    @classmethod
    def open_window(cls):
        """
        唤出微信窗口并微信控件.

        这一步通常不是必须的, 此类下所有方法进行对微信的操作都会自动按需唤出微信窗口.

        Raises:
            WeChatError: 见 wechat_control

        Returns:
            微信控件.
        """
        return wechat_control()

    @classmethod
    @requires_init
    def close_window(cls):
        """
        关闭微信主窗口.

        如果微信主窗口不存在, 则不进行任何操作.
        不会报错.
        """
        try:
            control = get_wechat_window_control()  # 只对任务栏中的微信窗口操作.
            control.SetFocus()
            (control.ToolBarControl(Depth=4)
             .ButtonControl(Name="关闭", searchDepth=1).Click(simulateMove=False,
                                                              waitTime=WAIT_TIME))
        except WeChatError as e:
            project_logger.debug(f"close_window: {e}")

    @classmethod
    @requires_init
    def search(cls, pattern: str) -> None:
        """
        使用微信的搜索框搜索内容,
            - 如果搜索内容是聊天窗口名称, 则会将微信定位至此聊天窗口.
                - 当搜索到的聊天窗口以独立窗口存在的时候也能正常聚焦到聊天窗口.
            - 如果搜索内容不是聊天窗口名称, 可能会弹出搜索记录窗口, 对此脚本影响未知.

        Parameters:
            pattern: 搜索字符串.

        Raises:
            WeChatError: 见 wechat_control 函数.
        """
        wechat_control().SetFocus()
        search_edit = wechat_control().EditControl(Depth=7, Name="搜索")
        search_edit.Click(simulateMove=False, waitTime=WAIT_TIME)
        if uiautomation.SetClipboardText(pattern):
            search_edit.SendKeys("{Ctrl}a{Ctrl}v{Enter}", waitTime=WAIT_TIME)
        else:
            project_logger.error(f"search: failed to set clipboard.")

    @classmethod
    def locate_chat(cls, name: str | None = None) -> uiautomation.EditControl:
        """
        获取当前聊天窗口输入框的 Control.
        支持获取独立聊天窗口中的输入框和微信主窗口中的聊天框.

        此方法不会执行聊天框搜索操作, 需要提前手动调用 search 方法将焦点至于指定的聊天框.

        Parameters:
            name: 聊天框的名称.

        对于 name:

        - 如果没有指定, 那么使用微信主窗口的聊天输入框.
            - 如果主窗口没有聊天框, 报 LookupError.
        - 如果指定了,
            - 如果当前微信主窗口处于 name 对应的聊天框, 使用此聊天框.
            - 如果当前微信主窗口不处于 name 对应的聊天框, 在独立窗口中寻找 name 聊天窗口,
                - 如果找到了此聊天窗口, 使用此聊天框.
                - 如果没找到, 报 LookupError.


        Raises:
            WeChatError: 见 wechat_control 函数.
            LookupError: 找不到微信中的指定组件, 可能是没进入聊天框, 可能是 name 指定的聊天框不存在.
        """
        ec = wechat_control().EditControl(Depth=13)  # 主窗口聊天框.
        if ec.Exists(0, 0) and ec.Name == (name or ec.Name):
            return ec
        if name is None:
            # 没有指定 name 时, 无法对独立窗口进行搜索, 故直接报错.
            raise LookupError("failed to locate chat in main wechat window.")
        standalone = uiautomation.WindowControl(searchDepth=1, ClassName="ChatWnd", Name=name)
        ec = standalone.EditControl(Name="输入")
        if ec.Exists(0, 0) and ec.Name == "输入":
            return ec
        raise LookupError(f"failed to locate chat: {name}")

    @classmethod
    def switch_to(cls, name: str) -> uiautomation.EditControl:
        """
        获取指定聊天对象聊天框的 EditControl, 不需要提前设置焦点到聊天框.

        Raises:
            WeChatError: 见 wechat_control 函数.
        """
        try:
            return cls.locate_chat(name)  # 尝试直接获取窗口.
        except LookupError:
            cls.search(name)
            return cls.locate_chat(name)

    @classmethod
    @requires_init
    def send_message(cls, name: str, text: str):
        """
        向指定聊天对象发送文字消息.

        Parameters:
            name: 聊天对象名称.
            text: 发送的消息.

        Raises:
            WeChatError: 见 wechat_control 函数.

        Returns:
            是否成功发送消息.
        """
        if uiautomation.SetClipboardText(text):
            cls.switch_to(name).SendKeys("{Ctrl}a{Ctrl}v{Enter}", waitTime=WAIT_TIME)
        else:
            project_logger.error(f"send_message: failed to set clipboard.")

    @classmethod
    @requires_init
    def send_img(cls, name: str, img: str | typing.BinaryIO):
        """
        向指定聊天对象发送图片.

        Parameters:
            name: 聊天对象名称.
            img: 图片本地路径或者图片文件二进制输入流.

        Raises:
            WeChatError: 见 wechat_control 函数.
        """

        if isinstance(img, str):
            # img 是图片路径.
            bitmap = uiautomation.Bitmap.FromFile(img)
        else:
            # img 是图片输入流.
            with tempfile.NamedTemporaryFile(
                    # suffix=".png", # 这句可不加, 就算没有后缀, FromFile 也能读取图片.
                    delete_on_close=False  # 选择在上下文结束的时候才删除文件, 以便 FromFile 读取.
            ) as temp_img:
                temp_img.write(img.read())  # 估计图片文件不会太大, 直接读取然后写应该没什么问题.
                temp_img.close()
                # 这个方法不会加载图片文件, 而是创建一个指向图片文件的 bitmap, 这里需要关闭 temp_img 才能读取.
                lazy_bitmap = uiautomation.Bitmap.FromFile(temp_img.name)
                # 让 bitmap 加载到内存.
                bitmap = uiautomation.Bitmap(lazy_bitmap.Width, lazy_bitmap.Height)
                bitmap.Paste(0, 0, lazy_bitmap)
                del lazy_bitmap  # 删除原来的指向临时文件的 bitmap 以便上下文管理器删除临时文件.

        if uiautomation.SetClipboardBitmap(bitmap):
            cls.switch_to(name).SendKeys("{Ctrl}a{Ctrl}v{Enter}", waitTime=WAIT_TIME)
        else:
            project_logger.error(f"send_img: failed to set clipboard.")

    @classmethod
    @requires_init
    def send_file(cls, name: str, filepath: str):
        """
        向指定聊天对象发送文件, 只能发送单个文件, 不能发送目录, 不能发送空文件.

        微信在发送文件出现问题时会弹出一个窗口, 不过不影响接下来的脚本向其发送消息, 可以直接忽视.

        Parameters:
            name: 聊天对象名称.
            filepath: 发送文件的路径.

        Raises:
            WeChatError: 见 wechat_control 函数.
            FileNotFoundError: 传入的目录表示的文件不存在或者不是文件.
            FileIsEmptyError: 文件为空, 无法通过微信发送.
        """
        from src.cpp.copyfile import copyfile  # 延迟导入, 不用此功能时, 可以省略编译步骤.
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"failed to open file: {filepath}.")
        if os.path.getsize(filepath) == 0:
            raise FileIsEmptyError(f"{filepath} is empty, can't be sent through wechat.")
        if copyfile(filepath):
            project_logger.error(f"send_file: clipboard operation failed.")
        else:
            cls.switch_to(name).SendKeys("{Ctrl}a{Ctrl}v{Enter}", waitTime=WAIT_TIME)


wx = WeChat  # 使用时直接使用 wx.xxx() 即可.
