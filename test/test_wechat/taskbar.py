from src.config import init
from src.wechat.open import Wechat


def main():
    init()
    wechat = Wechat()
    wechat.click_taskbar_icon()

if __name__ == '__main__':
    main()
