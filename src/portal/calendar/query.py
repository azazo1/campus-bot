"""
校历查询.
"""
from src.portal.calendar import Request
from src.uia.login import PortalCache

__all__ = ["CalendarQuery"]

USER_SCHEDULES = """
query ($filter: ScheduleFilter, $userId: String) {
  userSchedules(filter: $filter, userId: $userId) { # 课表
    address # 上课地点
    allDay # 全日课
    attachments
    calendar {
      colour
      content
      id
      name
      __typename
    }
    hosts {
      name
      account
      openid
      __typename
    }
    createTime
    creator {
      account
      name
      openid
      __typename
    }
    description # 课程描述, 和 title 值相似
    endTime # 此次课结束的时间戳
    id
    leader
    startTime # 此次课开始时间
    system {
      id
      name
      __typename
    }
    title # 课程名称
    updateTime
    __typename
  }
}
"""


class CalendarQuery(Request):
    def __init__(self, cache: PortalCache):
        super().__init__(cache)

    def query_user_schedules(self, start_time: int, end_time: int):
        """
        查询用户课程规划.

        Parameters:
            start_time, end_time: 筛选器要查询的真实时间时间段, 以毫秒时间戳表示.
        """
        rsp = self.query(query=USER_SCHEDULES, variables={
            "filter": {
                "startTime": {"eq": start_time},
                "endTime": {"eq": end_time}
            }
        })
        ret = self.check_login_and_extract_data(rsp)
        return ret
