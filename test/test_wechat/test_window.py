import os
import timeit
import unittest

from src.config import init, logger
from src.wechat import wx


class TestWechat(unittest.TestCase):
    def setUp(self):
        os.chdir("..")  # test 默认运行在 test 文件夹, 向上到项目文件夹.
        init()

    def test_close_window(self):
        wx.close_window()

    def test_search(self):
        wx.search("WechatTest")

    def test_bench_get_pid_by_name(self):
        timeit.main(['-s','from src.wechat.pc import get_pid_by_name', "get_pid_by_name('wechat.exe', True)"])

    def tearDown(self):
        pass
