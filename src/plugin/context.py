from __future__ import annotations

import datetime
import logging
from copy import deepcopy
from pathlib import Path
from typing import Callable

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
    """
    插件持久化保存数据存储对象, 只能存放 json 可序列化对象,
    可以把 PluginCache 看成一个`映射`数据结构,
    但是只允许特定的写入方法对数据进行修改.
    """
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
        """在此处写入需要持久化的内容, value 仅支持可 json 化的对象, key 只支持字符串"""
        if not isinstance(key, str):
            raise TypeError("key must be a string.")
        self._check_serializable(key)
        self._check_serializable(value)
        self.__dic[key] = value

    def remove(self, key):
        """从 cache 中移除 key 的数据, 如果 key 不在 cache 中, 不会发生任何事"""
        if key in self.__dic:
            del self.__dic[key]

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        self.remove(key)


class ForwardLoggerHandler(logging.Handler):
    def __init__(self, target_logger: logging.Logger, level: int | str = logging.NOTSET):
        super().__init__(level)
        self.target = target_logger

    def emit(self, record):
        self.target.handle(record)


class PluginContext:

    def __init__(self, name: str):
        self.__name = name  # 插件名称.
        self.__logger = logging.Logger(f"plugin-{self.__name}")
        self.__logger.addHandler(ForwardLoggerHandler(project_logger))
        self._uia_cache: LoginCache | None = None
        self._plugin_cache = PluginCache(self.__name)  # 插件持久化保存数据的位置, 同时也是存放 routine 状态的位置.
        self._report_cache_invalid: Callable[[], None] = lambda: None

    def last_routine(self):
        return datetime.datetime.fromtimestamp(self._plugin_cache._last_routine)

    def report_cache_invalid(self):
        """
        插件发现 uia cache 失效的时候, 可以通过此函数报告 PluginLoader,
        PluginLoader 对新的 UIA 登录会话进行安排.
        最后再次触发 on_uia_login 事件.

        只有被加载的插件 (on_load 调用开始及之后, on_unload 调用结束之前) 使用此方法报告 uia cache 失效才有作用.
        """
        self._report_cache_invalid()

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
        return self.__logger

    def get_uia_cache(self) -> LoginCache:
        """
        获取 ECNU 统一登陆的登录缓存,
        需要本地机器登陆过 ECNU 后才能获取有效缓存,
        在那之前调用此方法会返回 None.
        """
        return self._uia_cache
