import json
import time
from typing import Optional

import requests

from .login import LoginCache


class Area:
    """
    表示 quickSelect 请求返回的 json 中的 data 字段.
    包含可选 预约日期, 校区, 楼层, 区域 的速览信息.
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

    def _post(self, url: str, headers: dict = None, data: dict = None):
        headers_ = {"Authorization": self.cache.authorization}
        if headers is not None:
            headers_.update(headers)
        return requests.post(
            url,
            headers=headers_,
            json=data or {},  # 这里不能选择 data 的形参, 因为 data 形参对应的是 x-www-form-urlencodeed.
            cookies=self.cache.cookies,
        )

    def _get(self, url: str):
        return requests.get(
            url,
            headers={"Authorization": self.cache.authorization},
            cookies=self.cache.cookies,
        )

    def query_area(self) -> Area:
        """
        查询各个区域的座位空闲情况, 相当于 quickSelect 请求.

        url: https://seat-lib.ecnu.edu.cn/reserve/index/quickSelect

        method: POST

        headers:
          Authorization: ...
          Content-Type: application/json

        cookies: ...

        payload(json): {
          "id": "[int]", // 未知作用, 同义: reserveType, 始终为 "1".
          "date": "[%Y-%m-%d]", // 要预约的日期, 影响 response 中空闲的位置数量.
          "members": [int], // 未知作用, 始终为 0.
          "authorization": "..."

          // 以下为已发现的可选部分, 用于筛选空闲座位.
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

        response(json):
            返回 json 对象, 包含可以预约的时间(date), 校区(premises), 楼层(storey), 每层的区域(area), 见.
        """
        now = time.localtime()
        ret_data = json.loads(self._post(
            "https://seat-lib.ecnu.edu.cn/reserve/index/quickSelect",
            headers={"Content-Type": "application/json"},
            data={
                "id": "1",
                "date": f"{now.tm_year}-{now.tm_mon:02d}-{now.tm_mday:02d}",
                "members": 0,
                "authorization": self.cache.authorization
            }).text).get("data")
        return Area(ret_data)

    def query_seat(self):
        """
        查询某个楼层中一个区域可用的座位具体情况.

        会返回座位的位置分布信息.

        url: https://seat-lib.ecnu.edu.cn/api/Seat/seat

        headers: Authorization: ...

        cookies: ...

        payload(json): {
          "area": "[int]",
          "segment": "[int]",
          "day": "[%Y-%m-%d]",
          "startTime": "[%H:%M]",
          "endTime": "[%H:%M]",
          "authorization": "..."
        }
        """
        pass

    def query_date(self):
        """
        查询可用的预约时间.

        url: https://seat-lib.ecnu.edu.cn/api/Seat/date

        headers: Authorization: ...

        cookies: ...

        payload(json): {
          "build_id": "[int]",
          "authorization": "..."
        }
        """
