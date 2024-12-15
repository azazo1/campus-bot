import time
import unittest

from src.config import init
from src.plugin import PluginLoader


class TestLoader(unittest.TestCase):
    def setUp(self):
        init()
        self.loader = PluginLoader()

    def tearDown(self):
        """
        清理 PluginLoader 实例, 避免触发 SingleInstanceError.

        Tips: 可以直接从 class TestLoader 类进入, 一次运行多个测试.
        """
        if self.loader:
            self.loader.close()
            PluginLoader.reset_instance()
        self.loader = None

    def test_register_plugin(self):
        self.loader.import_plugins()

    def test_loader_all(self):
        self.loader.import_plugins()
        self.loader.load_config()
        self.loader.load_all()
        # self.loader.ecnu_uia_login()
        for i in range(3):
            self.loader.poll()
            time.sleep(1)
        self.loader.save_config()
        self.loader.close()
