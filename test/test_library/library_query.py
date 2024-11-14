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


def query_area():
    init()
    login_cache = load_cache()
    r = LibraryQuery(login_cache).query_area()
    id_ = r.get_most_free_seats_area()
    most_free_seats = r.get_by_id(id_)
    print(most_free_seats)
    storey = r.get_by_id(int(most_free_seats["parentId"]))
    print(storey)
    premises = r.get_by_id(int(storey["parentId"]))
    print(premises)
    print(r.get_premises_of(id_))
    print(r.get_premises_of(21))


if __name__ == '__main__':
    query_area()
