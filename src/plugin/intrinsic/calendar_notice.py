import datetime

from src.plugin import register_plugin, PluginConfig, Routine, Plugin, PluginContext, \
    NumberItem
from src.portal import PortalCache
from src.portal.calendar.query import CalendarQuery
from src.uia.login import LoginError


@register_plugin(
    name="calendar_notice",
    configuration=PluginConfig().add(
        NumberItem(
            name="notice_before_class_start", default_value=10 * 60, description="上课提前提醒时间"
        )
    ),
    routine=Routine.MINUTELY,
    ecnu_cache_grabber=PortalCache.grab_from_driver
)
class CalendarNotice(Plugin):
    def __init__(self):
        self.calendar_query: CalendarQuery | None = None
        self.time_ahead: int | None = None

    def on_config_load(self, ctx: PluginContext, cfg: PluginConfig):
        item = cfg.get_item("notice_before_class_start")
        self.time_ahead = item.current_value()

    def on_uia_login(self, ctx: PluginContext):
        login_cache = ctx.get_uia_cache()
        cache = login_cache.get_cache(PortalCache)
        if not cache:
            ctx.get_logger().error("failed to get cache.")
            return
        self.calendar_query = CalendarQuery(cache)

    def on_routine(self, ctx: PluginContext):
        now_time = datetime.datetime.now()
        try:
            schedule = self.calendar_query.query_user_schedules(
                int(now_time.timestamp() * 1000),
                int((now_time + datetime.timedelta(days=1)).timestamp() * 1000)
            )
        except (AttributeError, LoginError):
            ctx.report_cache_invalid()
            return
        # not yet implemented the function.
        ctx.get_logger().debug(schedule)
        ctx.get_logger().debug(f"{self.time_ahead=}")
