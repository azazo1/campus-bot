import os
import pickle
import unittest
from pprint import pprint

from src.log import init, project_logger
from src.studyroom import StudyRoomCache
from src.studyroom.query import RoomQuery
from src.studyroom.available import process_reservation_data
from src.uia.login import get_login_cache, LoginError

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
    """测试 RoomQuery 类的功能"""

    def setUp(self):
        init()
        self.cache = load_cache()
        self.query = RoomQuery(self.cache.get_cache(StudyRoomCache))

    def test_available_room(self):
        test_data = self.query.query_room_infos()
        pprint(test_data)
        processed_data = process_reservation_data(test_data)
        pprint(processed_data)
