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
            name="notice_before_class_start", default_value=datetime.time(0, 10, 0),
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
        self.notified_schedules: set[ClassSchedule] = set()
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
            return
        self.calendar_query = CalendarQuery(cache)

    def on_routine(self, ctx: PluginContext):
        if self.calendar_query is not None:
            self.throttler.throttle(self.update_schedules, ctx)
        now = datetime.datetime.now()
        for sche in self.schedules:
            if now < sche.startTime < now + self.time_ahead:
                if sche in self.notified_schedules:
                    ctx.get_logger().info(f"{sche.title} is reaching...")
                    # todo 通过邮件或者其他方式提醒用户.
                    # todo 添加邮件提醒插件;
                    # todo 账号密码保存在其下;
                    # todo configitem 添加 password 类型;
                    # todo 实现插件间通信, 调用方法为: ctx.send(plugin_name, message), 间接调用, 不返回值, 不是立即到达, 只有被加载的插件能够接收消息.
                    # todo ctx 提供特定插件是否被加载查询.
                self.notified_schedules.add(sche)
            else:
                self.notified_schedules.remove(sche)

    def update_schedules(self, ctx: PluginContext):
        now_time = datetime.datetime.now()
        try:
            schedules = self.calendar_query.query_user_schedules(
                int(now_time.timestamp() * 1000),
                int((now_time + datetime.timedelta(days=1)).timestamp() * 1000)
            )
        except (AttributeError, LoginError):
            ctx.report_cache_invalid()
            return
        self.notified_schedules.clear()
        self.schedules = schedules
        ctx.get_logger().info("class schedules updated.")
