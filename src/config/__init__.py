import logging
import os
import sys
import warnings
from logging import Logger
from typing import Optional

import toml

from src import SRC_DIR

LOG_FILE = "ec-plugin.log"
CONFIG_FILE = "configuration.toml"

SMTP_HOST = ""
SMTP_PASS = ""
SMTP_USER = ""
SMTP_FROM = []
SMTP_TO = []


def requires_init(f):
    """
    标记 依赖项目初始化 的函数的装饰器.

    例如在每个需要使用 logger 的函数前添加 `@require_init`
    """

    def wrapper(*args, **kwargs):
        if not _initialized:
            warnings.warn("the project has not been initialized.")
        return f(*args, **kwargs)

    return wrapper


class WrapLogger:
    """Logger 包装类, 和 Logger 类方法相同, 只不过可以有未初始化状态, 解决提前导入的 logger 变量为 None 的情况."""

    def __init__(self):
        self._logger: Optional[Logger] = None

    def wrap(self, l: Logger):
        self._logger = l

    @requires_init
    def __getattr__(self, item):
        # getattribute 魔法方法在任何时候都会触发, 而不是找不到时才触发.
        return self._logger.__getattribute__(item)


logger = WrapLogger()
_initialized = False


def _read_config_file() -> dict:
    with open(CONFIG_FILE, 'r', encoding="utf-8") as f:
        return toml.load(f)


def _load_email(config: dict):
    """
    # Example

    ```toml
    # configuration.toml
    [smtp]
    host = "smtp.qq.com" # smtp server
    pass = "password" # SMTP 服务器的 Token
    user = "sender_email @ qq.com" # 用来发邮件的邮箱
    to = ["name", "email"] # 收件人的名字和邮箱
    ```
    """
    global SMTP_HOST, SMTP_PASS, SMTP_USER, SMTP_FROM, SMTP_TO
    SMTP_HOST = config["smtp"]["host"]
    SMTP_PASS = config["smtp"]["pass"]
    SMTP_USER = config["smtp"]["user"]
    SMTP_FROM = (SMTP_USER.split("@", 1)[0], SMTP_USER)
    to_ = config["smtp"]["to"]
    SMTP_TO = (to_.split("@", 1)[0], to_)


def _init_logger():
    logger_ = logging.Logger("ec-plugin")
    logger_.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger_.addHandler(stream_handler)

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.WARN)
    file_handler.setFormatter(formatter)
    logger_.addHandler(file_handler)

    logger.wrap(logger_)


def init():
    global _initialized
    _init_logger()
    path = os.path.dirname(SRC_DIR)
    os.chdir(path)  # 移动到代码项目目录, 防止异常执行位置导致的错误.
    logging.info(f"Change dir to {path}")  # 使用 logging 防止触发 warning.
    config = _read_config_file()
    _load_email(config)
    _initialized = True
