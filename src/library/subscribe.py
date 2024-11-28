"""
图书馆座位预约.

https://seat-lib.ecnu.edu.cn/api/index/subscribe 查询预约.
https://seat-lib.ecnu.edu.cn/api/Seat/confirm 执行预约操作, 此操作涉及加密, 见 assets/confirm_subscribe.js.
"""
from src.uia.login import LoginCache


class Subscribe:
    def __init__(self, cache: LoginCache):
        self.cache = cache
