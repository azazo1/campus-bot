import logging
import sys
from typing import Optional

import toml

LOG_FILE = "ec-plugin.log"
CONFIG_FILE = "configuration.toml"

SMTP_HOST = ""
SMTP_PASS = ""
SMTP_USER = ""
SMTP_FROM = None
SMTP_TO = None

logger: Optional[logging.Logger] = None


def _read_config_file() -> dict:
    with open(CONFIG_FILE, 'r', encoding="utf-8") as f:
        return toml.load(f)


def _load_email(config: dict):
    '''
    # Example

    ```toml
    # configuration.toml
    [smtp]
    host = "smtp.qq.com" # smtp server
    pass = "password" # SMTP 服务器的 Token
    user = "sender_email @ qq.com" # 用来发邮件的邮箱
    from = ["name", "email"] # 发件人的名字和邮箱
    to = ["name", "email"] # 收件人的名字和邮箱
    ```

    '''
    global SMTP_HOST, SMTP_PASS, SMTP_USER, SMTP_FROM, SMTP_TO
    SMTP_HOST = config["smtp"]["host"]
    SMTP_PASS = config["smtp"]["pass"]
    SMTP_USER = config["smtp"]["user"]
    SMTP_FROM = (config["smtp"]["from"][0], config["smtp"]["from"][1])
    SMTP_TO = (config["smtp"]["to"][0], config["smtp"]["to"][1])
    logger.info((SMTP_HOST, SMTP_PASS, SMTP_USER, SMTP_FROM, SMTP_TO))


def _init_logger():
    global logger
    logger = logging.Logger("ec-plugin")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def init():
    _init_logger()
    config = _read_config_file()
    _load_email(config)
