import os
import pickle
from src.config import init, logger
from src.uia.login import get_login_cache
from src.library.query import LibraryQuery

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


def quick_select(q: LibraryQuery):
    qs = q.quick_select()
    id_ = qs.get_most_free_seats_area()
    most_free_seats = qs.get_by_id(id_)
    logger.info(most_free_seats)
    storey = qs.get_by_id(int(most_free_seats["parentId"]))
    logger.info(storey)
    premises = qs.get_by_id(int(storey["parentId"]))
    logger.info(premises)
    logger.info(qs.get_premises_of(id_))
    logger.info(qs.get_premises_of(21))


def query_date(q: LibraryQuery):
    qs = q.quick_select()
    id_ = qs.get_most_free_seats_area()
    days = q.query_date(id_)
    logger.info(days)


def query_seats(q: LibraryQuery):
    qs = q.quick_select()
    id_ = qs.get_most_free_seats_area()
    days = q.query_date(id_)
    ret = q.query_seats(id_, days[0].times[0])
    logger.info(ret)


def main():
    init()
    login_cache = load_cache()
    q = LibraryQuery(login_cache)
    # quick_select(q)
    # query_date(q)
    query_seats(q)


if __name__ == '__main__':
    main()
