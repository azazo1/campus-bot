import datetime
import os
import pickle
import unittest

from src.config import init
from src.uia.login import get_login_cache, PortalCache
from src.portal.calendar.query import CalendarQuery

LOGIN_CACHE_FILE = "login-cache.pickle"


def load_cache():
    if os.path.exists(LOGIN_CACHE_FILE):
        with open(LOGIN_CACHE_FILE, "rb") as f:
            login_cache = pickle.load(f)
    else:
        login_cache = get_login_cache()
        with open(LOGIN_CACHE_FILE, "wb") as f:
            pickle.dump(login_cache, f)
    return login_cache


class TestCalendar(unittest.TestCase):
    def setUp(self):
        init()
        self.cache = load_cache()
        self.calendar = CalendarQuery(self.cache.get_cache(PortalCache))

    def test_calendar(self):
        now = datetime.datetime.now()
        print(self.calendar.query_user_schedules(
            int(now.timestamp() * 1000),
            int((now + datetime.timedelta(days=1)).timestamp() * 1000),
        ))
