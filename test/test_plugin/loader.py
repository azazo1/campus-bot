import unittest

from src.config import init
from src.plugin import PluginLoader


class TestLoader(unittest.TestCase):
    def setUp(self):
        init()
        self.loader = PluginLoader()

    def test_register_plugin(self):
        self.loader.import_plugins()
