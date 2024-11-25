from src.config import init
from src.wechat.open import Wechat


def main():
    init()
    wechat = Wechat()
    wechat.show_main_window()
    wechat.locate_search_box()
    wechat.click_search_box()
    wechat.content_enter("WechatTest")
    wechat.content_enter("Send A Test Message Successfully!")

if __name__ == '__main__':
    main()
