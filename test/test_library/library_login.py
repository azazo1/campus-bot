from src.config import init
from src.library.login import get_login_cache


def main():
    init()
    get_login_cache()


if __name__ == '__main__':
    main()
