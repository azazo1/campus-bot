import datetime

from src.plugin import register_plugin, Plugin, PluginContext, PluginConfig, TextItem, NumberItem, \
    DateItem, TimeItem, DatetimeItem


def is_time_seq(t1: datetime.time, t2: datetime.time):
    return (datetime.timedelta(hours=t1.hour, minutes=t1.minute, seconds=t1.second,
                               microseconds=t1.microsecond)
            - datetime.timedelta(hours=t2.hour, minutes=t2.minute, seconds=t2.second,
                                 microseconds=t2.microsecond)
            >= datetime.timedelta())


@register_plugin(name="simple_demo",
                 configuration=PluginConfig()
                 .add(NumberItem("a", 1))
                 .add(NumberItem("b", 1, "只能选择 1 到 10", lambda a: 0 < a <= 10))
                 .add(TextItem("c", "Hello World", "输入字符串"))
                 .add(DateItem("select_a_day", datetime.date(2024, 1, 1),
                               "选择一个日期, 只能选择 2024 年的日期",
                               lambda a: a.year == 2024))
                 .add(TimeItem("select_a_time", datetime.time(12, 0),
                               "选择一个时间, 只能选择 12:00p.m. 之后的时间",
                               lambda a: is_time_seq(a, datetime.time(12, 0))))
                 .add(DatetimeItem("select_a_datetime", datetime.datetime(2024, 12, 24, 12, 0),
                                   "选择一个日期时间"))
                 .add(NumberItem("e", 1, "测试用"))
                 .add(NumberItem("f", 1, "测试用"))
                 .add(NumberItem("g", 1, "测试用"))
                 .add(NumberItem("h", 1, "测试用"))
                 .add(NumberItem("i", 1, "测试用"))
                 .add(NumberItem("j", 1, "测试用"))
                 .add(NumberItem("k", 1, "测试用"))
                 .add(NumberItem("l", 1, "测试用"))
                 .add(NumberItem("m", 1, "测试用"))
                 )
class SimpleDemoPlugin(Plugin):
    def on_register(self, ctx: PluginContext):
        ctx.get_logger().info("simple demo known it's registered")
