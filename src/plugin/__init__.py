"""
插件加载.
"""
from __future__ import annotations

import os
import sys
from enum import Enum, auto
from pathlib import Path
from typing import Optional

from src import SRC_DIR_PATH
from src.config import requires_init, logger
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


class Registry:
    def __init__(
            self, name: str, plugin_cls,
            plugin_config: Optional[PluginConfig],
            routine: Optional[Routine]
    ):
        self.name = name
        self.plugin_cls = plugin_cls
        self.config = plugin_config
        self.routine = routine
        self.instance = None  # 类型应为 self.plugin_cls
        self.ctx = PluginContext(name)


class Register:
    __registered_plugins: dict[str, Registry] = {}

    @classmethod
    @requires_init
    def add_registry(cls, registry: Registry):
        if registry.name in cls.__registered_plugins.keys():
            raise ValueError(f"plugin: {registry.name} already registered.")
        registry.instance = registry.plugin_cls()
        registry.instance.on_register(registry.ctx)
        cls.__registered_plugins.update({registry.name: registry})
        logger.info(f"plugin: {registry.name} registered.")


class Routine(Enum):
    MINUTELY = auto()
    HOURLY = auto()
    DAILY = auto()
    WEEKLY = auto()


@requires_init
def register_plugin(  # 此方法应该在运行之后延迟调用, 也就是说 PluginLoader 先等待项目初始化结束后再加载插件.
        name: str,
        configuration: PluginConfig = None,
        routine: Routine = None,
):
    """
    注册插件, 只有被注册的插件才会被加载.

    被装饰的类将会注册到 PluginLoader 中准备加载.

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
        Register.add_registry(Registry(name, cls, configuration, routine))
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
        pass

    def on_unload(self, ctx: PluginContext):
        """
        生命周期函数, 插件被卸载时触发.
        """
        pass

    def on_register(self, ctx: PluginContext):
        """
        生命周期函数, 插件成功注册时触发.

        插件成功注册时, 资源基本没有加载好, 但项目已经初始化.
        """

    def on_config_load(self, ctx: PluginContext, cfg: PluginConfig):
        """
        事件函数, 插件的配置被加载时触发, 插件需要在此处读取加载的配置.

        Parameters:
            ctx: 插件上下文.
            cfg: 插件配置, 和注册时的插件配置不是同一个对象, 但是配置项相同,
                 且拥有加载得到的值.
        """

    def on_config_save(self, ctx: PluginContext, cfg: PluginConfig):
        """
        事件函数, 插件的配置被保存时触发.

        Parameters:
            ctx: 插件上下文.
            cfg: 插件配置, 修改此处的值不会修改要被保存的配置.
        """

    def on_routine(self, ctx: PluginContext):
        """
        事件函数, 插件注册时指定的 routine 对应的时间到达时触发.
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
    IMPORT_PATH = [
        SRC_DIR_PATH.parent / "src" / "plugin" / "intrinsic",  # 内部模块在先.
        SRC_DIR_PATH.parent / "plugins",
    ]
    IMPORTED_MODULE = {}
    __instantiated = False

    def __new__(cls, *args, **kwargs):
        """限制单例, 无法从别处创建实例, 且无法从别处获取实例, 减少数据破坏情况"""
        if cls.__instantiated:
            raise SingleInstanceError()
        obj = super().__new__(cls)
        cls.__instantiated = True
        return obj

    def __init__(self):
        pass

    @requires_init
    def import_plugins(self):
        """
        导入插件, 只会导入选定路径下的首层模块, 模块内调用 register_plugin 来注册模块.

        _import_module 不支持模块结构, 如果被导入模块内部如果要导入子模块, 必须使用相对于选定路径的方式来导入.

        被导入的插件不能延迟导入其他模块, 必须在其被导入的时候导入其他所需的模块, 否则可能出现找不到指定模块的错误.
        """
        for path in self.IMPORT_PATH:
            for s in os.listdir(path):
                s = Path(path, s)
                sub_init = s.joinpath("__init__.py")
                if s.is_dir() and sub_init.exists():
                    n = s.name
                    p = sub_init
                elif s.is_file() and s.suffix == ".py" and s.stem != "__init__":
                    n = s.stem
                    p = path
                else:
                    continue
                if n not in self.IMPORTED_MODULE.keys():
                    # 不导入重复的模块.
                    with TempSysPath(path):  # 为了插件能导入子模块.
                        self.IMPORTED_MODULE[n] = _import_module(n, p)
                    logger.info(f"module: {n} imported.")
                else:
                    logger.info(f"module: "
                                f"{n} not imported for "
                                f"its name duplicates with previous one.")
