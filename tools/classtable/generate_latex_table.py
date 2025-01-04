import datetime
import logging
import os
from typing import Optional, List
from dataclasses import dataclass

# 元组 (start_hour, start_minute, end_hour, end_minute)
time_slots = [
    ((8, 0), (8, 45)), ((8, 50), (9, 35)), ((9, 50), (10, 35)), ((10, 40), (11, 25)), ((11, 30), (12, 15)),  # 上午
    ((13, 0), (13, 45)), ((13, 50), (14, 35)), ((14, 50), (15, 35)), ((15, 40), (16, 25)), ((16, 30), (17, 15)),  # 下午
    ((18, 0), (18, 45)), ((18, 50), (19, 35)), ((19, 40), (20, 25))  # 晚上
]


@dataclass
class ClassSchedule:
    title: str
    address: str
    startTime: datetime.datetime
    endTime: datetime.datetime
    description: str
    hosts: List[Optional[dict[str, str]]]
    typename: str


class LatexGenerator:
    def __init__(self, courses, file_prefix="timetable"):
        self.courses = courses
        self.file_prefix = file_prefix
        self.file_name = file_prefix + ".tex"
        self.week_courses = {i: [] for i in range(7)}  # 按星期分类课程, 0 = 周一, 1 = 周二, ... , 6 = 周日

    @staticmethod
    def time_to_slot(hour: int, minute: int) -> Optional[int]:
        """
        给定一个小时和分钟, 返回对应的节次编号.
        Tips: 遍历 time_slots, 看这个时间落在哪个范围内的开始 - 结束之间.
        这里假设 start_time 就落在对应节次的开始时间或稍后一点点.

        :param hour: 小时
        :param minute: 分钟
        :return: 将小时和分钟映射到节次编号 (1 开始计数)
        """
        for i, ((sh, sm), (eh, em)) in enumerate(time_slots, start=1):
            start_time = sh * 60 + sm
            end_time = eh * 60 + em
            current = hour * 60 + minute
            # 这里假设当前时间点 >= 节次的开始时间 且 < 节次的结束时间，即为该节次
            if start_time <= current <= end_time:
                return i
        return None

    def classify_courses(self):
        """
        将课程按照星期分类, 并提取出课程的开始节次和结束节次.

        Tips:
            由于接口原因, 在获取用户课表时可能出现 hosts 字典为 None 的情况.
            优先使用空的教师名字作为传入 LateX 代码的参数.
        """
        for cls in self.courses:
            start_dt = cls.startTime
            end_dt = cls.endTime
            wday = start_dt.weekday()  # 获取星期几 (0 = 周一, 6 = 周日)

            # 找到开始节次和结束节次
            start_slot = self.time_to_slot(start_dt.hour, start_dt.minute)
            end_slot = self.time_to_slot(end_dt.hour, end_dt.minute)

            if start_slot is None or end_slot is None:
                logging.warning(f"课程时间未匹配到节次: {cls.title} 时间: {cls.startTime} - {cls.endTime}")
                continue  # 跳过无法匹配节次的课程

            # 提取教师信息
            teacher_str = " "  # 默认教师为空
            if cls.hosts:
                for host in cls.hosts:
                    if host and 'name' in host and host['name']:
                        teacher_str = host['name']
                        break  # 找到第一个有效的教师名称后退出循环

            # 收集课程信息
            self.week_courses[wday].append({
                'course_name': cls.title,
                'start_slot': start_slot,
                'end_slot': end_slot,
                'location': cls.address,
                'teacher': teacher_str
            })

    def generate_latex(self):
        colors = ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9"]
        latex_output = [
            r"\documentclass[libertinus,en,sharp,landscape]{tools/classtable/litetable}",
            r"\begin{document}",
            r"",
            r"\timelist{",
            r"8:00,8:50,09:50,10:40,11:30,13:00,13:50,14:50,15:40,16:30,18:00,18:50,19:40;",
            r"8:45,9:35,10:35,11:25,12:15,13:45,14:35,15:35,16:25,17:15,18:45,19:35,20:25",
            r"}",
            r"",
            r"\sticker{tools/classtable/favicon}",
            r"",
            r"\begin{tikzpicture}",
            r"  \makeframe{Timetable -- This Week}"]

        for day in range(5):
            # 0 = 周一, 1 = 周二, ... , 4 = 周五.
            # 除周一外其余天前需要加 \newday 标记
            if day != 0:
                latex_output.append(r"  \newday % Day " + str(day))

            day_courses = self.week_courses[day]
            color_index = 0  # 从 H1 开始循环分配颜色, 直到 H9
            for c in day_courses:
                col = colors[color_index % len(colors)]
                color_index += 1
                teacher_str = c['teacher']

                # 暂不添加周次信息, 本 API 对周次的适配较为繁琐
                week_info = " "

                # 添加课程行, 示例输出: \course{H1}{3}{5}{概率论与数理统计}{教书院 219}{巩俊卿}{Week 1}
                # Warning: 请勿分行, 可能存在换行符导致 LateX 编译错误.
                latex_output.append(
                    f"\\course{{{col}}}{{{c['start_slot']}}}{{{c['end_slot']}}}{{{c['course_name']}}}{{{c['location']}}}{{{teacher_str}}}{{{week_info}}}"
                )

        latex_output.append(r"\end{tikzpicture}")
        latex_output.append(r"")
        latex_output.append(r"\end{document}")

        with open(self.file_name, "w", encoding="utf-8") as f:
            f.write("\n".join(latex_output))
            logging.info(f"The Latex file has been generated: {self.file_name}")

    def compile_latex(self):
        os.system(f"xelatex -interaction=nonstopmode {self.file_name}")
        temp_files = [f"{self.file_prefix}.aux", f"{self.file_prefix}.log", f"{self.file_prefix}.out", f"{self.file_prefix}.tex"]

        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logging.info(f"Temporary file {temp_file} has been deleted.")
