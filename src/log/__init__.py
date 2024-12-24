import logging
import os
import sys
import warnings

from src import SRC_DIR

LOG_FILE = "ec-plugin.log"
LOGGER_NAME = "ec-plugin"


def requires_init(f):
    """
    标记 依赖项目初始化 的函数的装饰器.

    例如:
    - 在每个需要使用 logger 的函数前添加 `@require_init`.
    - 在需要当前运行目录变化到项目根目录后才能执行的操作前添加 `@require_init`.
    """

    def wrapper(*args, **kwargs):
        if not _initialized:
            warnings.warn("the project has not been initialized.")
        return f(*args, **kwargs)

    return wrapper


class MyLogger(logging.Logger):
    def handle(self, record):
        if not _logger_initialized:
            warnings.warn("project logger not initialized.")
        super().handle(record)


project_logger = MyLogger(LOGGER_NAME)
_logger_initialized = False
_initialized = False


def _init_logger():
    global _logger_initialized
    project_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    project_logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    project_logger.addHandler(file_handler)

    _logger_initialized = True


def init():
    global _initialized
    if _initialized:
        return
    path = os.path.dirname(SRC_DIR)
    os.chdir(path)  # 移动到代码项目目录, 防止异常执行位置导致的错误.
    _init_logger()
    project_logger.info(f"Change dir to {path}")
    _initialized = True
