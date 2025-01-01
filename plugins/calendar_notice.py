import datetime

from src import Throttler
from src.plugin import register_plugin, PluginConfig, Routine, Plugin, PluginContext, \
    TimeItem
from src.portal import PortalCache
from src.portal.calendar.query import CalendarQuery, ClassSchedule
from src.uia.login import LoginError


@register_plugin(
    name="calendar_notice",
    configuration=PluginConfig().add(
        TimeItem(
            name="notice_before_class_start", default_value=datetime.time(0, 10),
            description="上课提前提醒时间 (提前h小时m分钟)"
        )
    ),
    routine=Routine.MINUTELY,
    ecnu_cache_grabber=PortalCache.grab_from_driver
)
class CalendarNotice(Plugin):
    def __init__(self):
        self.calendar_query: CalendarQuery | None = None
        self.time_ahead: datetime.timedelta | None = None
        self.schedules: list[ClassSchedule] = []
        self.notified_class_on_schedules: set[ClassSchedule] = set()
        self.notified_class_off_schedules: set[ClassSchedule] = set()
        self.throttler = Throttler(datetime.timedelta(minutes=10))

    def on_config_load(self, ctx: PluginContext, cfg: PluginConfig):
        item = cfg.get_item("notice_before_class_start")
        t = item.current_value
        self.time_ahead = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)

    def on_config_save(self, ctx: PluginContext, cfg: PluginConfig):
        item = cfg.get_item("notice_before_class_start")
        t = item.current_value
        self.time_ahead = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)

    def on_uia_login(self, ctx: PluginContext):
        login_cache = ctx.get_uia_cache()
        cache = login_cache.get_cache(PortalCache)
        if not cache:
            ctx.get_logger().error("failed to get cache.")
            ctx.report_cache_invalid()
            return
        self.calendar_query = CalendarQuery(cache)
        self.update_schedules(ctx)

    def on_routine(self, ctx: PluginContext):
        self.throttler.throttle(self.update_schedules, ctx)
        now = datetime.datetime.now()
        for sche in self.schedules:
            if now < sche.startTime < now + self.time_ahead:  # 上课前的指定时间之内.
                if sche not in self.notified_class_on_schedules:
                    ctx.get_logger().info(f"{sche.title} is reaching...")
                    ctx.send_message("email_notifier",
                                     (
                                         "课程即将开始",
                                         f"{sche.title} [{sche.address}] 即将开始({sche.startTime.strftime('%m-%d %H:%M:%S')})"
                                     ))  # 发送邮件提醒用户.
                    self.notified_class_on_schedules.add(sche)
            else:
                if sche in self.notified_class_on_schedules:
                    self.notified_class_on_schedules.remove(sche)
            if (datetime.timedelta(0)
                    < now - sche.endTime
                    < datetime.timedelta(minutes=5)):  # 下课后的五分钟之内.
                if sche not in self.notified_class_off_schedules:
                    ctx.get_logger().info(f"{sche.title} is about to end...")
                    next_class_schedule = self.get_next_class_schedule()
                    if next_class_schedule:
                        ctx.send_message("library_seat_subscriber",
                                         next_class_schedule.startTime)
                    self.notified_class_off_schedules.add(sche)
            else:
                if sche in self.notified_class_off_schedules:
                    self.notified_class_off_schedules.remove(sche)

    def get_next_class_schedule(self) -> ClassSchedule | None:
        """获取下一个即将开始的课程"""
        td = datetime.timedelta(weeks=1)  # 一个足够大的时间作初始值.
        now_time = datetime.datetime.now()
        rst = None
        for sche in self.schedules:
            new_td = sche.startTime - now_time
            if datetime.timedelta(0) < new_td < td:
                td = sche.endTime - now_time
                rst = sche
        return rst

    def update_schedules(self, ctx: PluginContext):
        now_time = datetime.datetime.now()
        try:
            schedules = self.calendar_query.query_user_schedules(
                int((now_time - datetime.timedelta(days=1)).timestamp() * 1000),
                int((now_time + datetime.timedelta(days=1)).timestamp() * 1000)
            )
        except (AttributeError, LoginError):
            ctx.report_cache_invalid()
            return
        self.schedules = schedules
        ctx.get_logger().info("class schedules updated.")
