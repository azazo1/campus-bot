"""
校历查询.
"""

import datetime
from typing import Self

from src.portal import PortalCache
from src.portal.calendar import Request

__all__ = ["CalendarQuery", "ClassSchedule"]

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

    def query_user_schedules(self, start_time: int, end_time: int) -> list[ClassSchedule]:
        """
        查询用户课程规划.

        Parameters:
            start_time: 筛选器要查询的真实时间时间段, 以毫秒时间戳表示.
            end_time: 同 start_time, 时间段结尾.

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
        return ClassSchedule.from_json_objs(ret.get("userSchedules"))

    def query_school_calendar(self) -> dict:
        """
        查询学校日历, 校历无需 filter 参数.
        """
        rsp = self.query(query=SCHOOL_CALENDAR, variables={})
        ret = self.check_login_and_extract_data(rsp)
        return ret

    def query_user_class_table(self) -> list[ClassSchedule]:
        """
        查询本周和下周, 聚合双周的课程表. (考虑到某些课程只有单周有)
        Tips:
            1. 未经处理的示例返回:
                [ClassSchedule(title=面向对象程序设计（基于Python）, address=理科大楼B226, startTime=2024-12-24 18:00:00, endTime=2024-12-24 19:35:00)
                ClassSchedule(title=面向对象程序设计（基于Python）, address=理科大楼B226, startTime=2024-12-31 18:00:00, endTime=2024-12-31 19:35:00)
                ClassSchedule(title=面向对象程序设计(基于Python)实践, address=理科大楼B226, startTime=2024-12-24 19:40:00, endTime=2024-12-24 20:25:00)
                ClassSchedule(title=面向对象程序设计(基于Python)实践, address=理科大楼B226, startTime=2024-12-31 19:40:00, endTime=2024-12-31 20:25:00)
                ClassSchedule(title=军事理论（含军训）, address=文附楼218, startTime=2024-12-23 18:00:00, endTime=2024-12-23 19:35:00)
                ClassSchedule(title=军事理论（含军训）, address=文附楼218, startTime=2024-12-30 18:00:00, endTime=2024-12-30 19:35:00)

            注意几种特殊情况, 需要特殊去重:
                1. 当相同课程在一周内有多节课时
                2. 当相同课程在一天内有多节课时

            2. 此接口存在 host 字段返回不稳定的问题, 优先使用空的教师名字作为传入 LateX 代码的参数.

        Todo: 考虑多次频繁调用接口直至出现 host 字段

        Returns: 用户课程表
        """
        now = datetime.datetime.now()  # 当前时间: 2024-12-26 14:11:00.123456
        current_week_start = now - datetime.timedelta(days=now.weekday())  # 本周一 00:00
        start_time = int(current_week_start.timestamp() * 1000)  # 本周一 00:00 时间戳
        end_time = int((current_week_start + datetime.timedelta(days=14)).timestamp() * 1000)  # 下周日 23:59 的时间戳
        double_week_class_table = self.query_user_schedules(start_time, end_time)

        # 去重逻辑
        seen = set()
        unique_classes = []
        for cls in double_week_class_table:

            # 提取上课的星期几和时间 (小时和分钟)
            weekday = cls.startTime.weekday()  # 0 = 周一, 6 = 周日
            class_time = cls.startTime.time().replace(second=0, microsecond=0)  # 仅保留时分

            # 创建唯一标识: (课程, 星期, 时间)
            identifier = (cls.title, weekday)
            if identifier not in seen:
                seen.add(identifier)
                unique_classes.append(cls)

        return unique_classes