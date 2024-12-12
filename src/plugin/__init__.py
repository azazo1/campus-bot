"""
插件加载.
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import traceback
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Callable, Any, Sequence

import toml
from seleniumwire.webdriver import Edge

from src import SRC_DIR_PATH
from src.config import requires_init, project_logger
from src.plugin.config import (PluginConfig, ConfigItem,
                               TextItem, ItemType, DateItem,
                               TimeItem, NumberItem, DatetimeItem)
from src.plugin.context import PluginContext

__all__ = [
    "Routine",
    "ItemType",
    "ConfigItem", "TextItem", "DateItem",
    "TimeItem", "NumberItem", "DatetimeItem",
    "register_plugin",
    "PluginConfig", "Plugin", "PluginContext", "PluginLoader",
]

from src.uia.login import get_login_cache


class Record:

    def __init__(
            self, name: str, plugin_cls,
            plugin_config: Optional[PluginConfig],
            routine: Optional[Routine],
            cache_grabber: Callable[[Edge], Any]
    ):
        self.name = name  # 插件名称.
        self.plugin_cls = plugin_cls
        self.config = plugin_config
        self.routine = routine
        self.instance: Plugin = None  # 类型应为 self.plugin_cls
        self.cache_grabber = cache_grabber
        self.ctx = PluginContext(name)


class Registry:
    __registered_plugins: dict[str, Record] = {}

    @classmethod
    @requires_init
    def add_record(cls, record: Record):
        if not (record.name and all(c.isalpha() or c == "_" for c in record.name)):
            raise ValueError(
                f"Invalid plugin name: "
                f"{repr(record.name)}, "
                f"plugin name must consist of English letters or underscores."
            )
        if record.name in cls.__registered_plugins.keys():
            raise ValueError(f"plugin: {record.name} already registered.")
        record.instance = record.plugin_cls()
        cls.__registered_plugins.update({record.name: record})
        project_logger.info(f"plugin: {record.name} registered.")
        record.instance.on_register(record.ctx)

    @classmethod
    def plugin_record(cls, plugin_name: str):
        return cls.__registered_plugins[plugin_name]

    @classmethod
    def iter_record(cls):
        return iter(cls.__registered_plugins.values())


class Routine(Enum):
    SECONDLY = auto()
    MINUTELY = auto()
    HOURLY = auto()
    DAILY = auto()
    WEEKLY = auto()


@requires_init
def register_plugin(  # 此方法应该在运行之后延迟调用, 也就是说 PluginLoader 先等待项目初始化结束后再加载插件.
        name: str,
        configuration: PluginConfig = None,
        routine: Routine = None,
        ecnu_cache_grabber: Callable[[Edge], Any] | None = None
):
    """
    注册插件, 只有被注册的插件才会可能被加载, 被装饰的类将会注册到 PluginLoader 中准备加载.

    Parameters:
        name: 插件名称, 只能是英文字母和下划线的排列组合, 插件名不能和其他插件重复.
        configuration: 插件需要的配置项集合, 注册后插件可获取项目读取到的对应格式的配置数据.
        routine: 插件期望的回调周期.
        ecnu_cache_grabber: 回调函数, 用于从 WebDriver 中抓取插件需求的 ECNU 登录缓存数据,
                           在 PluginLoader 执行 uia 登录操作时触发, 触发时为已经登录 uia 的状态,
                           函数定义方法见 get_login_cache 函数.

    Example:

    >>> from src.plugin.config import TextItem
    >>> from src.config import init
    >>> init()
    >>> @register_plugin(name="plugin_a",
    ...                  configuration=PluginConfig().add(TextItem("address", "no.9 l street")))
    ... class A(Plugin):
    ...     ...
    """

    def _decorator(cls):
        if not issubclass(cls, Plugin):
            raise ValueError(f"plugin: {cls.__name__} must be a subclass of Plugin.")
        Registry.add_record(Record(name, cls, configuration, routine, ecnu_cache_grabber))
        return lambda cls_: cls_

    return _decorator


class Plugin:
    """
    插件接口定义.

    要实现自己的插件, 需要子类构造函数必须参数列表为空.

    为了保证项目的整洁和规范性, 插件创建文件和记录日志等操作请使用生命周期函数和事件函数中提供的 PluginContext 进行.

    插件编写参见 项目根目录/plugins 下的 demo 和 simple_demo 两个插件.
    """

    def on_load(self, ctx: PluginContext):
        """
        生命周期函数, 插件被加载时触发.
        """

    def on_unload(self, ctx: PluginContext):
        """
        生命周期函数, 插件被卸载时触发.

        可以在此处对 plugin cache 进行最后修改, 修改会保存到硬盘文件中.
        """

    def on_register(self, ctx: PluginContext):
        """
        生命周期函数, 插件成功注册时触发.

        插件成功注册时, 资源基本没有加载好, 但项目已经初始化.
        """

    def on_config_load(self, ctx: PluginContext, cfg: PluginConfig):
        """
        事件函数, 插件的配置被加载时触发(无论插件是否被加载, 此事件都会被触发), 插件需要在此处读取加载的配置.
        最多只会触发一次.
        如果插件配置在注册时指定为 None 则此方法不会被触发, 同理于 on_config_save.

        Parameters:
            ctx: 插件上下文.
            cfg: 插件配置, 和注册时的插件配置不是同一个对象, 但是配置项相同, 且拥有加载得到的值.
                 不过可能由于插件配置未保存过, 无法从文件中加载, 当前值仍然为默认值.
        """

    def on_config_save(self, ctx: PluginContext, cfg: PluginConfig):
        """
        事件函数, 插件的配置被保存时触发, 用户在修改配置然后应用配置的时候触发配置保存操作.
        可被触发多次, 响应此事件以动态应用配置.
        如果插件配置注册时指定为 None, 则此方法不会被触发.

        Parameters:
            ctx: 插件上下文.
            cfg: 插件配置, 修改此处的值不会修改要被保存的配置.
        """

    def on_routine(self, ctx: PluginContext):
        """
        事件函数, 插件注册时指定的 routine 对应的时间到达时触发.

        请不要在此处长时间阻塞, 否则其他插件将无法得到回调.

        此回调方法不是在整点进行回调, 而是间隔时间大于指定时间后的一个时刻进行回调, 不能以此进行计时.

        Note:
            仅被加载的插件能接收到此事件.
        """

    def on_uia_login(self, ctx: PluginContext):
        """
        事件函数, 当 ECNU UIA 成功登录时触发.
        当被触发后, 使用 ctx.get_uia_cache 可以获取登录缓存.

        Note:
            仅被加载的插件能接收到此事件.
        """


class SingleInstanceError(Exception):
    def __init__(self, msg: str = None):
        super().__init__(msg or "can't create single instance twice.")


class TempSysPath:
    """临时修改 sys.path, 以便支持导入"""

    def __init__(self, path: str):
        self.path = os.path.abspath(path)

    def __enter__(self):
        sys.path.append(self.path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.path.remove(self.path)


def _import_module(module_name: str, file_path: str | Path):
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location(module_name, file_path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PluginLoader:
    __IMPORT_PATH = [
        SRC_DIR_PATH.parent / "src" / "plugin" / "intrinsic",  # 内部模块在先.
        SRC_DIR_PATH.parent / "plugins",
    ]
    __IMPORTED_MODULE = {}  # 用于防止二次导入, 不是实例变量, 因为如果 PluginLoader 被销毁重建, 插件不用再注册.
    __CONFIG_FILE_PATH = SRC_DIR_PATH.parent / "plugin_config.toml"
    CONFIG_HEAD_LINE = "# comments will be removed, don't write comments here."
    __PLUGIN_CACHE_PATH = SRC_DIR_PATH.parent / "plugin_cache.json"  # 给插件提供持续化保存内容的文件, cache 持续化内容不保证不会用户删除, 不应保存重要数据.
    __instantiated = False

    def __new__(cls, *args, **kwargs):
        """限制单例, 无法从别处创建实例, 且无法从别处获取实例, 减少数据破坏情况"""
        if cls.__instantiated:
            raise SingleInstanceError()
        obj = super().__new__(cls)
        cls.__instantiated = True
        return obj

    def __init__(self):
        self.cache_valid = False
        self.loaded_plugins: set[str] = set()

    @requires_init
    def import_plugins(self):
        """
        导入并注册插件, 只会导入选定路径下的首层模块, 模块内调用 register_plugin 来注册模块.

        _import_module 不支持模块结构, 如果被导入模块内部如果要导入子模块, 必须使用相对于选定路径的方式来导入.

        被导入的插件不能延迟导入其他模块, 必须在其被导入的时候导入其他所需的模块, 否则可能出现找不到指定模块的错误.
        """
        for path in self.__IMPORT_PATH:
            for s in os.listdir(path):
                s = Path(path, s)
                sub_init = s.joinpath("__init__.py")
                if s.is_dir() and sub_init.exists():
                    n = s.name
                    p = sub_init
                elif s.is_file() and s.suffix == ".py" and s.stem != "__init__":
                    n = s.stem
                    p = s
                else:
                    continue
                if n not in self.__IMPORTED_MODULE.keys():
                    # 不导入重复的模块.
                    with TempSysPath(path):  # 为了插件能导入子模块.
                        self.__IMPORTED_MODULE[n] = _import_module(n, p)
                    project_logger.info(f"module: {n} imported.")
                else:
                    project_logger.info(f"module: "
                                        f"{n} not imported for "
                                        f"its name duplicates with previous one.")

    @classmethod
    def _check_time_reached(cls, now: datetime.datetime,
                            last_routine: datetime.datetime,
                            routine: Routine):
        if routine == Routine.SECONDLY:
            if now - last_routine > datetime.timedelta(seconds=1):
                return True
        elif routine == Routine.MINUTELY:
            if now - last_routine > datetime.timedelta(minutes=1):
                return True
        elif routine == Routine.HOURLY:
            if now - last_routine > datetime.timedelta(hours=1):
                return True
        elif routine == Routine.DAILY:
            if now - last_routine > datetime.timedelta(days=1):
                return True
        elif routine == Routine.WEEKLY:
            if now - last_routine > datetime.timedelta(weeks=1):
                return True
        return False

    def load_config(self):
        project_logger.info("plugin_loader: loading config.")
        if os.path.exists(self.__CONFIG_FILE_PATH):
            with open(self.__CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                serializable = toml.load(f)
        else:
            serializable = {}

        for record in Registry.iter_record():
            if record.config is None:
                continue
            serializable_part = serializable.get(record.name)  # 通过插件名称获取对应的配置部分.
            if serializable_part is not None:
                record.config.from_serializable(serializable_part)
            record.instance.on_config_load(record.ctx, record.config.clone())

    def save_config(self):
        project_logger.info("plugin_loader: saving config.")
        serializable = {}
        for record in Registry.iter_record():
            if record.config is None:
                continue
            serializable[record.name] = record.config.serialize()
            record.instance.on_config_save(record.ctx, record.config.clone())
        with open(self.__CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(self.CONFIG_HEAD_LINE + "\n")
            toml.dump(serializable, f)

    def poll(self):
        """
        轮询调用各个插件.
        """
        now = datetime.datetime.now()
        for plugin_name in self.loaded_plugins:
            record = Registry.plugin_record(plugin_name)
            if self._check_time_reached(now, record.ctx.last_routine(), record.routine):
                record.ctx._plugin_cache._last_routine = now.timestamp()
                try:
                    record.instance.on_routine(record.ctx)
                except Exception:
                    project_logger.error(f"Error when calling {plugin_name} routine:\n"
                                         f"{traceback.format_exc()}")

    def load_all(self, exclude: Sequence[str] = None):
        """
        加载所有插件, 除了排除项, 如果排除项中的插件已经被加载, 则该插件不会被卸载.

        Parameters:
            exclude: 排除项, 默认为空.
        """
        for record in Registry.iter_record():
            if not (exclude and record.name in exclude):
                self.load_plugin(record.name)

    @classmethod
    def _touch_plugin_cache(self):
        if not os.path.exists(self.__PLUGIN_CACHE_PATH):
            with open(self.__PLUGIN_CACHE_PATH, "w", encoding="utf-8") as w:
                w.write("{}")

    def load_plugin(self, plugin_name: str):
        """已经注册的插件需要被加载才能执行 on_routine 等内容, 跳过已经加载的插件"""
        if plugin_name in self.loaded_plugins:
            return
        project_logger.info(f"plugin_loader: loading plugin {plugin_name}.")
        record = Registry.plugin_record(plugin_name)
        self.loaded_plugins.add(plugin_name)
        # 加载 plugin 的 cache, 不是 uia cache.
        self._touch_plugin_cache()
        with open(self.__PLUGIN_CACHE_PATH, "r", encoding="utf-8") as cache_file:
            record.ctx._plugin_cache._load_from(
                json.load(cache_file).get(plugin_name)  # 这里读取了整个插件 cache 文件, todo 选择一个更好的加载方式.
            )

        record.instance.on_load(record.ctx)

    def unload_plugin(self, plugin_name: str):
        """停止插件运行, 可能源自用户意愿和插件加载器停止运行, 如果插件没被加载, 不做任何事"""
        if plugin_name not in self.loaded_plugins:
            return
        project_logger.info(f"plugin_loader: unloading plugin {plugin_name}.")
        record = Registry.plugin_record(plugin_name)
        record.instance.on_unload(record.ctx)
        self.loaded_plugins.remove(plugin_name)
        # 保存 plugin_cache.
        self._touch_plugin_cache()
        with open(self.__PLUGIN_CACHE_PATH, "r", encoding="utf-8") as cache_file:
            obj = json.load(cache_file)
        with open(self.__PLUGIN_CACHE_PATH, "w", encoding="utf-8") as cache_file:
            obj[plugin_name] = record.ctx._plugin_cache._serialize()
            json.dump(obj, cache_file)

    def __del__(self):
        self.__instantiated = False
        self.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        for plugin_name in self.loaded_plugins.copy():
            self.unload_plugin(plugin_name)

    def ecnu_uia_login(self,
                       qrcode_callback: Callable[[str, str, bool], None] = lambda s1, s2, b1: None):
        """
        登录到 UIA, 调用此方法会调出 WebDriver 界面, 引导用户登录 ECNU UIA,
        成功登录后, 各个插件能够获取登录缓存.

        Parameters:
            qrcode_callback: 见 get_login_cache
        """
        grabbers = []
        for plugin_name in self.loaded_plugins:
            record = Registry.plugin_record(plugin_name)
            grabbers.append(record.cache_grabber)
        login_cache = get_login_cache(cache_grabbers=grabbers, qrcode_callback=qrcode_callback)
        for plugin_name in self.loaded_plugins:
            record = Registry.plugin_record(plugin_name)
            record.ctx._uia_cache = login_cache
            record.instance.on_uia_login(record.ctx)
        self.cache_valid = True

    def invalidate_plugin(self):
        self.cache_valid = False
        # todo 安排时间报告 uia cache 失效.
