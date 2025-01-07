import base64
import unittest
from io import BytesIO

from pyzbar import pyzbar
from PIL import Image

from .query import LibCache, LibraryQuery
from .seat import SeatFinder


class Tests(unittest.TestCase):
    def setUp(self):
        from src.log import init, project_logger
        from plugins.library.subscribe import Subscribe
        from src.uia.login import get_login_cache
        init()
        self.project_logger = project_logger
        self.cache = get_login_cache((LibCache.grab_from_driver,))
        self.q = LibraryQuery(self.cache.get_cache(LibCache))
        self.s = Subscribe(self.cache.get_cache(LibCache))

    def test_confirm_subscribe(self):
        """成功运行此测试后, 请检查自己的图书馆内的预约, 及时取消防止造成违规"""
        qs = self.q.quick_select()
        area_id = qs.get_area_by(
            lambda area: "一楼D区自习区" in area["nameMerge"]
        )
        day = self.q.query_time(area_id)[-1]  # 获取次日的日期以进行测试预约, 次日日期的预约取消没有限制.
        time_period = day.times[-1]
        sf = SeatFinder(self.q.query_seats(area_id, time_period))
        seat_id = sf.find_most_isolated().id
        rst = self.s.confirm(seat_id, time_period)
        self.project_logger.info(rst)
        return rst

    def test_query_subscribes(self):
        self.project_logger.info(self.s.query_subscribes())

    def test_cancel(self):
        rst = self.test_confirm_subscribe()
        self.s.cancel(rst["id"])

    def test_find_most_isolate_seat(self):
        q = LibraryQuery(self.cache.get_cache(LibCache))
        qs = q.quick_select()
        area_id = qs.get_most_free_seats_area(
            filter_func=lambda area: "中文理科图书借阅" in area["name"])
        t = q.query_time(area_id)[0].times[0]
        self.project_logger.info(f"area name: {qs.get_by_id(area_id)['nameMerge']}, timeperiod: {t}")
        seats = q.query_seats(area_id, t)
        sf = SeatFinder(seats)
        self.project_logger.info(sf.find_most_isolated())

    def test_quick_select(self):
        qs = self.q.quick_select()
        id_ = qs.get_most_free_seats_area()
        most_free_seats = qs.get_by_id(id_)
        self.project_logger.info(most_free_seats)
        storey = qs.get_by_id(int(most_free_seats["parentId"]))
        self.project_logger.info(storey)
        premises = qs.get_by_id(int(storey["parentId"]))
        self.project_logger.info(premises)
        self.project_logger.info(qs.get_premises_of(id_))
        self.project_logger.info(qs.get_premises_of(21))

    def test_query_date(self):
        qs = self.q.quick_select()
        id_ = qs.get_most_free_seats_area()
        days = self.q.query_time(id_)
        self.project_logger.info(days)

    def test_query_seats(self):
        qs = self.q.quick_select()
        id_ = qs.get_most_free_seats_area()
        days = self.q.query_time(id_)
        ret = self.q.query_seats(id_, days[0].times[0])
        self.project_logger.info(ret)

    def test_display_qrcode(self):
        with open("assets/development-references/login_qrcode_base64.txt", 'r') as f:
            base64_data = f.read().split(',')[1]
        base64_data = base64.b64decode(base64_data)
        img = Image.open(BytesIO(base64_data))
        img.show()

    def test_decode_qrcode(self):
        with open("assets/development-references/login_qrcode_base64.txt", 'r') as f:
            base64_data = f.read().split(',')[1]
        base64_data = base64.b64decode(base64_data)
        img = Image.open(BytesIO(base64_data))
        content = pyzbar.decode(img)
        self.project_logger.info(content[0].data)
