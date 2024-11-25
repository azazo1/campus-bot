"""
微信窗口控制.
"""
import uiautomation

from .pc import get_wechat_window_control, WeChatError, wechat_control
from ..config import logger, requires_init


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
             .ButtonControl(Name="关闭", searchDepth=1).Click(simulateMove=False))
        except WeChatError as e:
            logger.debug(f"close_window: {e}")

    @classmethod
    def search(cls, text: str):
        """
        使用微信的搜索框搜索内容, 注意如果搜索内容不是联系人的名称的话,
        可能会弹出搜索记录窗口, 对此脚本影响未知.

        Raises:
            WeChatError: 见 wechat_control 函数.
        """
        wechat_control().SetFocus()
        search_edit = wechat_control().EditControl(Depth=7, Name="搜索")
        search_edit.Click(simulateMove=False)
        if uiautomation.SetClipboardText(text):
            search_edit.SendKeys("{Ctrl}a{Ctrl}v{Enter}")
        else:
            logger.error(f"search: failed to set clipboard.")


wx = WeChat  # 使用时直接使用 wx.xxx() 即可.
