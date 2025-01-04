import os
import pickle
import unittest
from pprint import pprint

from src.log import init
from src.portal import PortalCache
from src.uia.login import get_login_cache
from src.portal.calendar.query import CalendarQuery
from tools.classtable.generate_latex_table import LatexGenerator

LOGIN_CACHE_FILE = "login-cache.pickle"


def load_cache() -> PortalCache:
    if os.path.exists(LOGIN_CACHE_FILE):
        with open(LOGIN_CACHE_FILE, "rb") as f:
            login_cache = pickle.load(f)
    else:
        login_cache = get_login_cache(cache_grabbers=[PortalCache.grab_from_driver])
        with open(LOGIN_CACHE_FILE, "wb") as f:
            pickle.dump(login_cache, f)

    # 如果对应的缓存为空, 重新调用 grab_from_driver.
    if login_cache.get_cache(PortalCache) is None:
        login_cache = get_login_cache(cache_grabbers=[PortalCache.grab_from_driver])
        with open(LOGIN_CACHE_FILE, "wb") as f:
            pickle.dump(login_cache, f)

    return login_cache


class TestCalendar(unittest.TestCase):
    def setUp(self):
        init()
        self.cache = load_cache()
        self.calendar = CalendarQuery(self.cache.get_cache(PortalCache))

    def test_get_class_table(self):
        double_week_class_table = self.calendar.query_user_class_table()
        pprint(double_week_class_table)
        generator = LatexGenerator(double_week_class_table)
        generator.classify_courses()
        generator.generate_latex()
        generator.compile_latex()
