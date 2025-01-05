import os
import pickle
import unittest
from datetime import datetime, timedelta
from pprint import pprint

from src.log import init, project_logger
from src.studyroom.req import StudyRoomCache
from src.studyroom.available import process_reservation_data_in_roomAvailable
from src.studyroom.subscribe import StudyRoomReserve
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

    def _perform_reservation(self, day: str, kind_name: str, min_duration_minutes: int):
        """
        根据提供的参数执行预约操作.

        参数:
            day (str): 要预约的日期（'today'，'tomorrow'，'day_after_tomorrow'）
            kind_name (str): 表示要预约的房间类型 ()
            min_duration_minutes (int): 预约的最短时长（分钟）

        返回:
            dict: 如果预约成功，返回服务器的响应数据。
        """
        # 记录开始预约的信息
        project_logger.info(
            f"开始预约，日期: {day}, 房间类型 ID: {kind_name}, 最短时长: {min_duration_minutes} 分钟"
        )

        # 获取可用房间, 此时的数据仍处于未处理状态, 调用 process_reservation_data_in_roomAvailable 进行处理
        available_rooms = self.query.query_roomsAvailable(day=day, kind_name=kind_name)
        processed_data = process_reservation_data_in_roomAvailable(
            data=available_rooms,  # 需要处理的数据
            query_date=day,
            filter_available_only=True  # 仅显示可用时长不为空的房间
        )
        project_logger.info(f"{day} 可用房间处理后数据: {processed_data}")

        # 如果没有可用房间，测试失败
        if not processed_data:
            self.fail(f"在 {day} 没有找到可用的房间。")

        # 查找满足最短预约时间且可用时段尽量久的房间
        best_room = None  # 最佳房间
        best_slot = None  # 最佳时间段
        longest_duration = timedelta(minutes=0)  # 当前找到的最长时长

        # 定义最短和最长预约时长
        min_duration = timedelta(minutes=min_duration_minutes)
        max_duration = timedelta(minutes=240)  # 最大预约时长为 240 分钟

        for room in processed_data:
            for slot in room.get("availableInfos", []):
                begin_time_str = slot.get("availableBeginTime")
                end_time_str = slot.get("availableEndTime")
                if not begin_time_str or not end_time_str:
                    continue  # 如果时间信息不完整，跳过该时间段

                # 解析时间字符串为 datetime 对象
                begin_time = datetime.strptime(begin_time_str, "%Y-%m-%d %H:%M:%S")
                end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
                duration = end_time - begin_time  # 计算时长
                project_logger.debug(
                    f"房间 '{room['roomName']}' 有可用时段从 {begin_time} 到 {end_time}（时长: {duration}）"
                )

                # 检查该时段是否满足最短时长且不超过最大时长，并且是当前最长
                if min_duration <= duration <= max_duration and duration > longest_duration:
                    best_room = room
                    best_slot = (begin_time_str, end_time_str)
                    longest_duration = duration
                    project_logger.debug(
                        f"在房间 '{room['roomName']}' 找到新的最佳时段，时长 {duration}"
                    )

        # 如果没有找到符合条件的房间或时间段，测试失败
        if not best_room or not best_slot:
            self.fail(
                f"在 {day} 没有找到满足最短时长 {min_duration_minutes} 分钟且不超过240分钟的可用时段，"
                f"房间类型 ID: {kind_name}。"
            )

        # 记录选择的房间和时间段
        project_logger.info(
            f"选择的房间 '{best_room['roomName']}'，时间段 {best_slot}"
        )

        # 预约房间
        resvBeginTime, resvEndTime = best_slot
        resvDev = [best_room.get("devId")]  # 房间的设备 ID
        testName = f"自动预约 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"  # 预约名称
        memo = "自动化测试预约"  # 预约备注
        response = self.reserve.reserve_room(
            resvBeginTime=resvBeginTime,
            resvEndTime=resvEndTime,
            testName=testName,
            resvDev=resvDev,
            memo=memo
        )
        project_logger.info(f"自动预约结束: {response}")
        return response

    def test_auto_reservation(self):
        """
        测试今天预约特定 kindId 的房间，最短预约时间为 60 分钟.

        后天有关的查询需要等到每日 22:00 后.
        """
        self._perform_reservation("tomorrow", "普陀校区木门研究室", 60)
        # self._perform_reservation("day_after_tomorrow", "闵行校区研究室", 90)
        # self._perform_reservation("tomorrow", "普陀校区玻璃门研究室", 120)

    def test_auto_cancel(self):
        """
        自动取消预约研修间, 用于测试取消预约功能的全自动化.

        该测试应在 test_auto_reservation 后运行.
        """
        pass
