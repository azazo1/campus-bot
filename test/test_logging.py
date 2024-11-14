"""
测试日志功能.
"""
from src.config import init, logger


def main():
    init()
    logger.info("Hello World")
    logger.debug("Hello World Debug")
    logger.error("Hello World Error")


if __name__ == '__main__':
    main()
