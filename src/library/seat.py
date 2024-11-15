"""
座位对象表示, 见 query_seats_example.json 文件.
"""
from functools import reduce
from typing import Self

from src.config import requires_init, logger


class Seat:
    """
    部分字段介绍:
    status:
        - 1: 空闲.
        - 2: 已预约.
        - 其他暂时未统计, 可以看作只有 1 表示空闲.

    x, y, width, height:
        原 js 代码对其的处理是:
        ```javascript
        left: Math.round(a.point_x * l / 100 * e.ratio) + "px",
        top: Math.round(a.point_y * t / 100 * e.ratio) + "px",
        width: Math.round(a.width * l / 100 * e.ratio) + "px",
        height: Math.round(a.height * t / 100 * e.ratio) + "px",
        ```
        这四个属性表示的就是座位在座位图上的百分比坐标.
    """

    def __init__(self, json_data: dict):
        self.raw = json_data

        self.id = int(self.raw['id'])
        self.area_id = int(self.raw['area'])  # 座位所属区域在 QuickSelect 中的 id.
        self.no = self.raw['no']  # 面向用户的序列号 e.g. "001"/"002"/...
        self.status = int(self.raw['status'])  # 状态

        # 此座位在座位图中的位置.
        self.x = float(self.raw['point_x'])
        self.y = float(self.raw['point_y'])
        self.width = float(self.raw['width'])
        self.height = float(self.raw['height'])

    @classmethod
    def from_response(cls, json_data: list[dict]) -> list[Self]:
        """
        从 seat 请求的响应中解析多个 Seat.
        """
        seats = []
        for obj in json_data:
            seats.append(Seat(obj))
        return seats

    def __repr__(self):
        return repr(self.raw)

    def __getitem__(self, item):
        return self.raw[item]


class SeatFinder:
    """
    用于筛选特定要求下最符合要求的座位.
    """

    def __init__(self, seats: list[Seat]):
        """
        Parameters:
            seats(list[Seat]): 图书馆中一个区域内的座位.
        """
        self.seats = seats
        self._check_seats()

    @requires_init
    def _check_seats(self):
        """
        检查自身的座位是否都是来自图书馆同一区域.
        """
        area_id = None
        for seat in self.seats:
            if area_id is None:
                area_id = seat.area_id
            elif area_id != seat.area_id:
                logger.warn("seat-finder: seats are not from the same area.")
                return

    def find_most_isolated(self) -> Seat:
        """
        寻找周围空闲数量最多的座位.
        """
        