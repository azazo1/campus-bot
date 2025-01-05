import requests

from datetime import datetime, timedelta
from typing import List, Optional, Dict

from .req import Request, StudyRoomCache, ROOM_KINDID


class StudyRoomQuery(Request):
    """
    查询研修间的房间信息类.
    """

    def __init__(self, cache: StudyRoomCache):
        super().__init__(cache)

    def query_roomsAvailable(self, day: str = "today", kind_name: str = None) -> Optional[List[dict]]:
        """
        查询当前类别的研修间的可用房间, 在局限于一个校区或钟爱某个类别的研修间时较为有用.

        URL: https://studyroom.ecnu.edu.cn/ic-web/roomDevice/roomAvailable
        Method: GET

        Parameters:
            day: str, 日期, 可选值为 "today" 或 "tomorrow" 或 "day_after_tomorrow".
            kind_name: str, 房间名称，目前仅支持 "普陀校区木门研究室"、"普陀校区玻璃门研究室"、"闵行校区研究室".
                            因为只有这三个房间支持单人预约.

        Tips:
            本接口可以查询今日、明日、后天的相关信息.

        Returns:
            list: 包含可用房间信息的字典列表，如果请求成功。
        """
        # 确定目标日期
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

        # 根据房间名称获取 kindId 和 campusId
        if kind_name not in ROOM_KINDID:
            raise ValueError(f"Invalid kindName: {kind_name}. Must be one of {list(ROOM_KINDID.keys())}")

        kindId = ROOM_KINDID[kind_name]
        campusId = 2 if "普陀校区" in kind_name else 1  # 动态设置 campusId，根据房间名称判断校区

        url = "https://studyroom.ecnu.edu.cn/ic-web/reserve"
        headers = {
            "Cookie": f"ic-cookie={self.cache.cookies.get('ic-cookie')}"
        }

        params = {
            "sysKind": 1,
            "resvDates": formatted_date,
            "page": 1,
            "pageSize": 30,  # 最大化查询数量, 其实研修间也没有 30 个
            "kindIds": kindId,  # 使用动态获取的 kindId
            "labId": "",
            "campusId": campusId  # 动态设置 campusId
        }

        # 发送请求
        response = requests.get(url, headers=headers, params=params)

        # 提取和检查数据
        data = self.check_login_and_extract_data(response, expected_code=0)
        return data.get("data")

    def check_resvInfo(
            self,
            needStatus: int
    ) -> Optional[List[Dict]]:
        """
        通过该接口可以查询研修室是否正在使用中, 用于检查签到状态.

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
        four_days_later = (datetime.today() + timedelta(days=4)).strftime("%Y-%m-%d")

        url = "https://studyroom.ecnu.edu.cn/ic-web/reserve/resvInfo"
        headers = {
            "Cookie": f"ic-cookie={self.cache.cookies.get('ic-cookie')}"
        }
        params = {
            "beginDate": yesterday,
            "endDate": four_days_later,  # 查询未来 4 天的预约信息
            "needStatus": needStatus,  # 需要查询的状态
            "page": 1,
            "pageNum": 10,  # 本查询支持的最大数量, 也没人预约 10 个研修间
            "orderKey": "gmt_create",
            "orderModel": "desc"
        }

        response = self.get(url, headers=headers, params=params)
        json_output = self.check_login_and_extract_data(response, expected_code=0)

        if json_output and "data" in json_output:
            resv_info_list = json_output["data"]
            return resv_info_list
