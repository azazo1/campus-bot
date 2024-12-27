# 研修间模块说明

## 模块结构

```text
ecnu-campus-plugin/
│
├── src/
│   └── studyroom/
│       ├── __init__.py
│       ├── available.py
│       ├── query.py
│       └── reserve.py
├── tests/
│   └── test_studyroom/
│       ├── available.py
│       ├── query.py
│       └── reserve.py
```

### Query (`query.py`)

该模块仅实现对 url 的简单请求, 不作任何数据处理。它通过相应的 API 获取研修室的可用性和详细信息。

**主要类和方法：**

- `StudyRoomQuery(Request)`：一个继承自 `Request` 类的类，提供专门用于查询研修室信息的功能。
  
  - `query_roomInfos() -> Optional[List[dict]]`：获取所有研修室的详细信息。
  
  - `query_roomAvailable(day: str = "today") -> Optional[List[dict]]`：获取指定日期（今天、明天或大后天）的可用研修室信息。
  
  - `query_resvInfo(needStatus: int) -> Optional[List[Dict]]`：查询预约状态，检查研修室是否正在使用或可用。其中：needStatus:
    - 2 代表查询 (未使用) 的研修间.
    - 4 代表查询 (已使用) 的研修间.
    - 6 代表查询 (未使用 + 使用中) 的研修间.
  


### Available (`available.py`)

`available.py` 模块负责处理房间可用性数据。它分析当前和已预订的时间段，确定研修室可预约的时间段。

**主要功能：**

- `process_reservation_data_in_roomInfos(data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]`：处理原始预约数据，并根据开放时间和现有预约提取可用时间段。该函数仅为 `query_roomInfos()` 服务。。
  
- `process_reservation_data_in_roomAvailable(data: List[Dict[str, Any]], query_date: str = "today", filter_available_only: bool = False) -> List[Dict[str, Any]]`：组织和过滤房间可用性数据，识别合适的预约时间段。该函数只为 `query_roomAvailable()` 服务。

### 

### Reserve (`reserve.py`)

`reserve.py` 模块管理预约流程。它包括进行预约、检查预约状态以及在特定条件下自动取消预约的功能。

**主要类和方法：**

- `StudyRoomReserve(Request)`：一个继承自 `Request` 类的类，提供专门用于预约的功能。
  
  - `_fetch_userInfo() -> Optional[dict]`：私有化方法，获取进行预约所需的用户信息。
  
  - `reserve_room(resvBeginTime: str, resvEndTime: str, testName: str, resvDev: list, memo: str = "") -> dict`：为指定时间段和研修室进行预约。

  - `cancel_reservation(reservation_id: int) -> None`: 根据唯一 ID 取消特定的预约。
