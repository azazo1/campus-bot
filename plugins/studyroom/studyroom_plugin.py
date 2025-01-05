from __future__ import annotations

import datetime
import traceback

from plugins.studyroom.req import StudyRoomCache, ROOM_KINDID
from src.plugin import TimeItem, PluginContext, PluginConfig, register_plugin, Plugin, Routine, \
    NumberItem, TextItem


@register_plugin(
    name="studyroom_subscriber",
    configuration=PluginConfig()
    .add(TimeItem("min_reserve_time", datetime.time(minute=60), "要预约研修间的最短时间, h小时m分钟"))
    .add(TimeItem("max_reserve_time", datetime.time(hour=4), "要预约研修间的最长时间, h小时m分钟"))
    .add(NumberItem("auto_cancel", 1,
                    "是否自动取消未签到的将过期预约,\n如果为 1(True),\n检查账号下的所有研修间预约,\n在违约的前 1~2 分钟自动取消该预约,\n为 0 则不会.",
                    lambda a: 0 <= a <= 1,
                    ))
    .add(TextItem("reserve_place", "",
                    "选择预约的研修间位置, 支持:\n"
                    "- 普陀校区木门研究室\n"
                    "- 普陀校区玻璃门研究室\n"
                    "- 闵行校区研究室",
                    lambda a: a in ROOM_KINDID.keys(),
                    )),
    routine=Routine.MINUTELY,
    ecnu_cache_grabber=StudyRoomCache.grab_from_driver
)
class LibrarySeatSubscriberPlugin(Plugin):
    def __init__(self):
        self.min_reserve_time: datetime.timedelta | None = None
        self.max_reserve_time: datetime.timedelta | None = None
        self.auto_cancel: bool = False
        self.reserve_place: str | None = None


    def on_uia_login(self, ctx: PluginContext):
        try:
            cache = ctx.get_uia_cache().get_cache(StudyRoomCache)
            # todo 构建 query
        except Exception:
            ctx.report_cache_invalid()
            ctx.get_logger().error(traceback.format_exc())

    def on_config_load(self, ctx: PluginContext, cfg: PluginConfig):
        t = cfg.get_item("min_reserve_time").current_value
        self.min_reserve_time = datetime.timedelta(hours=t.hour, minutes=t.minute)
        t = cfg.get_item("max_reserve_time").current_value
        self.max_reserve_time = datetime.timedelta(hours=t.hour, minutes=t.minute)
        t = cfg.get_item("auto_cancel").current_value
        self.auto_cancel = bool(t)
        self.reserve_place = cfg.get_item("reserve_place").current_value


    def on_config_save(self, ctx: PluginContext, cfg: PluginConfig):
        self.on_config_load(ctx, cfg)

    def on_routine(self, ctx: PluginContext):
        if self.auto_cancel:
            # todo 自动取消预约逻辑
            pass

