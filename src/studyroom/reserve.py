from typing import Optional, List

from src.studyroom import StudyRoomCache
from src.studyroom import Request, LoginError


class StudyRoomReserve(Request):
    """针对 StudyRoom 的请求类，继承自独立的 Request 类，扩展一些 StudyRoom 相关的功能。"""

    def __init__(self, cache: StudyRoomCache):
        super().__init__(cache)

    def reserve_room(self, payload: dict) -> dict:
        """
        封装预约研修间的 POST 请求。

        Parameters:
            payload: dict, 包含预约信息的数据，如时间、房间号等。

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
            'Cookie': f"ic-cookie={ic_cookie}",
        }

        response = self.post(url, json_payload=payload, headers=headers)
        return response.json()

    def cancel_reservation(self, reservation_id: int) -> None:
        """
        取消特定的研修间预约。

        Parameters:
            reservation_id: int, 需要取消的预约 ID.

        url: https://studyroom.ecnu.edu.cn/

        Returns:
            None. 如果没有抛出异常，则表示取消成功。
        """
        pass
        #
        # url = "https://studyroom.ecnu.edu.cn/ic-web/cancel"
        # payload = {"id": reservation_id}
        # response = self.post(url, json_payload=payload)
        # self.check_login_and_extract_data(response, expected_code=1)
