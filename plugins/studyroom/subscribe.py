from typing import Optional
from datetime import datetime, timedelta

from .available import process_reservation_data_in_roomAvailable
from .req import StudyRoomCache
from .req import Request, LoginError
from .query import StudyRoomQuery

class StudyRoomReserve(Request):
    """针对 StudyRoom 的请求类，继承自独立的 Request 类，扩展一些 StudyRoom 相关的功能。"""

    def __init__(self, cache: StudyRoomCache):
        super().__init__(cache)
        self.query = StudyRoomQuery(self.cache)

    def _fetch_userInfo(self) -> Optional[dict]:
        """
        获取用户的基本信息, 最主要的是提交预约 POST 请求时传入的 appAccNo 参数从此获取.

        url: https://studyroom.ecnu.edu.cn/ic-web/auth/userInfo

        Returns:
            dict, 包含用户 ID, 学号, 真实姓名, 学院名字, token, accNo 等信息.
        """
        url = "https://studyroom.ecnu.edu.cn/ic-web/auth/userInfo"
        headers = {
            "Cookie": f"ic-cookie={self.cache.cookies.get('ic-cookie')}"
        }
        response = self.get(url, headers=headers)
        json_output = self.check_login_and_extract_data(response, expected_code=0)

        # 仅提取可能需要的字段
        if json_output and "data" in json_output:
            user_data = json_output["data"]
            extracted_data = {
                "uuid": user_data.get("uuid"),  # 用户 ID, 但该 uuid 与指定研修间预约的 uuid 不一致
                "pid": user_data.get("pid"),  # 学号
                "trueName": user_data.get("trueName"),  # 真实姓名
                "className": user_data.get("className"),  # 学院名字
                "token": user_data.get("token"),  # 暂时不知道用来干嘛, 可能有用
                "accNo": user_data.get("accNo"),  # 用来发送 Reserve
            }
            return extracted_data

    def _get_room_uuid(self):
        """
        获取已预约研修间的 uuid, 用于取消预约.

        Url:
        """
        self.query = StudyRoomQuery(self.cache)
        self.uuid = self.query.check_resvInfo(needStatus=6)[0].get("uuid")
        return self.uuid

    def _reserve_room(
            self,
            resvBeginTime: str,
            resvEndTime: str,
            testName: str,
            resvDev: list,
            memo: str = ""
    ) -> dict:
        """
        封装预约研修间的 POST 请求。

        Parameters:
            resvBeginTime: str, 预约开始时间（格式: YYYY-MM-DD HH:MM:SS）。
            resvEndTime: str, 预约结束时间（格式: YYYY-MM-DD HH:MM:SS）。
            testName: str, 测试名称或预约名称。
            resvDev: list, 要预约的设备列表（设备 ID）。
            memo: str, 可选，备注信息。

        url: https://studyroom.ecnu.edu.cn/ic-web/reserve

        Returns:
            dict, 返回服务器的响应数据。
        """
        url = "https://studyroom.ecnu.edu.cn/ic-web/reserve"
        cookies = self.cache.cookies
        ic_cookie = cookies.get("ic-cookie")
        if not ic_cookie:
            raise LoginError("ic-cookie not found in cookies.")

        headers = {
            "Cookie": f"ic-cookie={ic_cookie}",
        }

        # appAccNo: int, 用户账号 ID, 从 _fetch_userInfo 获取.
        appAccNo = self._fetch_userInfo().get("accNo")

        payload = {
            "sysKind": 1,  # 系统类型，默认为 1
            "appAccNo": appAccNo,
            "memberKind": 1,  # 成员类型，默认为 1
            "resvBeginTime": resvBeginTime,
            "resvEndTime": resvEndTime,
            "testName": testName,
            "resvMember": [appAccNo],  # 默认预约人员列表只有当前用户
            "resvDev": resvDev,
            "memo": memo,
        }

        response = self.post(url, json_payload=payload, headers=headers)
        return self.check_login_and_extract_data(response, expected_code=0)

    def submit_reserve(
            self,
            day: str,
            kind_name: str,
            min_duration_minutes: int,
            max_duration_minutes: int = 240
    ) -> dict:
        """
        根据提供的参数执行预约操作。

        参数:
            day (str): 要预约的日期（'today'，'tomorrow'，'day_after_tomorrow'）。
            kind_name (str): 表示要预约的房间类型。
            min_duration_minutes (int): 预约的最短时长（分钟）。
            max_duration_minutes (int): 预约的最长时长（分钟），默认 240 分钟。

        返回:
            dict: 如果预约成功，返回服务器的响应数据。
        """
        # 获取可用房间
        available_rooms = self.query.query_roomsAvailable(day=day, kind_name=kind_name)
        processed_data = process_reservation_data_in_roomAvailable(
            data=available_rooms,
            query_date=day,
            filter_available_only=True
        )
        # project_logger.info(f"{day} 可用房间处理后数据: {processed_data}")

        if not processed_data:
            raise AssertionError(f"在 {day} 没有找到可用的房间。")

        best_room = None
        best_slot = None
        longest_duration = timedelta(minutes=0)

        min_duration = timedelta(minutes=min_duration_minutes)
        max_duration = timedelta(minutes=max_duration_minutes)

        for room in processed_data:
            for slot in room.get("availableInfos", []):
                begin_time_str = slot.get("availableBeginTime")
                end_time_str = slot.get("availableEndTime")
                if not begin_time_str or not end_time_str:
                    continue

                begin_time = datetime.strptime(begin_time_str, "%Y-%m-%d %H:%M:%S")
                end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
                duration = end_time - begin_time
                # project_logger.debug(
                #     f"房间 '{room['roomName']}' 有可用时段从 {begin_time} 到 {end_time}（时长: {duration}）"
                # )

                if min_duration <= duration <= max_duration and duration > longest_duration:
                    best_room = room
                    best_slot = (begin_time_str, end_time_str)
                    longest_duration = duration
                    # project_logger.debug(
                    #     f"在房间 '{room['roomName']}' 找到新的最佳时段，时长 {duration}"
                    # )

        if not best_room or not best_slot:
            raise AssertionError(
                f"在 {day} 没有找到满足最短时长 {min_duration_minutes} 分钟且不超过 {max_duration_minutes} 分钟的可用时段，"
                f"房间类型 ID: {kind_name}。"
            )

        # project_logger.info(
        #     f"选择的房间 '{best_room['roomName']}'，时间段 {best_slot}"
        # )

        resvBeginTime, resvEndTime = best_slot
        resvDev = [best_room.get("devId")]
        testName = f"自动预约 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        memo = "自动化测试预约"

        response = self._reserve_room(
            resvBeginTime=resvBeginTime,
            resvEndTime=resvEndTime,
            testName=testName,
            resvDev=resvDev,
            memo=memo
        )
        # project_logger.info(f"自动预约结束: {response}")
        return response

    def cancel_reservation(self, uuid: str) -> dict:
        """
        取消特定的研修间预约.

        Url: https://studyroom.ecnu.edu.cn/ic-web/reserve/delete
        Tips:
            该取消接口需要通过查询预约状态获取 uuid:
            -> 通过此 url 查询: https://studyroom.ecnu.edu.cn/ic-web/reserve/resvInfo
        """
        url = "https://studyroom.ecnu.edu.cn/ic-web/reserve/delete"
        headers = {
            "Cookie": f"ic-cookie={self.cache.cookies.get('ic-cookie')}"
        }
        payload = {
            "uuid": uuid
        }
        response = self.post(url, headers=headers, json_payload=payload)
        return self.check_login_and_extract_data(response, expected_code=0)
