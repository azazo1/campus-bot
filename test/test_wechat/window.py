from src.config import init
from src.wechat.open import Wechat


def main():
    init()
    wechat = Wechat()
    PID = wechat.GetWeChatPID('WeChat.exe')
    wechat.show_main_window(PID)
    # wechat.close_main_window(PID)
    # wechat.click_taskbar_icon()
    # wechat.close_window()

if __name__ == '__main__':
    main()
