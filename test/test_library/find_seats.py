import os
import pickle

from src.config import init, logger
from src.uia.login import get_login_cache
from src.library.query import LibraryQuery
from src.library.seat import SeatFinder

LOGIN_CACHE_FILE = "login-cache.pickle"


def load_cache():
    if os.path.exists(LOGIN_CACHE_FILE):
        with open(LOGIN_CACHE_FILE, "rb") as f:
            login_cache = pickle.load(f)
    else:
        login_cache = get_login_cache()
        with open(LOGIN_CACHE_FILE, "wb") as f:
            pickle.dump(login_cache, f)
    return login_cache


def main():
    init()
    login_cache = load_cache()
    q = LibraryQuery(login_cache)
    qs = q.quick_select()
    area_id = qs.get_most_free_seats_area(filter_func=lambda id_: "中文理科图书借阅" in qs.get_by_id(id_)["name"])
    t = q.query_date(area_id)[0].times[0]
    logger.info(f"area name: {qs.get_by_id(area_id)['nameMerge']}, timeperiod: {t}")
    seats = q.query_seats(area_id, t)
    sf = SeatFinder(seats)
    logger.info(sf.find_most_isolated())


if __name__ == '__main__':
    main()
