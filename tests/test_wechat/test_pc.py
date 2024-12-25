import unittest

from src.config import init
from src.wechat.pc import Taskbar, wechat_control, ReserveCursorFocus


class TestPC(unittest.TestCase):
    def setUp(self):
        init()

    def test_click_tray_icon(self):
        '''
        本测试需要微信收纳在任务栏的拓展隐藏栏 (显示隐藏的图标) 中才能通过.
        '''
        tb = Taskbar.get_taskbar()
        with ReserveCursorFocus(reserve_cursor=False):
            with tb.with_icon_expand() as tray:
                self.assertTrue(tray.click("微信"))

    def test_wx(self):
        wechat_control()
