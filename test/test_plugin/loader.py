import time
import unittest

from src.config import init
from src.plugin import PluginLoader


class TestLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init()
        cls.loader = PluginLoader()

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
