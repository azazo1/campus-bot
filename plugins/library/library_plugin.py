from __future__ import annotations

import datetime
import traceback
from typing import Any

from src.plugin import TimeItem, PluginContext, PluginConfig, register_plugin, Plugin, Routine, \
    NumberItem
from src.uia.login import LoginError
from .subscribe import Subscribe
from .query import LibraryQuery, QuickSelect
from .req import LibCache
from .seat import SeatFinder


@register_plugin(
    name="library_seat_subscriber",
    description="图书馆座位预约插件",
    configuration=PluginConfig()
    .add(TimeItem("prefer_study_duration", datetime.time(hour=4),
                  "偏好的学习时长(h小时m分钟),\n当一次下课时接下来的非上课时间超过此时长,\n则自动预约图书馆座位.\n不建议设置太短, 频繁地预约取消会达到当天预约取消次数上限."))
    .add(NumberItem("auto_cancel", 1,
                    "是否自动取消未签到的将过期预约,\n如果为 1(True),\n检查账号下的所有图书馆预约,\n在违约的前 1~2 分钟自动取消该预约,\n为 0 则不会.",
                    lambda a: 0 <= a <= 1,
                    ))
    .add(NumberItem("premise", -1,
                    "预约座位选择的校区, 0 为普陀, 1 为闵行, -1 为不限.",
                    lambda a: -1 <= a <= 1,
                    )),
    routine=Routine.MINUTELY,
    ecnu_cache_grabber=LibCache.grab_from_driver
)
class LibrarySeatSubscriberPlugin(Plugin):
    def __init__(self):
        self.prefer_study_duration: datetime.timedelta | None = None
        self.auto_cancel: bool = False
        self.premise: int = -1
        self.library_query: LibraryQuery | None = None
        self.subscriber: Subscribe | None = None

    def on_uia_login(self, ctx: PluginContext):
        try:
            cache = ctx.get_uia_cache().get_cache(LibCache)
            self.library_query = LibraryQuery(cache)
            self.subscriber = Subscribe(cache)
        except Exception:
            ctx.report_cache_invalid()
            ctx.get_logger().error(traceback.format_exc())

    def on_config_load(self, ctx: PluginContext, cfg: PluginConfig):
        t = cfg.get_item("prefer_study_duration").current_value
        self.prefer_study_duration = datetime.timedelta(hours=t.hour, minutes=t.minute)
        t = cfg.get_item("auto_cancel").current_value
        self.auto_cancel = bool(t)
        t = cfg.get_item("premise").current_value
        self.premise = t

    def on_config_save(self, ctx: PluginContext, cfg: PluginConfig):
        self.on_config_load(ctx, cfg)

    def premise_filter(self, qs: QuickSelect):
        def filter_func(area: dict, qs_=qs):
            if self.premise == -1:
                return True
            return qs_.get_premises_of(int(area["id"])) == self.premise

        return filter_func

    def on_recv(self, ctx: PluginContext, from_plugin: str, obj: Any):
        """
        接收下课消息, 下课时触发, 见 calendar_notice. # 已经放弃解耦了.
        obj: datetime.datetime (下一次上课的时间)
        """
        assert isinstance(obj, datetime.datetime)
        if not self.library_query or not self.subscriber:
            ctx.report_cache_invalid()
            return
        if obj - datetime.datetime.now() < self.prefer_study_duration:
            return
        try:
            qs = self.library_query.quick_select()
            area_id = qs.get_most_free_seats_area(self.premise_filter(qs))
            days = self.library_query.query_time(area_id)
            if not days or not days[0].times:
                ctx.get_logger().info("no available subscribing time")
            subscribe_time = days[0].times[0]
            sf = SeatFinder(self.library_query.query_seats(area_id, subscribe_time))
            target_seat = sf.find_most_isolated()
            rst = self.subscriber.confirm(target_seat.id, subscribe_time)
            ctx.get_logger().info(f"subscribe result: {rst}")
            ctx.send_message("email_notifier", ("text", "图书馆座位预约", f"预约结果: {rst}"))
        except LoginError:
            ctx.report_cache_invalid()

    def on_routine(self, ctx: PluginContext):
        if self.subscriber is None:
            ctx.report_cache_invalid()
            return
        if self.auto_cancel:
            for subs in self.subscriber.query_subscribes():
                last_signin_time = datetime.datetime.strptime(
                    subs["lastSigninTime"],
                    "%Y-%m-%d %H:%M:%S"
                )
                if last_signin_time - datetime.datetime.now() < datetime.timedelta(minutes=2):
                    self.subscriber.cancel(subs["id"])
                    ctx.send_message("email_notifier",
                                     ("text",
                                     "图书馆座位预约取消",
                                      f"已经为你自动取消即将过期的预约: {subs['nameMerge']} {subs['no']} 座位"))
