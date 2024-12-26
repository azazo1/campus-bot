import os
import pickle
import unittest

from src.log import init, project_logger
from src.library import LibCache
from src.uia.login import get_login_cache
from src.library.query import LibraryQuery
from src.library.seat import SeatFinder

LOGIN_CACHE_FILE = "lib-login-cache.pickle"


def load_cache():
    if os.path.exists(LOGIN_CACHE_FILE):
        with open(LOGIN_CACHE_FILE, "rb") as f:
            login_cache = pickle.load(f)
    else:
        login_cache = get_login_cache(cache_grabbers=[LibCache.grab_from_driver])
        with open(LOGIN_CACHE_FILE, "wb") as f:
            pickle.dump(login_cache, f)
    return login_cache


class TestLibrarySeat(unittest.TestCase):
    def setUp(self):
        init()
        self.cache = load_cache()

    def test_find_most_isolate_seat(self):
        """
        Tips:
            请注意, 该测试仅在电脑端运行, 若在手机端登录了图书馆系统, 会 Return Code: 10001,
            此时在类方法 check_login_and_extract_data() raise LoginError 前, 会移除当前的 Lib-login-cache.
            以便重新获取最新有效的 Lib-login-cache.
        """
        q = LibraryQuery(self.cache.get_cache(LibCache))
        qs = q.quick_select()
        area_id = qs.get_most_free_seats_area(
            filter_func=lambda area: "中文理科图书借阅" in area["name"])
        t = q.query_date(area_id)[0].times[0]
        project_logger.info(f"area name: {qs.get_by_id(area_id)['nameMerge']}, timeperiod: {t}")
        seats = q.query_seats(area_id, t)
        sf = SeatFinder(seats)
        project_logger.info(sf.find_most_isolated())
