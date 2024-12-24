import datetime
import os
import pathlib
from typing import Callable

__all__ = [
    "SRC_DIR_PATH", "SRC_DIR", "Throttler"
]
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR_PATH = pathlib.Path(SRC_DIR)


class Throttler:
    def __init__(self, interval_time: datetime.timedelta):
        self.interval_time = interval_time
        self.last_time = datetime.datetime.fromtimestamp(0)

    def throttle(self, func: Callable, *args, **kwargs):
        now = datetime.datetime.now()
        rst = None
        if now - self.last_time > self.interval_time:
            rst = func(*args, **kwargs)
            self.last_time = now
        return rst
