"""
图书馆座位预约.

https://seat-lib.ecnu.edu.cn/api/index/subscribe 查询预约.
https://seat-lib.ecnu.edu.cn/api/Seat/confirm 执行预约操作, 此操作涉及加密, 见 assets/confirm_subscribe.js.
"""
from __future__ import annotations

from src.library.date import TimePeriod
from src.uia.login import LoginCache
from . import Request
from .encrypt import Encryptor


class Subscribe(Request):
    def __init__(self, cache: LoginCache):
        super().__init__(cache)

    def confirm_subscribe(self, seat_id: int, time_period: TimePeriod):
        """
        预约图书馆座位.

        url: https://seat-lib.ecnu.edu.cn/api/Seat/confirm

        method: POST

        payload(json): {
            "aesjson": "..." # 使用 Encryptor.encrypt 加密的 json 数据.
        }

        其中被加密的 json 数据原格式为:

        {
            "seat_id": "[int]", // 座位 id.
            "segment": "[int]" // 时间段 id.
        }

        response(json): {
            "code": int, // 1 表示成功.
            "msg": "预约成功/...",
            "time": "%H:%M-%H:%M",
            "seat": "...", // 座位全称字符串.
            "new_time": "%Y-%m-%d %H:%M-%H:%M",
            "area": "...", // 区域全程字符串.
            "no": "[int]" // 座位字符串.
        }
        """
        response = self.post(
            "https://seat-lib.ecnu.edu.cn/api/Seat/confirm",
            payload={"aesjson": Encryptor.encrypt({
                "seat_id": seat_id,
                "segment": f"{time_period.id}",
            })}
        )
        return self.check_login_and_extract_data(response, 1)
