from __future__ import annotations

import datetime
import json
import logging
from copy import deepcopy
from pathlib import Path

from src import SRC_DIR_PATH
from src.config import project_logger
from src.uia.login import LoginCache


def is_json_serializable(obj):
    if isinstance(obj, (str, int, float, bool, type(None))):
        return True
    elif isinstance(obj, (list, tuple)):
        return all(is_json_serializable(item) for item in obj)
    elif isinstance(obj, dict):
        return all(
            isinstance(key, str) and is_json_serializable(value) for key, value in obj.items())
    return False


class PluginCache:
    """插件持久化保存数据存储对象, 只能存放 json 可序列化对象"""
    __OBJ = object()

    def __init__(self, name: str):
        self.__dic = {}
        self.__name = name
        self._last_routine = 0  # 上一次 routine 执行的时间, (s).

    def _check_serializable(self, obj=__OBJ):
        if obj == self.__OBJ:
            obj = self.__dic
        if not is_json_serializable(obj):
            raise ValueError("Cache object can only accept json serializable object.")

    def _load_from(self, json_obj):
        """从可序列化对象中恢复, 可以为 None, 此时使用默认的 Cache, 即原 Cache 被删除或者第一次创建 Cache"""
        if json_obj is None:
            return
        self._check_serializable(json_obj)
        if json_obj['name'] != self.__name:
            raise ValueError("Incorrect plugin name.")
        self._last_routine = json_obj['last_routine']
        self.__dic.update(json_obj['cache'])

    def _serialize(self):
        return deepcopy({
            'name': self.__name,
            'last_routine': self._last_routine,
            'cache': self.__dic
        })

    def get(self, item):
        """获取 cache 内容的一个副本, 在返回值中进行数据修改不会反应到持久化保存内容中"""
        return deepcopy(self.__dic[item])

    def set(self, key, value):
        """在此处设置需要持久化的内容, 仅支持可 json 化的对象"""
        self._check_serializable(key)
        self._check_serializable(value)
        self.__dic[key] = value

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        self.set(key, value)


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
        self._logger.addHandler(ForwardLoggerHandler(project_logger))
        self._uia_cache: LoginCache | None = None
        self._plugin_cache = PluginCache(self.__name)  # 插件持久化保存数据的位置, 同时也是存放 routine 状态的位置.

    def last_routine(self):
        return datetime.datetime.fromtimestamp(self._plugin_cache._last_routine)

    def get_cache(self) -> PluginCache:
        """
        获取插件自身的 cache, 插件 cache 会在插件被加载时被加载, 在插件被 unload 的时候持久化保存.

        插件可以在 on_load 触发及其之后获取有效的 cache.

        插件自身的 cache 用于插件持久化保存数据, 但是 cache 中保存的数据有可能被用户清除数据.
        """
        return self._plugin_cache

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
        需要本地机器登陆过 ECNU 后才能获取有效缓存,
        在那之前调用此方法会返回 None.
        """
        return self._uia_cache
