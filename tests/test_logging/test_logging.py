"""
测试日志功能.
"""
from src.log import init, project_logger


def main():
    init()
    project_logger.info("Hello World")
    project_logger.debug("Hello World Debug")
    project_logger.error("Hello World Error")


if __name__ == '__main__':
    main()
