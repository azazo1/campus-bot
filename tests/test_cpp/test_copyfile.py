import unittest

import win32clipboard

from src.config import project_logger, init
from src.cpp.copyfile_build import copyfile_setup


class TestCopyFile(unittest.TestCase):
    '''
    该测试点在首次运行时可能报错, 请尝试多次进入测试点.
    可从 class 定义中进入.
    '''
    def setUp(self):
        init()

    def test_build_copyfile(self):
        copyfile_setup.build()  # 执行错误会报错.

    def test_copyfile(self):
        from src.cpp.copyfile import copyfile
        copyfile(__file__)
        win32clipboard.OpenClipboard()  # 执行错误会直接抛出异常
        try:
            self.assertEqual(
                win32clipboard.GetClipboardData(win32clipboard.CF_HDROP),
                (__file__,)
            )
        finally:
            try:
                win32clipboard.CloseClipboard()
            except Exception as e:
                project_logger.warning(e)
