import datetime
from typing import List, Dict, Any

from src.log import project_logger


def process_reservation_data_in_roomInfo(data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    处理预约数据, 返回包含 devId, devName, resvInfos 和 availableInfos 的列表.

    Warning: 本函数只用于适配 query_room_infos(self) -> Optional[List[dict]] 返回的信息.

    Parameters:
        data: 原始预约数据字典.
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
    project_logger.info(f"当前时间: {now}")

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

    project_logger.info(f"查询日期: {target_date} (is_today={is_today})")

    for room in data:
        # 提取基本字段
        room_id = room.get('roomId')
        dev_id = room.get('devId')
        room_name = room.get('roomName')
        kind_id = room.get('kindId')
        lab_name = room.get('labName')

        project_logger.info(f"处理房间: {room_name} (roomId={room_id})")

        # 提取开放时间
        open_times = room.get('openTimes', [])
        parsed_open_times = []
        for ot in open_times:
            open_start_str = f"{target_date} {ot.get('openStartTime')}"
            open_end_str = f"{target_date} {ot.get('openEndTime')}"
            try:
                open_start = datetime.datetime.strptime(open_start_str, "%Y-%m-%d %H:%M")
                open_end = datetime.datetime.strptime(open_end_str, "%Y-%m-%d %H:%M")
                project_logger.info(f"  开放时间段: {open_start} - {open_end}")

                # 如果查询的是今天，需要排除已经过去的时间段
                if is_today:
                    if open_end <= now:
                        project_logger.info(f"    该开放时间段已全部过去，跳过")
                        # 整个开放时间已过，无可用时间
                        continue
                    elif open_start <= now < open_end:
                        project_logger.info(f"    当前时间位于开放时间内，调整开放开始时间为当前时间: {now}")
                        # 当前时间位于开放时间内，将 open_start 调整为当前时间
                        open_start = now

                # 添加到解析后的开放时间列表
                if open_start < open_end:
                    parsed_open_times.append((open_start, open_end))
                    project_logger.info(f"    添加到解析后的开放时间列表: {open_start} - {open_end}")
                else:
                    project_logger.info(f"    开放开始时间 >= 结束时间，跳过")
            except ValueError as ve:
                project_logger.info(f"    无效的开放时间格式: {ve}")
                # 跳过格式错误的开放时间
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
                            project_logger.info(f"    已有预约: {formatted_start_time} - {formatted_end_time}")
                        else:
                            project_logger.info(f"    预约日期不匹配，跳过: {formatted_start_time} - {formatted_end_time}")
                except (ValueError, OSError) as e:
                    project_logger.info(f"    无效的预约时间格式: {e}")
                    # 跳过无效的时间
                    continue
            else:
                # 如果缺少时间， append None
                formatted_resv_infos.append({
                    "startTime": formatted_start_time,
                    "endTime": formatted_end_time
                })
                project_logger.info(f"    预约时间缺失，添加 None")

        # 按预约开始时间排序
        booked_intervals.sort(key=lambda x: x[0])

        # 获取最小预约时间
        resv_rule = room.get('resvRule', {})
        min_resv_time = resv_rule.get('minResvTime', 60)  # 默认为60分钟
        project_logger.info(f"  最小预约时间: {min_resv_time} 分钟")

        # 计算可预约时间段
        available_infos = []

        for open_start, open_end in parsed_open_times:
            current_start = open_start
            project_logger.info(f"  处理开放时间段: {open_start} - {open_end}")
            for resv_start, resv_end in booked_intervals:
                # 如果预约时间段与开放时间段无重叠，跳过
                if resv_start >= open_end or resv_end <= current_start:
                    project_logger.info(f"    预约 {resv_start} - {resv_end} 与开放时间段无重叠，跳过")
                    continue

                # 获取重叠部分
                resv_start_clamped = max(resv_start, current_start)
                resv_end_clamped = min(resv_end, open_end)
                project_logger.info(f"    预约重叠部分: {resv_start_clamped} - {resv_end_clamped}")

                # 检查 current_start 与 resv_start_clamped 之间的空隙
                if resv_start_clamped > current_start:
                    available_duration = (resv_start_clamped - current_start).total_seconds() / 60
                    project_logger.info(f"      可预约时长: {available_duration} 分钟")
                    if available_duration >= min_resv_time:
                        available_infos.append({
                            "availableBeginTime": current_start.strftime("%Y-%m-%d %H:%M:%S"),
                            "availableEndTime": resv_start_clamped.strftime("%Y-%m-%d %H:%M:%S")
                        })
                        project_logger.info(f"      添加可预约时间段: {current_start} - {resv_start_clamped}")

                # 更新 current_start
                current_start = max(current_start, resv_end_clamped)
                project_logger.info(f"      更新当前开始时间为: {current_start}")

            # 检查开放时间结束后的空隙
            if current_start < open_end:
                available_duration = (open_end - current_start).total_seconds() / 60
                project_logger.info(f"    开放时间结束后可预约时长: {available_duration} 分钟")
                if available_duration >= min_resv_time:
                    available_infos.append({
                        "availableBeginTime": current_start.strftime("%Y-%m-%d %H:%M:%S"),
                        "availableEndTime": open_end.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    project_logger.info(f"      添加可预约时间段: {current_start} - {open_end}")

        # 如果没有预约，则整个开放时间段都是空闲的
        if not booked_intervals:
            for open_start, open_end in parsed_open_times:
                available_duration = (open_end - open_start).total_seconds() / 60
                project_logger.info(f"  无预约时，开放时间段可预约时长: {available_duration} 分钟")
                if available_duration >= min_resv_time:
                    available_infos.append({
                        "availableBeginTime": open_start.strftime("%Y-%m-%d %H:%M:%S"),
                        "availableEndTime": open_end.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    project_logger.info(f"    添加可预约时间段: {open_start} - {open_end}")

        # 移除重复的 availableInfos
        unique_available_infos = []
        seen = set()
        for info in available_infos:
            key = (info['availableBeginTime'], info['availableEndTime'])
            if key not in seen:
                seen.add(key)
                unique_available_infos.append(info)
        project_logger.info(f"  可预约时间段: {unique_available_infos}")
        project_logger.info(f" ")

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
