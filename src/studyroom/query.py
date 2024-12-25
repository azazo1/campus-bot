from datetime import datetime, timedelta
from typing import List, Optional

import requests

from src.studyroom import Request, StudyRoomCache


class RoomQuery(Request):
    """
    RoomQuery 类用于查询研修间的房间信息。
    继承自 src.StudyRoom.request.Request。
    """

    def __init__(self, cache: StudyRoomCache):
        """
        初始化 RoomQuery。

        :param cache: StudyRoomCache 实例，用于提供 cookies。
        """
        super().__init__(cache)

    def query_room_infos(self) -> Optional[List[dict]]:
        """
        查询研修间的房间信息。

        URL: https://studyroom.ecnu.edu.cn/ic-web/roomDevice/roomInfos

        Method: GET

        Headers:
            Cookie: ic-cookie

        Returns:
            list: 包含房间信息的字典列表，如果请求成功。
            None: 如果请求失败。
        """
        url = "https://studyroom.ecnu.edu.cn/ic-web/roomDevice/roomInfos"
        headers = {
            "Cookie": f"ic-cookie={self.cache.cookies.get('ic-cookie')}"
        }
        response = self.get(url, headers=headers)
        json_output = self.check_login_and_extract_data(response, expected_code=0)
        return json_output

    def query_rooms(self, day: str = "today") -> Optional[List[dict]]:
        """
        查询研修间的可用房间。

        URL: https://studyroom.ecnu.edu.cn/ic-web/roomDevice/roomAvailable

        Method: GET

        Parameters:
            day: str, 日期, 可选值为 "today" 或 "tomorrow".

        Returns:
            list: 包含可用房间信息的字典列表，如果请求成功。
            None: 如果请求失败。
        """
        if day == "today":
            target_date = datetime.today()
        elif day == "tomorrow":
            target_date = datetime.today() + timedelta(days=1)
        else:
            raise ValueError("day must be 'today' or 'tomorrow'")

        # 格式化日期为 "YYYYMMDD"
        formatted_date = target_date.strftime("%Y%m%d")

        url = "https://studyroom.ecnu.edu.cn/ic-web/reserve"
        headers = {
            "Cookie": f"ic-cookie={self.cache.cookies.get('ic-cookie')}"
        }

        params = {
            "sysKind": 1,
            "resvDates": formatted_date,
            "page": 1,
            "pageSize": 30,
            "kindIds": 3675133,
            "labId": "",
            "campusId": 2
        }

        response = requests.get(url, headers=headers, params=params)
        data = self.check_login_and_extract_data(response, expected_code=0)
        return data.get("data")
