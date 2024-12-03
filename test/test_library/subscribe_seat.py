import os
import pickle
import unittest

from src.config import init, logger
from src.library.query import LibraryQuery
from src.library.seat import SeatFinder
from src.library.subscribe import Subscribe
from src.uia.login import get_login_cache, LibCache

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


class TestSubscribe(unittest.TestCase):
    def setUp(self):
        init()
        self.cache = load_cache()
        self.q = LibraryQuery(self.cache.get_cache(LibCache))
        self.s = Subscribe(self.cache.get_cache(LibCache))

    def test_confirm_subscribe(self):
        """成功运行此测试后, 请检查自己的图书馆内的预约, 及时取消防止造成违规"""
        qs = self.q.quick_select()
        area_id = qs.get_area_by(
            lambda area: "一楼D区自习区" in area["nameMerge"]
        )
        day = self.q.query_date(area_id)[-1]  # 获取次日的日期以进行测试预约, 次日日期的预约取消没有限制.
        time_period = day.times[-1]
        sf = SeatFinder(self.q.query_seats(area_id, time_period))
        seat_id = sf.find_most_isolated().id
        rst = self.s.confirm(seat_id, time_period)
        logger.info(rst)
        return rst

    def test_query_subscribes(self):
        logger.info(self.s.query_subscribes())

    def test_cancel(self):
        rst = self.test_confirm_subscribe()
        self.s.cancel(rst["id"])
