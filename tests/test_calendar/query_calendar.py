import datetime
import os
import pickle
import unittest
from pprint import pprint

from src.config import init
from src.portal import PortalCache
from src.uia.login import get_login_cache
from src.portal.calendar.query import CalendarQuery

LOGIN_CACHE_FILE = "login-cache.pickle"


def load_cache():
    if os.path.exists(LOGIN_CACHE_FILE):
        with open(LOGIN_CACHE_FILE, "rb") as f:
            login_cache = pickle.load(f)
    else:
        login_cache = get_login_cache(cache_grabbers=[PortalCache.grab_from_driver])
        with open(LOGIN_CACHE_FILE, "wb") as f:
            pickle.dump(login_cache, f)
    return login_cache


class TestCalendar(unittest.TestCase):
    def setUp(self):
        init()
        self.cache = load_cache()
        self.calendar = CalendarQuery(self.cache.get_cache(PortalCache))

    def test_user_schedules(self):
        now = datetime.datetime.now()
        pprint(self.calendar.query_user_schedules(
            int(now.timestamp() * 1000),
            int((now + datetime.timedelta(days=1)).timestamp() * 1000),
        ))

    def test_school_calendar(self):
        school_calendar = self.calendar.query_school_calendar()
        pprint(school_calendar)
