import os
import pickle
import unittest
from datetime import datetime, timedelta
from pprint import pprint

from src.log import init, project_logger
from src.studyroom import StudyRoomCache
from src.studyroom.available import process_reservation_data_in_roomAvailable
from src.studyroom.reserve import StudyRoomReserve
from src.studyroom.query import StudyRoomQuery
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


class RoomReserver(unittest.TestCase):
    """测试 StudyRoomReserve 类的功能"""

    def setUp(self):
        init()
        self.cache = load_cache()
        self.reserve = StudyRoomReserve(self.cache.get_cache(StudyRoomCache))
        self.query = StudyRoomQuery(self.cache.get_cache(StudyRoomCache))

    def test_auto_reservation(self):
        """
        自动预约研修间, 用于测试预约功能的全自动化.

        Steps:
            1. 调用 _fetch_userInfo 获取用户信息.
            2. 调用 query_rooms_available_(today, tomorrow, day_after_tomorrow) 获取可用房间.
            3. 构造 payload 请求头, 调用 reserve_room 方法.
        """
        try:
            # Step 1: 获取用户信息
            user_info = self.reserve._fetch_userInfo()
            if not user_info:
                self.fail("无法获取用户信息, 预约终止.")
            appAccNo = user_info.get("accNo")
            if not appAccNo:
                self.fail("用户的 accNo 不存在, 无法进行预约.")

            available_rooms_tomorrow = self.query.query_roomsAvailable(day="tomorrow")
            processed_data = process_reservation_data_in_roomAvailable(
                data=available_rooms_tomorrow,
                query_date="tomorrow",
                filter_available_only=True
            )
            pprint(processed_data)  # 获取有预约时段的房间信息
            project_logger.info("Available rooms tomorrow: %s", processed_data)

            # 这里假设选择第一个可用的房间和时间段
            selected_room = processed_data[0]
            project_logger.info("Selected room: %s", selected_room)

            # 选择房间中的可用时间段, 这里为了测试先选择第一个可用时间段
            AvailableInfos = selected_room.get("availableInfos")
            resvBeginTime = AvailableInfos[0].get("availableBeginTime")
            resvEndTime = AvailableInfos[0].get("availableEndTime")
            project_logger.info("Selected room: %s", selected_room)

            # 传递 roomId 让系统知道要预约哪个房间
            resvDev = [selected_room.get("devId")]
            project_logger.info("Selected device (roomId): %s", resvDev)

            # testName: 预约主题, memo: 预约备注
            testName = f"自动预约测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            memo = "自动化测试预约"

            if not resvBeginTime or not resvEndTime or not resvDev:
                self.fail("选定的房间信息不完整，无法进行预约。")

            response = self.reserve.reserve_room(
                resvBeginTime=resvBeginTime,
                resvEndTime=resvEndTime,
                testName=testName,
                resvDev=resvDev,
                memo=memo
            )

            self.assertIsNotNone(response, "服务器未返回任何响应。")
            self.assertEqual(response.get("code"), 0, f"预约失败: {response.get('message')}")
            project_logger.info(f"自动预约成功: {response}")
        except LoginError as e:
            self.fail(f"Login Error: {e}")
        except Exception as e:
            self.fail(f"The reservation process is abnormal. Procedure: {e}")

    def test_auto_cancel(self):
        """
        自动取消预约研修间, 用于测试取消预约功能的全自动化.

        该测试应在 test_auto_reservation 后运行.
        """
        try:
            cancel_response = self.reserve.cancel_reservation()
            pprint(cancel_response)
            project_logger.info("Cancel response: %s", cancel_response)
            self.assertIsNotNone(cancel_response, "服务器未返回任何响应。")
        except LoginError as e:
            self.fail(f"Login Error: {e}")
