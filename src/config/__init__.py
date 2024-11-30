import logging
import os
import sys
import warnings
import toml

from src import SRC_DIR

LOG_FILE = "ec-plugin.log"
LOGGER_NAME = "ec-plugin"
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


class MyLogger(logging.Logger):
    def handle(self, record):
        if not _logger_initialized:
            warnings.warn("project logger not initialized.")
        super().handle(record)


logger = MyLogger(LOGGER_NAME)
_logger_initialized = False
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
    global _logger_initialized
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _logger_initialized = True


def init():
    global _initialized
    if _initialized:
        return
    path = os.path.dirname(SRC_DIR)
    os.chdir(path)  # 移动到代码项目目录, 防止异常执行位置导致的错误.
    _init_logger()
    logger.info(f"Change dir to {path}")
    config = _read_config_file()
    _load_email(config)
    _initialized = True
