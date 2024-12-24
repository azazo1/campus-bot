"""
校历查询.
"""

import datetime
from typing import Self

from src.portal import PortalCache
from src.portal.calendar import Request

__all__ = ["CalendarQuery"]

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
            课表数据.
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
