import os
import pickle
import unittest

from src.config import init, logger
from src.uia.login import get_login_cache
from src.library.query import LibraryQuery
from src.library.seat import SeatFinder

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


class TestLibrarySeat(unittest.TestCase):
    def setUp(self):
        init()
        self.cache = load_cache()

    def test_find_most_isolate_seat(self):
        q = LibraryQuery(self.cache)
        qs = q.quick_select()
        area_id = qs.get_most_free_seats_area(
            filter_func=lambda area: "中文理科图书借阅" in area["name"])
        t = q.query_date(area_id)[0].times[0]
        logger.info(f"area name: {qs.get_by_id(area_id)['nameMerge']}, timeperiod: {t}")
        seats = q.query_seats(area_id, t)
        sf = SeatFinder(seats)
        logger.info(sf.find_most_isolated())
