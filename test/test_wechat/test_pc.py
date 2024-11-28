import unittest

from src.config import init
from src.wechat.pc import Taskbar, wechat_control


class TestPC(unittest.TestCase):
    def setUp(self):
        init()

    def test_click_tray_icon(self):
        tb = Taskbar.get_taskbar()
        with tb.with_icon_expand() as tray:
            tray.click("微信")

    def test_wx(self):
        wechat_control()
