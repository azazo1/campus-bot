import unittest

from src.log import init, project_logger
from src.studyroom.req import StudyRoomCache
from src.studyroom.available import process_checkResvInfos
from src.studyroom.subscribe import StudyRoomReserve
from src.studyroom.query import StudyRoomQuery
from src.uia.login import get_login_cache


class RoomReserver(unittest.TestCase):
    """测试 StudyRoomReserve 类的功能"""

    def setUp(self):
        init()
        self.cache = get_login_cache((StudyRoomCache.grab_from_driver,))
        self.reserve = StudyRoomReserve(self.cache.get_cache(StudyRoomCache))
        self.query = StudyRoomQuery(self.cache.get_cache(StudyRoomCache))

    def test_auto_reservation(self):
        """
        测试今天预约特定 kindId 的房间，最短预约时间为 60 分钟.

        后天有关的查询需要等到每日 22:00 后.
        """
        self.reserve.submit_reserve("tomorrow", "普陀校区木门研究室", 60)
        # self._perform_reservation("day_after_tomorrow", "闵行校区研究室", 90)
        # self._perform_reservation("tomorrow", "普陀校区玻璃门研究室", 120)

    def test_auto_cancel(self):
        """
        自动取消预约研修间, 用于测试取消预约功能的全自动化.

        Tips:
            本测试会直接遍历所有已预约但未使用的研修间, 直接全部取消.

        该测试应在 test_auto_reservation 后运行.
        """
        # 获取已预约但未使用的研修间
        resv_info = self.query.check_resvInfo(2)
        process_resv_info = process_checkResvInfos(resv_info)
        if not process_resv_info:
            self.fail("没有找到已预约但未使用的研修间。")

        # 遍历所有已预约的研修间并取消预约
        for resv in process_resv_info:
            uuid = resv.get("uuid")

            try:
                response = self.reserve.cancel_reservation(uuid)
                project_logger.info(f"取消预约 (uuid={uuid}) 成功: {response}")
            except Exception as e:
                project_logger.error(f"取消预约 (uuid={uuid}) 时发生异常: {e}")
