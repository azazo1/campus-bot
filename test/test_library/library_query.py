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
    print(r)


if __name__ == '__main__':
    query_area()
