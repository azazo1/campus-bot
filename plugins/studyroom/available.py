import datetime
from typing import List, Dict, Any


def process_reservation_data_in_roomAvailable(
        data: List[Dict[str, Any]],
        query_date: str = "today",
        filter_available_only: bool = False
) -> List[Dict[str, Any]]:
    """
    整理房间预约数据, 并分析可预约的时间段.

    Warning:
        本函数只用于适配 query_rooms_available(self, day: str = "today") -> Optional[List[dict]] 返回的信息.
        对于接口为: https://studyroom.ecnu.edu.cn/ic-web/roomDevice/roomAvailable

    Parameters:
        data (List[Dict[str, Any]]): 输入的房间数据列表.
        query_date (str): 查询日期, 可以是 "today" 或 "tomorrow".
        filter_available_only (bool): 如果为 True，只返回 availableInfos 不为空的房间. 其缺省值为 False.

        示例输入 (仅保留有效字段):
             {'addServices': None,
              'devId': 3676574,
              'devName': '普陀校区单人间C428',
              'kindId': 3675133,
              'kindName': '普陀研究室（木门）',
              'labId': 3674920,
              'labName': '普陀校区图书馆四楼',
              'openStart': '08:00',
              'openTimes': [{'openEndTime': '22:00',
                             'openLimit': 1,
                             'openStartTime': '08:00'}],
              'resvInfo': [{'devId': 3676574,
                            'endTime': 1735308000000,
                            'logonName': '1*********4',
                            'startTime': 1735293600000,
                            'title': '学',
                            'trueName': '苏*涵',
                            'uuid': 'dca7c10b275b4e33a40741e033d7b3f0'},
                           {'devId': 3676574,
                            'endTime': 1735275600000,
                            'logonName': '1*********1',
                            'startTime': 1735266000000,
                            'title': '自习',
                            'trueName': '杨*晨',
                            'uuid': '3f4f52fef1c04e7aba76160a439a6c89'}],
              'roomId': 3676573,
              'roomName': '普陀校区单人间C428'},

    Return:
        List[Dict[str, Any]]: 整理后的房间信息列表, 包含可预约的时间段.
        Example:
            {'availableInfos':
            [{'availableBeginTime': '2024-12-27 08:00:00','availableEndTime': '2024-12-27 10:20:00'},
             {'availableBeginTime': '2024-12-27 13:00:00','availableEndTime': '2024-12-27 18:00:00'}],
              'kindId': 3675133,
              'labName': '普陀校区图书馆四楼',
              'openTimes': [{'openEndTime': '22:00', 'openStartTime': '08:00'}],
              'resvInfo':
              [{'endTime': '2024-12-27 22:00:00','startTime': '2024-12-27 18:00:00'},
               {'endTime': '2024-12-27 13:00:00','startTime': '2024-12-27 10:20:00'}],
                'roomId': 3676573,
                'roomName': '普陀校区单人间C428'},
    """
    result = []

    # 获取当前时间
    now = datetime.datetime.now()

    # 计算目标日期
    if query_date == "today":
        target_date = now.strftime("%Y-%m-%d")
        is_today = True
    elif query_date == "tomorrow":
        tomorrow = now + datetime.timedelta(days=1)
        target_date = tomorrow.strftime("%Y-%m-%d")
        is_today = False
    elif query_date == "day_after_tomorrow":
        day_after_tomorrow = now + datetime.timedelta(days=2)
        target_date = day_after_tomorrow.strftime("%Y-%m-%d")
        is_today = False
    else:
        raise ValueError("query_date 参数必须为 'today' 或 'tomorrow'")

    for room in data:
        # 提取基本字段
        room_id = room.get('roomId')
        dev_id = room.get('devId')
        room_name = room.get('roomName')
        kind_id = room.get('kindId')
        lab_name = room.get('labName')

        # 提取开放时间
        open_times = room.get('openTimes', [])
        parsed_open_times = []
        for ot in open_times:
            open_start_str = f"{target_date} {ot.get('openStartTime')}"
            open_end_str = f"{target_date} {ot.get('openEndTime')}"
            try:
                open_start = datetime.datetime.strptime(open_start_str, "%Y-%m-%d %H:%M")
                open_end = datetime.datetime.strptime(open_end_str, "%Y-%m-%d %H:%M")

                # 如果查询的是今天，需要排除已经过去的时间段
                if is_today:
                    if open_end <= now:
                        # 整个开放时间已过，无可用时间
                        continue
                    elif open_start <= now < open_end:
                        # 当前时间位于开放时间内，将 open_start 调整为当前时间
                        open_start = now

                # 添加到解析后的开放时间列表
                if open_start < open_end:
                    parsed_open_times.append((open_start, open_end))
            except ValueError:
                continue

        # 提取预约信息，并过滤出目标日期的预约
        resv_infos = room.get('resvInfo', [])
        booked_intervals = []
        formatted_resv_infos = []
        for resv in resv_infos:
            start_time = resv.get('startTime')
            end_time = resv.get('endTime')
            formatted_start_time = None
            formatted_end_time = None
            if start_time and end_time:
                try:
                    # 判断 startTime 的类型
                    if isinstance(start_time, int) or isinstance(start_time, float):
                        resv_start = datetime.datetime.fromtimestamp(start_time / 1000)
                        formatted_start_time = resv_start.strftime("%Y-%m-%d %H:%M:%S")
                    elif isinstance(start_time, str):
                        resv_start = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                        formatted_start_time = start_time
                    else:
                        resv_start = None

                    # 判断 endTime 的类型
                    if isinstance(end_time, int) or isinstance(end_time, float):
                        resv_end = datetime.datetime.fromtimestamp(end_time / 1000)
                        formatted_end_time = resv_end.strftime("%Y-%m-%d %H:%M:%S")
                    elif isinstance(end_time, str):
                        resv_end = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                        formatted_end_time = end_time
                    else:
                        resv_end = None

                    if resv_start and resv_end:
                        # 仅添加与目标日期匹配的预约
                        if resv_start.strftime("%Y-%m-%d") == target_date:
                            booked_intervals.append((resv_start, resv_end))
                            formatted_resv_infos.append({
                                "startTime": formatted_start_time,
                                "endTime": formatted_end_time
                            })
                except (ValueError, OSError) as e:
                    # 跳过无效的时间
                    continue
            else:
                # 如果缺少时间， append None
                formatted_resv_infos.append({
                    "startTime": formatted_start_time,
                    "endTime": formatted_end_time
                })

        # 按预约开始时间排序
        booked_intervals.sort(key=lambda x: x[0])

        # 获取最小预约时间
        resv_rule = room.get('resvRule', {})
        min_resv_time = resv_rule.get('minResvTime', 60)  # 默认为60分钟

        # 计算可预约时间段
        available_infos = []

        for open_start, open_end in parsed_open_times:
            current_start = open_start
            for resv_start, resv_end in booked_intervals:
                # 如果预约时间段与开放时间段无重叠，跳过
                if resv_start >= open_end or resv_end <= current_start:
                    continue

                # 获取重叠部分
                resv_start_clamped = max(resv_start, current_start)
                resv_end_clamped = min(resv_end, open_end)

                # 检查 current_start 与 resv_start_clamped 之间的空隙
                if resv_start_clamped > current_start:
                    available_duration = (resv_start_clamped - current_start).total_seconds() / 60
                    if available_duration >= min_resv_time:
                        available_infos.append({
                            "availableBeginTime": current_start.strftime("%Y-%m-%d %H:%M:%S"),
                            "availableEndTime": resv_start_clamped.strftime("%Y-%m-%d %H:%M:%S")
                        })

                # 更新 current_start
                current_start = max(current_start, resv_end_clamped)

            # 检查开放时间结束后的空隙
            if current_start < open_end:
                available_duration = (open_end - current_start).total_seconds() / 60
                if available_duration >= min_resv_time:
                    available_infos.append({
                        "availableBeginTime": current_start.strftime("%Y-%m-%d %H:%M:%S"),
                        "availableEndTime": open_end.strftime("%Y-%m-%d %H:%M:%S")
                    })

        # 如果没有预约，则整个开放时间段都是空闲的
        if not booked_intervals:
            for open_start, open_end in parsed_open_times:
                available_duration = (open_end - open_start).total_seconds() / 60
                if available_duration >= min_resv_time:
                    available_infos.append({
                        "availableBeginTime": open_start.strftime("%Y-%m-%d %H:%M:%S"),
                        "availableEndTime": open_end.strftime("%Y-%m-%d %H:%M:%S")
                    })

        # 移除重复的 availableInfos
        unique_available_infos = []
        seen = set()
        for info in available_infos:
            key = (info['availableBeginTime'], info['availableEndTime'])
            if key not in seen:
                seen.add(key)
                unique_available_infos.append(info)

        # 构建结果字典, 目前有用的字段仅有 devId, roomName, resvInfo, 而 availableInfos 是通过计算得到的.
        room_info = {
            "roomId": room_id,
            "devId": dev_id,
            "roomName": room_name,
            "kindId": kind_id,
            "labName": lab_name,
            "openTimes": [{"openStartTime": ot.get('openStartTime'), "openEndTime": ot.get('openEndTime')} for ot in open_times],
            "resvInfo": formatted_resv_infos,
            "availableInfos": unique_available_infos
        }

        # 如果只需要返回 availableInfos 不为空的房间
        if filter_available_only and not unique_available_infos:
            continue

        result.append(room_info)

    return result


def process_checkResvInfos(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    提取每个预约项中的 testName、uuid 和 resvBeginTime 字段。

    参数:
    data (List[Dict[str, Any]]): 包含预约信息的列表。

    返回:
    List[Dict[str, Any]]: 每个字典包含 testName、uuid 和 resvBeginTime。
    """
    extracted = []
    for item in data:
        test_name = item.get('testName')
        uuid = item.get('uuid')
        resv_begin_time = item.get('resvBeginTime')

        extracted.append({
            'testName': test_name,
            'uuid': uuid,
            'resvBeginTime': resv_begin_time
        })

    return extracted
