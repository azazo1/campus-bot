import logging

import toml

CONFIG_FILE = "info.toml"

SMTP_HOST = ""
SMTP_PASS = ""
SMTP_USER = ""
SMTP_FROM = None
SMTP_TO = None

def _read_config_file():
    with open(CONFIG_FILE, 'r', encoding = "utf-8") as f:
        return toml.load(f)

def load_email(config: dict):
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
def init():
    config = _read_config_file()
    logging.basicConfig(filename="output.log", level=logging.INFO, format="%(asctime)s - %(message)s")
    load_email(config)

if __name__ == "__main__":
    init()
