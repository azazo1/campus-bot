import os
import pickle
from src.config import init
from src.library.login import get_login_cache
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
    print(most_free_seats)
    storey = qs.get_by_id(int(most_free_seats["parentId"]))
    print(storey)
    premises = qs.get_by_id(int(storey["parentId"]))
    print(premises)
    print(qs.get_premises_of(id_))
    print(qs.get_premises_of(21))


def query_date(q: LibraryQuery):
    qs = q.quick_select()
    id_ = qs.get_most_free_seats_area()
    days = q.query_date(id_)
    print(days)


def main():
    init()
    login_cache = load_cache()
    q = LibraryQuery(login_cache)
    # quick_select(q)
    query_date(q)


if __name__ == '__main__':
    main()
