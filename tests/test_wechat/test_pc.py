import unittest

from src.log import init
from src.wechat.pc import Taskbar, wechat_control, ReserveCursorFocus


class TestPC(unittest.TestCase):
    def setUp(self):
        init()

    def test_click_tray_icon(self):
        tb = Taskbar.get_taskbar()
        with ReserveCursorFocus(reserve_cursor=False):
            with tb.with_icon_expand() as tray:
                self.assertTrue(tray.click("微信"))

    def test_wx(self):
        wechat_control()
