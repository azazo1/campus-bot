import json
import time
import requests

from .login import LoginCache


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

    def query_area(self):
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
        return json.loads(self._post(
            "https://seat-lib.ecnu.edu.cn/reserve/index/quickSelect",
            headers={"Content-Type": "application/json"},
            data={
                "id": "1",
                "date": f"{now.tm_year}-{now.tm_mon:02d}-{now.tm_mday:02d}",
                "members": 0,
                "authorization": self.cache.authorization
            }).text).get("data")

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
