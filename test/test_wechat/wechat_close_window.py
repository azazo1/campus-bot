import time
from src.config import init
from src.wechat.open import Wechat


def main():
    init()
    wechat = Wechat()
    wechat.close_main_window()

if __name__ == '__main__':
    main()
