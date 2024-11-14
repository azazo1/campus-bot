"""
座位对象表示, 见 query_seats_example.json 文件.
"""
from typing import Self


class Seat:
    """
    部分字段介绍:
    status:
        - 1: 空闲.
        - 2: 已预约.
        - 其他暂时未统计, 可以看作只有 1 表示空闲.
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
