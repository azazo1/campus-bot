import json
from typing import Optional

import requests
from requests import Response

from .date import Day, TimePeriod
from .login import LoginCache


class LoginError(Exception):
    """登录缓存失效时触发."""

    def __init__(self, msg: str = ""):
        super().__init__(msg)


class QuickSelect:
    """
    表示 quickSelect 请求返回的 json 中的 data 字段.
    包含可选 预约日期(day), 校区(premises), 楼层(storey), 区域(area) 的速览信息.
    """

    def __init__(self, data: dict):
        self.date = data['date']

        # 一下每个分类中的每个对象都有唯一的 id.
        self.storage = {}  # 用于快速检索 id 对应的对象.
        self.premises = []  # type: list[int]
        for premises in data['premises']:
            id_ = int(premises['id'])
            premises["id"] = id_
            premises["type"] = 0  # 标记其是校区.
            self.storage[id_] = premises
            self.premises.append(id_)
        self.storeys = []  # type: list[int]
        for storey in data['storey']:
            id_ = int(storey['id'])
            storey["id"] = id_
            storey["type"] = 1
            self.storage[id_] = storey
            self.storeys.append(id_)
        self.areas = []  # type: list[int]
        for area in data['area']:
            id_ = int(area["id"])
            area["id"] = id_
            area["type"] = 2
            self.storage[id_] = area
            self.areas.append(id_)

    def get_premises_of(self, id_: int) -> int:
        """
        返回一个 id 所述的校区.

        Returns:
            0: 普陀校区.
            1: 闵行校区.
            -1: id 参数无效, 或者在网站未来的变更导致校区名称改变.
        """
        obj = self.get_by_id(id_)
        if obj is None:
            return -1
        while int(obj["parentId"]) != 0:
            obj = self.get_by_id(int(obj["parentId"]))
        if obj is None:
            return -1
        if obj["name"] == "普陀校区":
            return 0
        elif obj["name"] == "闵行校区":
            return 1
        return -1

    def get_by_id(self, id_: int) -> Optional[dict]:
        """
        获取 id 对应的对象.

        Returns:
            - 如果 id 存在, 返回对应的字典对象.
            - 如果 id 不存在, 返回 None.
        """
        return self.storage.get(id_)

    def get_free_seats_num(self):
        """
        获取可预约座位的总数.
        """
        sum_ = 0
        for area_id in self.areas:
            sum_ += int(self.get_by_id(area_id)["free_num"])
        return sum_

    def get_most_free_seats_area(self):
        """
        获取拥有最多空闲座位的区域.

        Returns:
            - 返回空闲座位最多的区域的 id.
        """
        max_num = 0
        max_id = -1
        for area_id in self.areas:
            n = self.get_by_id(area_id)["free_num"]
            if n > max_num:
                max_num = n
                max_id = area_id
        return max_id


class LibraryQuery:
    def __init__(self, cache: LoginCache):
        self.cache = cache

    def _post(self, url: str, headers: dict = None, payload: dict = None):
        """
        提交 POST 请求并自动附加以下内容:

        headers:
            Authorization: ...
            Content-Type: application/json

        cookies: ...

        payload(json): {
            "authorization": ...,
        }
        """
        headers_ = {"Authorization": self.cache.authorization, "Content-Type": "application/json"}
        if headers is not None:
            headers_.update(headers)
        data_ = {'authorization': self.cache.authorization}
        if payload is not None:
            data_.update(payload)
        return requests.post(
            url,
            headers=headers_,
            json=payload,  # 这里不能选择 data 的形参, 因为 data 形参对应的是 x-www-form-urlencodeed.
            cookies=self.cache.cookies,
        )

    def _get(self, url: str):
        return requests.get(
            url,
            headers={"Authorization": self.cache.authorization},
            cookies=self.cache.cookies,
        )

    @classmethod
    def check_login_and_extract_data(cls, response: Response,
                                     expected_code: int = 0) -> dict | list:
        if response.status_code != 200:
            raise LoginError(f"response status code: {response.status_code}.")
        if "json" not in response.headers["content-type"]:
            raise LoginError("request was redirected, which means you didn't login.")
        ret = json.loads(response.text)
        if ret["code"] != expected_code:
            raise LoginError(f"result code: {ret['code']}, {ret}.")
        rst = ret.get("data")
        assert rst is not None, "error in response, no data."
        return rst

    def quick_select(self) -> QuickSelect:
        """
        查询各个区域的座位空闲情况, 相当于 quickSelect 请求.

        url: https://seat-lib.ecnu.edu.cn/reserve/index/quickSelect

        method: POST

        payload(json): {
          "id": "[int]", // 未知作用, 同义: reserveType, 始终为 "1".
          "members": [int], // 未知作用, 始终为 0.

          // 以下为已发现的可选部分, 用于筛选空闲座位.
          "date": "[%Y-%m-%d]", // 要预约的日期.
          "categoryIds": [ // 座位类型.
            "1" // "1" 表示 `普通座位`.
          ],
          "storeyIds": [ // 楼层的 id.
            "2", ...
          ],
          "premisesIds": [ // 校区 id.
            "1" //
          ],
          "noiseId": "..." // 座位噪声水平.
        }

        Returns:
            - 如果请求成功, 返回 QuickSelect 对象.
            - 如果出现了登录信息失效.
        """
        response = self._post(
            "https://seat-lib.ecnu.edu.cn/reserve/index/quickSelect",
            payload={"id": "1", "members": 0}
        )
        return QuickSelect(self.check_login_and_extract_data(response))

    def query_seats(self, area_id: int, time_period: TimePeriod):
        """
        查询一个区域可用的座位具体情况.

        会返回座位的位置分布信息.

        Parameters:
            area_id(int): 要查询的区域在 QuickSelect 中的 id 值.
            time_period(TimePeriod): 要查询的日期和时间段.

        url: https://seat-lib.ecnu.edu.cn/api/Seat/seat

        payload(json): {
          "area": "[int]", // 区域的 id.
          "segment": "[int]", // 时间段 Time 对象的 id.
          "day": "[%Y-%m-%d]", // 从可选日期中选择的日期.
          "startTime": "[%H:%M]", // 从可选时间段中选取的开始时间.
          "endTime": "[%H:%M]", // 从可选时间段中选取的结束时间.
        }
        """
        response = self._post("https://seat-lib.ecnu.edu.cn/api/Seat/seat",
                              payload={"area": area_id,
                                       "segment": time_period["id"],
                                       "day": time_period.day["day"],
                                       "startTime": time_period["start"],
                                       "endTime": time_period["end"], })
        ret_data = self.check_login_and_extract_data(response, expected_code=1)
        return ret_data

    def query_date(self, id_: int) -> list[Day]:
        """
        查询某个区域可用的预约时间.

        Parameters:
            id_(int): 要查询的区域在 QuickSelect 中的 id 值.

        url: https://seat-lib.ecnu.edu.cn/api/Seat/date

        payload(json): {
          "build_id": "[int]",
        }
        """
        response = self._post(
            "https://seat-lib.ecnu.edu.cn/api/Seat/date",
            payload={"build_id": f"{id_}"}
        )
        ret_data = self.check_login_and_extract_data(
            response,
            expected_code=1
        )
        return Day.from_response(ret_data)

    # detail, map 请求没有适配, 暂时认为需求不大.
