import datetime
import textwrap
from typing import Self

import requests
from requests import Response
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire.webdriver import Edge
import selenium.webdriver.support.expected_conditions as EC

from src import Throttler
from src.plugin import register_plugin, PluginConfig, Routine, Plugin, PluginContext, \
    TimeItem
from src.uia.login import LoginError

USER_SCHEDULES = """
query ($filter: ScheduleFilter, $userId: String) {
  userSchedules(filter: $filter, userId: $userId) {
    address
    hosts {
      name
      account
      openid
    }
    description
    endTime
    id
    startTime
    title # title 与 description 一致
    __typename
  }
}
"""

SCHOOL_CALENDAR = """
query ($term: Int, $year: Int, $filter: SchoolCalendarFilter) {
  schoolCalendar(term: $term, year: $year, filter: $filter) {
    createTime
    creator {
      account
      email
      name
      openid
      phone
      __typename
    }
    endTime
    id
    memo
    startTime
    term
    termName
    updateTime
    year
    __typename
  }
}
"""


class PortalCache:
    def __init__(self, authorization: str):
        self.authorization = authorization

    def __repr__(self):
        auth_display = textwrap.shorten(self.authorization, width=10)
        return f"PortalCache(authorization='{auth_display}')"

    @classmethod
    def grab_from_driver(cls, driver: Edge, timeout: float = 24 * 60) -> Self:
        driver.get("https://portal2023.ecnu.edu.cn/portal/home")
        WebDriverWait(driver, timeout).until(
            EC.url_matches("https://portal2023.ecnu.edu.cn/")
        )
        req = driver.wait_for_request("calendar-new", 60)
        return cls(req.headers['Authorization'])


class Request:
    def __init__(self, cache: PortalCache):
        self.cache = cache
        if self.cache is None:
            raise ValueError("cache cannot be None.")

    @classmethod
    def check_login_and_extract_data(cls, response: Response) -> dict:
        """
        进行返回内容的一系列检查, 并对表示错误的返回值以报错或日志的形式呈现.

        Parameters:
            response: requests 请求的返回返回对象.

        Raises:
            LoginError: 登录失效及请求错误.

        Returns:
            如果执行正常, 返回请求回应中的 json 结构 data 字段.
        """
        if response.status_code != 200:
            raise LoginError(f"response status code: {response.status_code}.")
        if "json" not in response.headers["content-type"]:
            raise LoginError("request was redirected, which means you didn't login.")
        ret = response.json()
        if ret.get("data") is None:
            raise LoginError(f"response has no valid data, {ret}.")
        return ret["data"]

    def query(self, query: str, variables: dict,
              headers: dict = None) -> requests.Response:
        """
        向 calendar-new 提交 POST 请求并自动附加以下内容:

        url: https://portal2023.ecnu.edu.cn/bus/graphql/calendar-new

        headers:
            Authorization: ...
            Content-Type: application/json

        payload(GraphQL): {"query": query, "variables": variables}
        """
        headers_ = {"Authorization": self.cache.authorization, "Content-Type": "application/json"}
        if headers is not None:
            headers_.update(headers)
        return requests.post(
            "https://portal2023.ecnu.edu.cn/bus/graphql/calendar-new",
            headers=headers_,
            json={
                "query": query,
                "variables": variables,
            },  # 这里不能选择 data 的形参, 这里使用 GraphQL 传递数据.
        )


class ClassSchedule:
    def __init__(self):
        self.address = ""
        self.hosts = []
        self.description = ""
        self.endTime = datetime.datetime.fromtimestamp(0)
        self.id = ""
        self.startTime = datetime.datetime.fromtimestamp(0)
        self.title = ""
        self.typename = ""

    @classmethod
    def from_json_objs(cls, json_objs: list) -> list[Self]:
        rst = []
        try:
            for obj in json_objs:
                cs = ClassSchedule()
                cs.address = obj["address"]
                cs.hosts.extend(obj["hosts"])
                cs.description = obj["description"]
                cs.endTime = datetime.datetime.fromtimestamp(obj["endTime"])
                cs.id = obj["id"]
                cs.startTime = datetime.datetime.fromtimestamp(obj["startTime"])
                cs.title = obj["title"]
                cs.typename = obj["__typename"]
                rst.append(cs)
        except (KeyError, AttributeError) as e:
            raise LoginError(str(e))
        return rst


class CalendarQuery(Request):
    def __init__(self, cache: PortalCache):
        super().__init__(cache)

    def query_user_schedules(self, start_time: int, end_time: int, optimize: bool) \
            -> list[ClassSchedule]:
        """
        查询用户课程规划.

        Parameters:
            start_time: 筛选器要查询的真实时间时间段, 以毫秒时间戳表示.
            end_time: 同 start_time, 时间段结尾.
            optimize: 是否去除重复的课程,
                如果两个 ClassSchedule 的标题和上课星期相同,
                那么他们是重复的.

        Returns:
            课表数据, 见 ClassSchedule.
        """
        rsp = self.query(query=USER_SCHEDULES, variables={
            "filter": {
                "startTime": {"eq": int(start_time)},
                "endTime": {"eq": int(end_time)}
            }
        })
        ret = self.check_login_and_extract_data(rsp)
        schedules = ClassSchedule.from_json_objs(ret.get("userSchedules"))
        if not optimize:
            return schedules
        else:
            return self._optimize(schedules)

    def query_school_calendar(self) -> dict:
        """
        查询学校日历
        """
        # 校历无需 filter 参数.
        rsp = self.query(query=SCHOOL_CALENDAR, variables={})
        ret = self.check_login_and_extract_data(rsp)
        return ret

    @staticmethod
    def _optimize(class_schedules: list[ClassSchedule]) -> list[ClassSchedule]:
        """
        去除重复的课程

        如果两个 ClassSchedule 的 title 和 上课星期是相同的, 那么两个 ClassSchedule 是重复的
        """
        # 去重逻辑
        seen = set()
        unique_classes = []
        for cls in class_schedules:
            # 提取上课的星期几和时间 (小时和分钟)
            weekday = cls.startTime.weekday()  # 0 = 周一, 6 = 周日
            # 创建唯一标识: (课程, 星期, 时间)
            identifier = (cls.title, weekday)
            if identifier not in seen:
                seen.add(identifier)
                unique_classes.append(cls)
        return unique_classes

@register_plugin(
    name="calendar_notice",
    description="课程提醒辅助插件, 产生课程消息给其他插件",
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
                int((now_time + datetime.timedelta(days=1)).timestamp() * 1000),
                True
            )
        except (AttributeError, LoginError):
            ctx.report_cache_invalid()
            return
        self.schedules = schedules
        ctx.get_logger().info("class schedules updated.")
