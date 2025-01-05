from typing import Optional

from src.studyroom.req import StudyRoomCache
from src.studyroom.req import Request, LoginError
from src.studyroom.query import StudyRoomQuery


class StudyRoomReserve(Request):
    """针对 StudyRoom 的请求类，继承自独立的 Request 类，扩展一些 StudyRoom 相关的功能。"""

    def __init__(self, cache: StudyRoomCache):
        super().__init__(cache)

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
