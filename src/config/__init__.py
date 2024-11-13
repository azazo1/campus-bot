import logging
import sys

import toml

LOG_FILE = "ec-plugin.log"
CONFIG_FILE = "info.toml"

SMTP_HOST = ""
SMTP_PASS = ""
SMTP_USER = ""
SMTP_FROM = None
SMTP_TO = None

logger = None


def _read_config_file():
    with open(CONFIG_FILE, 'r', encoding="utf-8") as f:
        return toml.load(f)


def _load_email(config: dict):
    global SMTP_HOST
    global SMTP_PASS
    global SMTP_USER
    global SMTP_FROM
    global SMTP_TO
    # 访问配置数据
    SMTP_HOST = config["smtp"]["host"]
    SMTP_PASS = config["smtp"]["pass"]
    SMTP_USER = config["smtp"]["user"]
    SMTP_FROM = (config["smtp"]["from"][0], config["smtp"]["from"][1])
    SMTP_TO = (config["smtp"]["to"][0], config["smtp"]["to"][1])
    logging.info((SMTP_HOST, SMTP_PASS, SMTP_USER, SMTP_FROM, SMTP_TO))


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


if __name__ == "__main__":
    init()
