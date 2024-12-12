"""
插件配置.

Examples:

>>> plugin_config = PluginConfig("plugin_name_a")
>>> i = TextItem("address", "no.9 south street", value_assert=lambda a: "no." in a)
>>> i.set_value("no.10 south street")
>>> plugin_config.add(i)
>>> plugin_config.clone().serialize()
{'plugin_name_a': {'address': 'no.10 south street'}}
>>> i.set_value("something else")
Traceback (most recent call last):
    ...
ValueError: value didn't pass the value assertion: 'something else'
>>> TextItem("name", 1)
Traceback (most recent call last):
    ...
ValueError: invalid value type: <class 'int'>.
"""
from __future__ import annotations

import datetime
from abc import abstractmethod, ABC
from copy import deepcopy
from typing import Callable, TypeVar, Generic


class ItemType:
    TEXT = str  # 普通文字.
    NUMBER = int  # 整数数字 (可用于实现 Selector).
    DATE = datetime.date  # 日期.
    TIME = datetime.time  # 时间.
    DATETIME = datetime.datetime  # 日期和时间.


T = TypeVar(
    'T',
    ItemType.TEXT,
    ItemType.NUMBER,
    ItemType.DATE,
    ItemType.TIME,
    ItemType.DATETIME
)


class ConfigItem(ABC, Generic[T]):  # 子类继承 T 需为可序列化对象.
    """
    ConfigItem 为 PluginConfig 中的一个配置项.
    """

    def __init__(
            self,
            name: str,
            default_value: T,
            description: str = "",
            value_assert: Callable[[T], bool] = lambda value: True,
    ):
        """
        Parameters:
            name: 配置项的名称, 每个插件中的名称需要唯一, 否则在配置项可能无法保存, 但是不同插件可以拥有同一个名称的配置项.
                  只能为英文和下划线, 不能使用数字.
            default_value: 此配置项的默认值.
            description: 配置项的说明.
            value_assert: 配置项值判断函数, 如果值让其返回 False 则值不被此配置项接受.
        """
        if not (name and all(c.isalpha() or c == "_" for c in name)):
            raise ValueError(f"invalid name: {name}.")

        self._name = name
        self._description = description
        self._default_value = default_value
        self._value_assert = value_assert
        self.set_value(default_value)

    def name(self) -> str:
        return self._name

    def description(self) -> str:
        return self._description

    def assert_value(self, value: T) -> bool:
        return self._value_assert(value)

    def default_value(self) -> T:
        """获取此配置项的默认值"""
        return deepcopy(self._default_value)

    def current_value(self) -> T:
        """返回配置项当前的值"""
        return deepcopy(self._current_value)

    def set_value(self, value: T):
        """设置配置项当前数据"""
        if not self.check_type(value):
            raise ValueError(f"invalid value type: {type(value)} from {repr(value)}.")
        if not self.assert_value(value):
            raise ValueError(f"value didn't pass the value assertion: {repr(value)}")
        # noinspection PyAttributeOutsideInit
        self._current_value = value

    @abstractmethod
    def serialize(self):
        """返回当前值可序列化的对象"""

    @abstractmethod
    def check_type(self, value) -> bool:
        """检查值是否符合泛型"""

    @abstractmethod
    def from_serializable(self, obj):
        """从可序列化对象中恢复当前值"""


class TextItem(ConfigItem[str]):
    def serialize(self):
        return self.current_value()

    def check_type(self, value):
        return isinstance(value, str)

    def from_serializable(self, obj: str):
        self.set_value(obj)


class NumberItem(ConfigItem[int]):
    def serialize(self):
        return self.current_value()

    def check_type(self, value):
        return isinstance(value, int)

    def from_serializable(self, obj: int):
        self.set_value(obj)


class DateItem(ConfigItem[datetime.date]):
    def serialize(self):
        return self.current_value().strftime("%Y/%m/%d")

    def check_type(self, value):
        return isinstance(value, datetime.date)

    def from_serializable(self, obj: str):
        self.set_value(datetime.datetime.strptime(obj, "%Y/%m/%d").date())


class TimeItem(ConfigItem[datetime.time]):
    def serialize(self):
        return self.current_value().strftime("%H:%M:%S")

    def check_type(self, value):
        return isinstance(value, datetime.time)

    def from_serializable(self, obj: str):
        self.set_value(datetime.datetime.strptime(obj, "%H:%M:%S").time())


class DatetimeItem(ConfigItem[datetime.datetime]):
    def serialize(self):
        return self.current_value().strftime("%Y/%m/%d-%H:%M:%S")

    def check_type(self, value):
        return isinstance(value, datetime.datetime)

    def from_serializable(self, obj: str):
        self.set_value(datetime.datetime.strptime(obj, "%Y/%m/%d-%H:%M:%S"))


class PluginConfig:
    """
    PluginConfig 用于单个 Plugin 给 PluginLoader 提供自己配置项的说明,
    以便 PluginLoader 在加载 Plugin 的时候加载配置, 同时方便用户进行可视化的配置.
    """

    def __init__(self):
        self._items: dict[str, ConfigItem] = {}

    def add(self, item: ConfigItem):
        """添加配置项, 可链式调用"""
        if item.name() in self._items.keys():
            raise ValueError("Item with name '{}' already exists.".format(item.name()))
        self._items[item.name()] = item
        return self

    def serialize(self) -> dict:
        """把所有配置项转换成可序列化内容"""
        return {k: v.serialize() for k, v in self._items.items()}

    def from_serializable(self, obj: dict):
        """从可序列化对象中恢复所有配置项的值"""
        for k in obj.keys():
            self._items[k].from_serializable(obj[k])

    def clone(self) -> PluginConfig:
        """返回自身拷贝"""
        return deepcopy(self)

    def __iter__(self):
        return iter(self._items.values())

    def get_item(self, name: str) -> ConfigItem:
        return self._items[name]