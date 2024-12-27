import requests

from datetime import datetime, timedelta
from typing import List, Optional, Dict

from src.studyroom import Request, StudyRoomCache


class StudyRoomQuery(Request):
    """
    查询研修间的房间信息类.
    """

    def __init__(self, cache: StudyRoomCache):
        super().__init__(cache)

    def query_roomInfos(self) -> Optional[List[dict]]:
        """
        查询研修间的房间信息。

        URL: https://studyroom.ecnu.edu.cn/ic-web/roomDevice/roomInfos
        Method: GET
        Headers:
            Cookie: ic-cookie

        Tips:
            本 GET 请求无法提供负载, 故只能请求本日的所有信息
            src.StudyRoom.available.process_reservation_data 可以处理本日的信息.

        Returns:
            list: 包含房间信息的字典列表
        """
        url = "https://studyroom.ecnu.edu.cn/ic-web/roomDevice/roomInfos"
        headers = {
            "Cookie": f"ic-cookie={self.cache.cookies.get('ic-cookie')}"
        }
        response = self.get(url, headers=headers)
        json_output = self.check_login_and_extract_data(response, expected_code=0)
        return json_output

    def query_roomsAvailable(self, day: str = "today") -> Optional[List[dict]]:
        """
        查询当前类别的研修间的可用房间, 在局限于一个校区或钟爱某个类别的研修间时较为有用.

        URL: https://studyroom.ecnu.edu.cn/ic-web/roomDevice/roomAvailable
        Method: GET

        Parameters:
            day: str, 日期, 可选值为 "today" 或 "tomorrow" 或 "day_after_tomorrow".

        Tips:
            本接口可以查询今日、明日、后天的相关信息.

        Returns:
            list: 包含可用房间信息的字典列表，如果请求成功。
        """
        if day == "today":
            target_date = datetime.today()
        elif day == "tomorrow":
            target_date = datetime.today() + timedelta(days=1)
        elif day == "day_after_tomorrow":
            target_date = datetime.today() + timedelta(days=2)
        else:
            raise ValueError("day must be 'today', 'tomorrow', or 'day_after_tomorrow'")

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
            "pageSize": 30,  # 最大化查询数量, 其实研修间也没有 30 个
            "kindIds": 3675133,  # 测试点为普陀研究室 (木门)
            "labId": "",
            "campusId": 2
        }

        response = requests.get(url, headers=headers, params=params)
        data = self.check_login_and_extract_data(response, expected_code=0)
        return data.get("data")

    def check_resvInfo(
            self,
            needStatus: int
    ) -> Optional[List[Dict]]:
        """
        通过该接口可以查询研修室是否正在使用中, 用于检查签到状态.
        # Todo 考虑后期检验在 29 分钟未签到时自动取消预约.

        示例 url: https://studyroom.ecnu.edu.cn/ic-web/reserve/resvInfo?beginDate=2024-12-23&endDate=2024-12-29&needStatus=6&page=1&pageNum=10&orderKey=gmt_create&orderModel=desc

        Tips:
            resvStatus: 1093 代表正在使用中, 1027 代表已预约但未使用.
            needStatus:
                2 代表查询 (未使用) 的研修间.
                4 代表查询 (已使用) 的研修间.
                6 代表查询 (未使用 + 使用中) 的研修间.
        Returns:
            Optional[List[Dict]]: 返回包含预约信息的列表，如果查询失败则返回 None。
        """
        yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        day_after_tomorrow = (datetime.today() + timedelta(days=2)).strftime("%Y-%m-%d")

        url = "https://studyroom.ecnu.edu.cn/ic-web/reserve/resvInfo"
        headers = {
            "Cookie": f"ic-cookie={self.cache.cookies.get('ic-cookie')}"
        }
        params = {
            "beginDate": yesterday,
            "endDate": day_after_tomorrow,
            "needStatus": needStatus,
            "page": 1,
            "pageNum": 1,
            "orderKey": "gmt_create",
            "orderModel": "desc"
        }

        response = self.get(url, headers=headers, params=params)
        json_output = self.check_login_and_extract_data(response, expected_code=0)

        if json_output and "data" in json_output:
            resv_info_list = json_output["data"]
            return resv_info_list
