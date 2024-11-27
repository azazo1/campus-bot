import os
import time
import timeit
import unittest

from src.config import init, logger
from src.wechat import wx
from src.wechat.pc import get_pid_by_name


class TestWechat(unittest.TestCase):
    def setUp(self):
        init()  # 自动移动到项目目录.

    def test_close_window(self):
        wx.close_window()

    def test_search(self):
        wx.search("WechatTest")

    def test_bench_get_pid_by_name(self):
        timeit.main(['-s', 'from src.wechat.pc import get_pid_by_name',
                     '-r', '10',
                     "get_pid_by_name('wechat.exe')"])
        repeat_times = 10
        bench_time = timeit.timeit(lambda: get_pid_by_name("wechat.exe"), number=repeat_times)
        logger.info("%f / %d = %f sec/times", bench_time, repeat_times, bench_time / repeat_times)
        logger.info(get_pid_by_name("wechat.exe"))

    def test_locate_chat(self):
        """
        请在指定的微信聊天框输入 asdf, 然后运行测试.

        请测试各种情况:

        1. 指定聊天窗口在微信主窗口内.
        2. 指定聊天窗口在独立窗口.
        3. 单个独立聊天窗口.
        4. 多个独立聊天窗口.
        5. 聊天窗口在主窗口内但是没被聚焦, 即当前聊天窗口不是指定聊天窗口.

        以上情况可结合测试.
        """
        ec = wx.locate_chat("WechatTest")
        vp = ec.GetValuePattern()
        self.assertEqual(vp.Value, "asdf")

    def test_bench_locate_chat(self):
        wx.search("WechatTest")
        repeat_times = 10
        bench_time = timeit.timeit(lambda: wx.locate_chat("WechatTest") and wx.close_window(),
                                   number=repeat_times)
        logger.info("%f sec of %d times", bench_time, repeat_times)

    def test_send_message(self):
        wx.send_message("WechatTest", "HelloWorld1234")

    def test_send_img(self):
        wx.send_message("WechatTest", "1")
        wx.send_img("WechatTest", "assets/ecnu_logo.png")
        wx.send_message("WechatTest", "2")
        with open("assets/ecnu_logo.png", "rb") as f:
            wx.send_img("WechatTest", f)

    def test_send_file(self):
        for _ in range(10):
            wx.send_file("WechatTest", __file__)
