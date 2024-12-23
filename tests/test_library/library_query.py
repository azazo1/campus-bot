import os
import pickle
import unittest

from src.config import init, project_logger
from src.library import LibCache
from src.uia.login import get_login_cache
from src.library.query import LibraryQuery

LOGIN_CACHE_FILE = "login-cache.pickle"


def load_cache():
    if os.path.exists(LOGIN_CACHE_FILE):
        with open(LOGIN_CACHE_FILE, "rb") as f:
            login_cache = pickle.load(f)
    else:
        login_cache = get_login_cache(cache_grabbers=[LibCache.grab_from_driver])
        with open(LOGIN_CACHE_FILE, "wb") as f:
            pickle.dump(login_cache, f)
    return login_cache


class LibraryQueryTest(unittest.TestCase):
    def setUp(self):
        init()
        self.cache = load_cache()
        self.q = LibraryQuery(self.cache.get_cache(LibCache))

    def test_quick_select(self):
        qs = self.q.quick_select()
        id_ = qs.get_most_free_seats_area()
        most_free_seats = qs.get_by_id(id_)
        project_logger.info(most_free_seats)
        storey = qs.get_by_id(int(most_free_seats["parentId"]))
        project_logger.info(storey)
        premises = qs.get_by_id(int(storey["parentId"]))
        project_logger.info(premises)
        project_logger.info(qs.get_premises_of(id_))
        project_logger.info(qs.get_premises_of(21))

    def test_query_date(self):
        qs = self.q.quick_select()
        id_ = qs.get_most_free_seats_area()
        days = self.q.query_date(id_)
        project_logger.info(days)

    def test_query_seats(self):
        qs = self.q.quick_select()
        id_ = qs.get_most_free_seats_area()
        days = self.q.query_date(id_)
        ret = self.q.query_seats(id_, days[0].times[0])
        project_logger.info(ret)
