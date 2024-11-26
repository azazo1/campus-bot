import os
import timeit
import unittest

from src.config import init, logger
from src.wechat import wx
from src.wechat.pc import get_pid_by_name


class TestWechat(unittest.TestCase):
    def setUp(self):
        init() # 自动移动到项目目录.

    def test_close_window(self):
        wx.close_window()

    def test_search(self):
        wx.search("WechatTest")

    def test_bench_get_pid_by_name(self):
        timeit.main(['-s', 'from src.wechat.pc import get_pid_by_name',
                     "get_pid_by_name('wechat.exe')"])
        logger.info(get_pid_by_name("wechat.exe"))
