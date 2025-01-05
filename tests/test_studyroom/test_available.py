"""
    Tips: 该测试集是 test_roomInfos 的拓展, 在获得响应字段的基础上进行数据处理.
"""
import os
import pickle
import unittest
from pprint import pprint

from src.log import init
from src.studyroom.req import StudyRoomCache
from src.studyroom.query import StudyRoomQuery
from src.studyroom.available import process_reservation_data_in_roomInfos, process_reservation_data_in_roomAvailable
from src.uia.login import get_login_cache

# 缓存文件路径
LOGIN_CACHE_FILE = "login-cache.pickle"


def load_cache() -> StudyRoomCache:
    """
    加载 StudyRoom 登录缓存。如果缓存文件不存在，则调用 grab_from_driver 获取新的缓存。
    """
    if os.path.exists(LOGIN_CACHE_FILE):
        with open(LOGIN_CACHE_FILE, "rb") as f:
            login_cache = pickle.load(f)
    else:
        # 如果缓存文件不存在，调用 `get_login_cache` 获取并保存
        login_cache = get_login_cache(cache_grabbers=[StudyRoomCache.grab_from_driver])
        with open(LOGIN_CACHE_FILE, "wb") as f:
            pickle.dump(login_cache, f)

    # 如果对应的缓存为空, 重新调用 grab_from_driver.
    if login_cache.get_cache(StudyRoomCache) is None:
        login_cache = get_login_cache(cache_grabbers=[StudyRoomCache.grab_from_driver])
        with open(LOGIN_CACHE_FILE, "wb") as f:
            pickle.dump(login_cache, f)

    return login_cache


class RoomQueryTest(unittest.TestCase):
    """
    测试 RoomQuery 类的功能

    Tips:
        该测试集是 test_roomInfos 的拓展, 在获得响应字段的基础上进行数据处理.
    """

    def setUp(self):
        init()
        self.cache = load_cache()
        self.query = StudyRoomQuery(self.cache.get_cache(StudyRoomCache))

    def test_available_room(self):
        test_data = self.query.query_roomInfos()
        processed_data = process_reservation_data_in_roomInfos(test_data)
        pprint(processed_data)

    def test_available_category_rooms(self):
        """
        查询当前类别所有研修间的可用时段.

        Warning:
            查询后天的可用房间时, 本接口可能存在使用时间限制, 或许在每日 22:00 后才能进行查询.

        Tips:
            请进入此 url 肉眼对照可预约时段结果:
                https://studyroom.ecnu.edu.cn/#/ic/researchSpace/3/3675133/2
                -> redirect to https://studyroom.ecnu.edu.cn/#/ic/home
                -> 普陀校区 -> 普陀研究室 (木门)
        """
        test_data = self.query.query_roomsAvailable("day_after_tomorrow", "普陀校区玻璃门研究室")
        # test_data = self.query.query_roomsAvailable("tomorrow", "普陀校区木门研究室")
        # test_data = self.query.query_roomsAvailable("today", "闵行校区研究室")
        processed_data = process_reservation_data_in_roomAvailable(
            data=test_data,
            query_date="tomorrow",
            filter_available_only=True
        )
        pprint(processed_data)
