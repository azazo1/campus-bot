from src.config import init
from src.wechat.open import Wechat


def main():
    init()
    wechat = Wechat()
    wechat.show_main_window()
    wechat.show_identifiers()
    wechat.locate_search_box()

if __name__ == '__main__':
    main()
