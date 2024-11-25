from src.config import init
from src.wechat.open import Wechat
from pywinauto.keyboard import send_keys


def main():
    init()
    wechat = Wechat()
    wechat.show_main_window()
    wechat.locate_search_box()
    wechat.click_search_box()
    wechat.content_enter("WechatTest")
    wechat._copy_image_to_clipboard("assets/ecnu_logo.png")
    send_keys("^v")
    send_keys("{ENTER}")


def main2():
    init()
    wechat = Wechat()
    wechat.send_file("WechatTest", "assets/smtp_open.jpg")


if __name__ == '__main__':
    # main()
    main2()
