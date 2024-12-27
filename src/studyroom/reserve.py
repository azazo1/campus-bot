from typing import Optional, List

from src.studyroom import StudyRoomCache
from src.studyroom import Request, LoginError


class StudyRoomReserve(Request):
    """针对 StudyRoom 的请求类，继承自独立的 Request 类，扩展一些 StudyRoom 相关的功能。"""

    def __init__(self, cache: StudyRoomCache):
        super().__init__(cache)

    def _fetch_userInfo(self) -> Optional[dict]:
        """
        获取用户的基本信息, 最主要的是从该 url 中提取 accNo, 在预约和取消预约时会用到.
        提交 POST 请求时传入的 appAccNo 参数从此获取.

        url: https://studyroom.ecnu.edu.cn/ic-web/auth/userInfo

        Returns:
            dict, 包含用户信息的数据。
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
                "uuid": user_data.get("uuid"),  # 用户 ID, 在 query 时会查到
                "pid": user_data.get("pid"),  # pid = 学号
                "trueName": user_data.get("trueName"),  # 真实姓名
                "className": user_data.get("className"),  # 学院名字
                "token": user_data.get("token"),  # 暂时不知道用来干嘛, 可能有用
                "accNo": user_data.get("accNo"),  # 用来发送 Reserve 和 Cancel 请求
            }
            return extracted_data

    def reserve_room(
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
            appAccNo: int, 用户账号 ID。
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

        # 获取用户 accNo, 用于发送 POST 请求
        user_info = self._fetch_userInfo()
        if not user_info:
            raise LoginError("Failed to fetch user information.")
        appAccNo = user_info.get("accNo")

        # 构造请求的 payload
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

        # 发送 POST 请求
        response = self.post(url, json_payload=payload, headers=headers)
        return response.json()

    def cancel_reservation(self) -> None:
        """
        取消特定的研修间预约。
        # Fixme 取消预约的接口需要传递 uuid 参数, 通过 _fetch_userInfo 获取.
        Parameters:
            uuid: int, 需要取消的预约 ID.

        url: https://studyroom.ecnu.edu.cn/ic-web/reserve/delete
        """
        pass

    def check_is_used(self):
        """
        通过该接口可以查询研修室是否正在使用中, 用于检查签到状态.
        # Todo 考虑后期检验在 29 分钟未签到时自动取消预约.

        示例 url: https://studyroom.ecnu.edu.cn/ic-web/reserve/resvInfo?beginDate=2024-12-23&endDate=2024-12-29&needStatus=6&page=1&pageNum=10&orderKey=gmt_create&orderModel=desc

        Tips:
            resvStatus: 1093 代表正在使用中, 1027 代表已预约但未使用.
        """
        pass
