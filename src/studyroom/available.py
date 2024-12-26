import datetime
from typing import List, Dict, Any


def process_reservation_data(data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    处理预约数据, 返回包含 devId, devName, resvInfos 和 availableInfos 的列表.

    Warning: 本函数只用于适配 query_room_infos(self) -> Optional[List[dict]] 返回的信息.

    Parameters:
        data 原始预约数据字典.
            字段分析:
                 {'devId': 3676503,                             # 设备 ID
                 'devName': '普陀校区单人间C421',                 # 设备名称
                 'minResvTime': 60,                             # 最小预约时间
                 'openTimes': [{'openEndTime': '22:00',         # 开放结束时间
                                'openLimit': 1,                 # 最少预约人数
                                'openStartTime': '08:00'}],     # 开放开始时间
                 'resvInfos': [{'resvBeginTime': '2024-12-26 '  # (People No.1) 的预约信息
                                                 '17:01:00',
                                'resvEndTime': '2024-12-26 '
                                               '21:01:00',
                                'resvStatus': 1093}]},
                {'devId': 3676511,
                 'devName': '普陀校区单人间C422',
                 'minResvTime': 60,
                 'openTimes': [{'openEndTime': '22:00',
                                'openLimit': 1,
                                'openStartTime': '08:00'}],
                 'resvInfos': [{'resvBeginTime': '2024-12-26 '
                                                 '18:00:00',
                                'resvEndTime': '2024-12-26 '
                                               '22:00:00',
                                'resvStatus': 1093}]},

    Tips:
        1. 将 [openStartTime, currentTime] 区间鉴定为不可用时间段. 例如 18:55 P.M., 只能从 18:55 开始, 后面的时间段才可能可用.
        2. 仅 AvailableTime > minResvTime 时, 才将这段区间设置为 AvailableTime, 如果不超过最小预约时间, 则不予考虑.
        3.

    Return: 处理后的信息字典，包含 'rooms' 键，值为房间信息列表.
        通过程序自动添入 availableInfos 字段.

        Example:
            {'availableInfos': [{'availableBeginTime': '2024-12-26 18:38:48',
                                'availableEndTime': '2024-12-26 20:00:00'}],
            'devId': 3676497,
            'devName': '普陀校区团体间B412',
            'resvInfos': [{'resvBeginTime': '2024-12-26 20:00:00',
                           'resvEndTime': '2024-12-26 22:00:00',
                           'resvStatus': 1027}]},
    """
    result = {"rooms": []}

    # 写死, 本函数只适用查询当日信息
    now = datetime.datetime.now()
    target_date = now.strftime("%Y-%m-%d")

    # 层层进入, 查询 resvInfos 字段
    for campus in data.get('data', []):
        dev_kinds = campus.get('devKinds', [])

        for dev_kind_group in dev_kinds:
            for dev_kind in dev_kind_group:
                room_infos = dev_kind.get('roomInfos', [])

                for room in room_infos:
                    dev_id = room.get('devId')
                    dev_name = room.get('devName')
                    resv_infos = room.get('resvInfos')

                    # 确保 resv_infos 为列表，即使原始值为 None, 因为当没人预约时 resvInfos is None
                    if resv_infos is None:
                        resv_infos = []
                    elif not isinstance(resv_infos, list):
                        resv_infos = [resv_infos]

                    # 提取: 开放时间段
                    open_times = room.get('openTimes', [])
                    open_intervals = []
                    for open_time in open_times:
                        """
                        openTimes 字段中含有 openStartTime 与 openEndTime 字段, 但是格式不规范, 需要手动拼接.
                        
                        Example:
                            'openTimes': [{'openEndTime': '22:00',
                                           'openLimit': 1,
                                           'openStartTime': '08:00'
                                         }],
                        """
                        open_start_str = f"{target_date} {open_time.get('openStartTime')}"
                        open_end_str = f"{target_date} {open_time.get('openEndTime')}"
                        try:
                            # 解析为 datetime 格式, 便于精准的时间对比
                            open_start = datetime.datetime.strptime(open_start_str, "%Y-%m-%d %H:%M")
                            open_end = datetime.datetime.strptime(open_end_str, "%Y-%m-%d %H:%M")

                            # 排除从 open_start 到 now 的时间段
                            if open_end <= now:
                                # 整个开放时间已过，无可用时间
                                continue
                            elif open_start <= now < open_end:
                                # 当前时间位于 open_start 与 open_end 之间, 将 open_start 调整为当前时间, 以便计算空闲时间
                                open_start = now

                            # 如果调整后的 open_start 仍然小于 open_end，添加到 open_intervals
                            if open_start < open_end:
                                open_intervals.append((open_start, open_end))
                        except ValueError:
                            # 跳过格式错误的开放时间
                            continue

                    # 提取并排序预约时间段
                    booked_intervals = []

                    if resv_infos:
                        for resv in resv_infos:
                            """
                            同样地, 此处是将 resvInfos 中的字段提取出来, 解析为 datetime 对象.
                            保存为一个元组列表 booked_intervals.
                            """
                            resv_begin_str = resv.get('resvBeginTime')
                            resv_end_str = resv.get('resvEndTime')
                            if resv_begin_str and resv_end_str:
                                try:
                                    resv_begin = datetime.datetime.strptime(resv_begin_str, "%Y-%m-%d %H:%M:%S")
                                    resv_end = datetime.datetime.strptime(resv_end_str, "%Y-%m-%d %H:%M:%S")
                                    booked_intervals.append((resv_begin, resv_end))
                                except ValueError:
                                    # 跳过格式错误的预约时间
                                    continue

                        # 按开始时间排序
                        booked_intervals.sort(key=lambda x: x[0])

                    # 计算空闲时间
                    available_infos = []
                    min_resv_time = room.get('minResvTime', 0)  # 获取 minResvTime，默认为 0

                    """
                    外层循环: 遍历开放时间段, open_intervals
                    内层循环: 遍历已预约的时间段, booked_intervals
                    """
                    for open_start, open_end in open_intervals:
                        current_start = open_start
                        for resv_start, resv_end in booked_intervals:

                            # 如果已预约的时间段与开放时间段没有重叠，则跳过
                            if resv_start >= open_end or resv_end <= open_start:
                                continue

                            # 将预约时间与开放时间做裁剪，得到它们的重叠部分
                            resv_start_clamped = max(resv_start, open_start)
                            resv_end_clamped = min(resv_end, open_end)

                            """
                            如果当前时间 current_start 与预约时间的起点之间有空隙, 并且这个空隙满足最小预约时长 minResvTime,
                            则记录该空隙为可用时间段.
                            """
                            if resv_start_clamped > current_start:
                                available_duration = (resv_start_clamped - current_start).total_seconds() / 60
                                if available_duration >= min_resv_time:
                                    available_infos.append({
                                        "availableBeginTime": current_start.strftime("%Y-%m-%d %H:%M:%S"),
                                        "availableEndTime": resv_start_clamped.strftime("%Y-%m-%d %H:%M:%S")
                                    })

                            current_start = max(current_start, resv_end_clamped)

                    # 如果没有预约，则整个开放时间段都是空闲的
                    else:
                        for open_start, open_end in open_intervals:
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

                    # 构建结果字典
                    room_info = {
                        "devId": dev_id,
                        "devName": dev_name,
                        "resvInfos": resv_infos,
                        "availableInfos": available_infos
                    }
                    result["rooms"].append(room_info)

    return result
