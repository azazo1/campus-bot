from __future__ import annotations

import datetime
import traceback

from .query import StudyRoomQuery
from .req import StudyRoomCache, ROOM_KINDID
from src.plugin import TimeItem, PluginContext, PluginConfig, register_plugin, Plugin, Routine, \
    NumberItem, TextItem
from .subscribe import StudyRoomReserve


@register_plugin(
    name="studyroom_subscriber",
    description="研修间自动预约和取消预约",
    configuration=PluginConfig()
    .add(TimeItem("min_reserve_time", datetime.time(hour=1), "要预约研修间的最短时间, h小时m分钟",
                  lambda a: datetime.time(hour=1) <= a <= datetime.time(hour=4)))
    .add(TimeItem("max_reserve_time", datetime.time(hour=4), "要预约研修间的最长时间, h小时m分钟",
                  lambda a: datetime.time(hour=1) <= a <= datetime.time(hour=4)))
    .add(NumberItem("auto_cancel", 1,
                    "是否自动取消未签到的将过期预约,\n如果为 1(True),\n检查账号下的所有研修间预约,\n在违约的前 1~2 分钟自动取消该预约,\n为 0 则不会.",
                    lambda a: 0 <= a <= 1,
                    ))
    .add(TextItem("reserve_place", "普陀校区木门研究室",
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
        self.query: StudyRoomQuery | None = None
        self.reserve: StudyRoomReserve | None = None

    def on_load(self, ctx: PluginContext):
        def sub():
            rst = self.reserve.submit_reserve(
                day="tomorrow",
                kind_name=self.reserve_place,
                min_duration_minutes=self.min_reserve_time.seconds // 60,
                max_duration_minutes=self.max_reserve_time.seconds // 60,
            )
            resv = rst['resvDevInfoList']
            resv_str = []
            for r in resv:
                resv_str.append(f"{r['kindName']} - {r['labName']} - {r['roomName']}")
            ctx.send_message("email_notifier",
                             ("text",
                              "研修间预约成功",
                              "预约成功:\n{}".format("\n".join(resv_str))))
        ctx.bind_action("演示按钮", sub)

    def on_uia_login(self, ctx: PluginContext):
        try:
            cache = ctx.get_uia_cache().get_cache(StudyRoomCache)
            self.query = StudyRoomQuery(cache)
            self.reserve = StudyRoomReserve(cache)
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
        if not self.query or not self.reserve:
            ctx.report_cache_invalid()
            return
        if self.auto_cancel:
            resv = self.query.check_resvInfo(2)
            if not resv:
                ctx.report_cache_invalid()
                return
            for r in resv:
                if (datetime.datetime.fromtimestamp(r["latestCheckInTime"] / 1000)
                        - datetime.datetime.now()
                        < datetime.timedelta(minutes=2)):
                    self.reserve.cancel_reservation(r["uuid"])
                    ctx.send_message("", (
                        'text',
                        "研修间预约自动取消",
                        f"取消预约, 详细消息: {r['resvDevInfoList']}"
                    ))

    def on_recv(self, ctx: PluginContext, from_plugin: str,
                next_class_start_time: datetime.datetime):
        """下课时触发"""
        now = datetime.datetime.now()
        off_class_duration = next_class_start_time - now
        if self.max_reserve_time >= off_class_duration >= self.min_reserve_time:
            rst = self.reserve.submit_reserve(
                day="today",
                kind_name=self.reserve_place,
                min_duration_minutes=self.min_reserve_time.seconds // 60,
                max_duration_minutes=self.max_reserve_time.seconds // 60,
            )
            if "成功" in rst["message"]:
                resv = rst['resvDevInfoList']
                resv_str = []
                for r in resv:
                    resv_str.append(f"{r['kindName']} - {r['labName']} - {r['roomName']}")
                ctx.send_message("email_notifier",
                                 ("text",
                                  "研修间预约成功",
                                  "预约成功:\n{}".format("\n".join(resv_str))))
