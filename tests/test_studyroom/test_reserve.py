import os
import pickle
import unittest

from src.log import init, project_logger
from src.studyroom import StudyRoomCache
from src.studyroom.reserve import StudyRoomReserve
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
        self.query = StudyRoomReserve(self.cache.get_cache(StudyRoomCache))

    def test_successful_reservation(self):
        """测试成功预约研究间"""
        # 准备预约数据
        payload = {
            "sysKind": 1,  # 必填, 系统类型
            "appAccNo": 142319353,  # 必填,申请预约的用户账号 ID
            "memberKind": 1,  # 必填, 成员类型
            "resvBeginTime": "2024-12-26 20:40:00",  # 必填
            "resvEndTime": "2024-12-26 21:40:00",  # 必填
            "testName": "Python 实践",  # 必填
            "resvMember": [142319353], # 预约人员列表, 如果有多个人才使用
            "resvDev": [11907], # 要预约的设备
            "memo": "仅供学习", # 非必填, 预约前的备注信息
        }

        try:
            response = self.query.reserve_room(payload)
            self.assertIsNotNone(response, "The server did not return a response.")
            self.assertEqual(response.get("code"), 0, f"预约失败: {response.get('message')}")
            project_logger.info(f"Reserve success: {response}")
        except LoginError as e:
            self.fail(f"Login Failed: {e}")
        except Exception as e:
            self.fail(f"An exception occurred during the reservation. Procedure: {e}")
