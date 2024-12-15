"""
校历查询.
"""

import datetime

from src.portal import PortalCache
from src.portal.calendar import Request

__all__ = ["CalendarQuery"]

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


class CalendarQuery(Request):
    def __init__(self, cache: PortalCache):
        super().__init__(cache)

    def query_user_schedules(self, start_time: int, end_time: int):
        """
        查询用户课程规划.

        Parameters:
            start_time: 筛选器要查询的真实时间时间段, 以毫秒时间戳表示.
            end_time: 同 start_time, 时间段结尾.
        """
        rsp = self.query(query=USER_SCHEDULES, variables={
            "filter": {
                "startTime": {"eq": int(start_time)},
                "endTime": {"eq": int(end_time)}
            }
        })
        ret = self.check_login_and_extract_data(rsp)
        return ret

    def query_user_class_table(self):
        """
        查询用户课程表.

        Tips: 查询本周和下周, 聚合双周的课程表.
        """
        now = datetime.datetime.now()

        current_week_start = now - datetime.timedelta(days=now.weekday())  # 本周一 00:00
        next_week_start = current_week_start + datetime.timedelta(weeks=1)  # 下周一 00:00

        start_time_this_week = int(current_week_start.timestamp() * 1000)
        end_time_this_week = int((current_week_start + datetime.timedelta(days=7)).timestamp() * 1000)

        start_time_next_week = int(next_week_start.timestamp() * 1000)
        end_time_next_week = int((next_week_start + datetime.timedelta(days=7)).timestamp() * 1000)

        this_week_courses = self.query_user_schedules(start_time_this_week, end_time_this_week)
        next_week_courses = self.query_user_schedules(start_time_next_week, end_time_next_week)

        all_courses = {
            "userSchedules": []
        }

        seen_descriptions = set()

        def remove_duplicates(schedules):
            for schedule in schedules:
                unique_key = schedule["description"]
                if unique_key not in seen_descriptions:
                    all_courses["userSchedules"].append(schedule)
                    seen_descriptions.add(unique_key)

        # 合并两个 userSchedules 列表
        if "userSchedules" in this_week_courses:
            remove_duplicates(this_week_courses["userSchedules"])
        if "userSchedules" in next_week_courses:
            remove_duplicates(next_week_courses["userSchedules"])

        return all_courses

    @staticmethod
    def collect_course_info(data):
        """
        根据返回的数据，提取简洁的课程信息。

        :param data: 包含课程信息的字典数据
        :return: 简化后的课程信息列表
        """
        schedules = data.get("userSchedules", [])
        result = []

        for schedule in schedules:
            course_name = schedule.get("title")
            location = schedule.get("address")
            start_timestamp = schedule.get("startTime")
            end_timestamp = schedule.get("endTime")

            hosts = schedule.get("hosts", [])
            teacher = [host.get("name") for host in hosts if isinstance(host, dict)]

            start_time = datetime.datetime.fromtimestamp(start_timestamp).strftime('%Y-%m-%d %H:%M:%S') if start_timestamp else "未知时间"
            end_time = datetime.datetime.fromtimestamp(end_timestamp).strftime('%Y-%m-%d %H:%M:%S') if end_timestamp else "未知时间"

            result.append({
                "course_name": course_name,
                "location": location,
                "start_time": start_time,
                "end_time": end_time,
                "teacher": teacher
            })

        return result
