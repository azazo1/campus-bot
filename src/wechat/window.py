"""
微信窗口控制.
"""
from __future__ import annotations

import typing

import uiautomation
from .pc import get_wechat_window_control, WeChatError, wechat_control, CLICK_WAIT_TIME
from ..config import logger, requires_init

SEND_KEYS_WAIT_TIME = 0.3


class WeChat:
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
                                                              waitTime=CLICK_WAIT_TIME))
        except WeChatError as e:
            logger.debug(f"close_window: {e}")

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
        search_edit.Click(simulateMove=False)
        if uiautomation.SetClipboardText(pattern):
            search_edit.SendKeys("{Ctrl}a{Ctrl}v{Enter}", waitTime=SEND_KEYS_WAIT_TIME)
        else:
            logger.error(f"search: failed to set clipboard.")

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
    @requires_init
    def send_message(cls, name: str, text: str):
        """
        向指定聊天对象发送文字消息.

        Parameters:
            name: 聊天对象名称.
            text: 发送的消息.

        Raises:
            WeChatError: 见 wechat_control 函数.
        """
        try:
            ec = cls.locate_chat(name) # 尝试直接获取窗口.
        except LookupError:
            cls.search(name)
            ec = cls.locate_chat(name)
        if uiautomation.SetClipboardText(text):
            ec.SendKeys("{Ctrl}a{Ctrl}v{Enter}", waitTime=SEND_KEYS_WAIT_TIME)
        else:
            logger.error(f"send_message: failed to set clipboard.")

    @classmethod
    def send_img(cls, name: str, img: str | typing.BinaryIO):
        """
        向指定聊天对象发送图片.

        Parameters:
            name: 聊天对象名称.
            img: 图片本地路径或者图片文件二进制输入流.

        Raises:
            WeChatError: 见 wechat_control 函数.
        """


wx = WeChat  # 使用时直接使用 wx.xxx() 即可.
