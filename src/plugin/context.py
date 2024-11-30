from __future__ import annotations

import logging
from pathlib import Path

from src import SRC_DIR_PATH
from src.config import logger
from src.uia.login import LoginCache


class ForwardLoggerHandler(logging.Handler):
    def __init__(self, target_logger: logging.Logger, level: int | str = logging.NOTSET):
        super().__init__(level)
        self.target = target_logger

    def emit(self, record):
        self.target.handle(record)


class PluginContext:
    def __init__(self, name: str):
        self.__name = name  # 插件名称.
        self._logger = logging.Logger(f"plugin-{self.__name}")
        self._logger.addHandler(ForwardLoggerHandler(logger))

    def get_plugin_dir(self) -> Path:
        """
        获取插件自身用于保存数据的文件夹, 获取时自动创建文件夹, 无需手动创建.

        插件不应在此处保存配置文件, 因为这样不利于用户感知和设置这些配置.
        """
        p = SRC_DIR_PATH.parent / "plugin_dir" / self.__name
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_logger(self):
        """获取插件专属的 logger"""
        return self._logger

    def get_uia_cache(self) -> LoginCache:
        """
        获取 ECNU 统一登陆的登录缓存,
        需要本地机器登陆过 ECNU 后才能获取有效缓存.
        """
        # todo
