"""
半自动化登录 ecnu 统一认证.
"""
import time
import traceback
from typing import Optional, Callable

import textwrap
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire.webdriver import Edge

from src.config import logger, requires_init

# ECNU 统一登陆界面的使用二维码登录按钮.
QRCODE_BUTTON = '#login-content-right > div.codeBrushing.qr'
QRCODE_IMG = '#login-content-right > app-login-auth-panel > div > div.content-top > app-login-by-corp-wechat-qr > div > div > div.qrcodeImgStyle > rg-page-qr-box > div > img'
# 图书馆网页中左侧的全部展开按钮.
EXPAND_ALL_SPAN = '#SeatScreening > div:nth-child(1) > div.content > div > div.header > div.extend > p > span'
# 图书馆网页中左侧的普陀校区筛选按钮.
PUTUO_DISTRICT_SPAN = '#SeatScreening > div:nth-child(1) > div.content > div > div.filterCon > div > div:nth-child(1) > div.van-collapse-item__wrapper > div > div > div.selectItem > span'

EXTRACT_QRCODE_JS = f"""
let qrcode_img = document.querySelector("{QRCODE_IMG}");
let canvas = document.createElement('canvas');
let ctx = canvas.getContext('2d');

canvas.width = qrcode_img.width;
canvas.height = qrcode_img.height;

ctx.drawImage(qrcode_img, 0, 0, canvas.width, canvas.height);
return canvas.toDataURL('image/png');
"""

EXTRACT_QRCODE_SRC_JS = f"""
let qrcode_img = document.querySelector("{QRCODE_IMG}");
return qrcode_img.src;
"""

# title, img, url.
QRCODE_HTML = """<!DOCTYPE html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
<div>Scan the qrcode below to login ECNU.</div>
<img src="{img}" alt="qrcode image here."/>
<div>Or copy this url in wechat:</div>
<div>{url}</div>
</body>
</html>
"""
UPDATED_QRCODE_TITLE = "ECNU Login QRCode Updated"
FIRST_QRCODE_TITLE = "Login to ECNU"


class LoginCache:
    """图书馆 quickSelect api 的必须登录缓存."""

    def __init__(self, authorization: str, cookies: dict):
        """
        :param authorization: 认证字符串.
        :param cookies: seat-lib.ecnu.edu.cn 域名的 cookies, 以 name-value 对储存.
        """
        self.authorization = authorization
        self.cookies = cookies.copy()

    def __repr__(self):
        # 使用安全的方式展示 authorization 和 cookies，避免内容过长或敏感信息暴露
        auth_display = textwrap.shorten(self.authorization, width=10)
        cookies_display = {k: textwrap.shorten(v, 10) for k, v in self.cookies.items()}

        return f"LoginCache(authorization='{auth_display}', cookies={cookies_display})"


def _click_element(driver: Edge, selector: str, timeout: float = 10):
    """
    在 driver 中点击元素, 如果元素不存在, 那么等待一段时间.
    :param driver: driver.
    :param selector: 要点击元素的 css selector.
    :param timeout: 等待元素出现要的时间.
    """
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )
    driver.execute_script(f"""
    let ele = document.querySelector({repr(selector)});
    ele.click();
    """)


def _attribute_changes(css_selector: str, attribute_name: str):
    """
    Expected Conditions 方法.

    一个元素的属性发生变化时触发.

    :param css_selector: 对应元素的 css selector, 如果其包含多个元素, 那么只会取第一个元素.
    :param attribute_name: 要监视的元素属性, 如 <img> 元素的 src 属性.
    """
    prev = None

    def _predicate(driver: EC.WebDriverOrWebElement):
        nonlocal prev
        ele = driver.find_element(By.CSS_SELECTOR, css_selector)
        new = ele.get_attribute(attribute_name)
        if prev is None:
            prev = new
        elif prev != new:
            prev = new
            return True
        return False

    return _predicate


def _wait_qrcode_update_or_login(driver: Edge, timeout: float) -> bool:
    """
    等待用户成功登录或者登录二维码刷新.

    :return: 如果成功登录返回 True, 其他情况返回 False.
    """
    login_url = "https://seat-lib.ecnu.edu.cn"
    WebDriverWait(driver, timeout).until(
        EC.any_of(
            _attribute_changes(QRCODE_IMG, "src"),
            EC.url_matches(login_url),
        )
    )
    return login_url in driver.current_url


def _get_qrcode(driver: Edge, timeout: float) -> tuple[str, str]:
    """
    获取统一登陆界面中的登录二维码.

    :return: (登录二维码的生成网址, 登录二维码 base64 数据(其可直接放入 img 元素的 src 字段))
    """
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, QRCODE_IMG))
    )
    img_base64_data = driver.execute_script(EXTRACT_QRCODE_JS)
    img_src = driver.execute_script(EXTRACT_QRCODE_SRC_JS)
    logger.debug("qrcode base64 data: "
                 + img_base64_data[:min(30, len(img_base64_data))] + "...")
    logger.debug("qrcode src: " + img_src)
    return img_src, img_base64_data


@requires_init
def get_login_cache(
        timeout: float = 24 * 60,
        qrcode_html_callback: Callable[[str, str], None] = lambda s: None
) -> Optional[LoginCache]:
    """
    使用浏览器的进行图书馆的登录操作,
    并获取相应的登录缓存, 以供爬虫部分使用.

    如果登录失败或者超时抑或者是没有检测到 quickSelect 请求, 返回 None.

    quickSelect 请求在此处为查询图书馆座位的请求.

    :param timeout: 在某个操作等待时间超过 timeout 时, 停止等待, 终止登录逻辑.
    :param qrcode_html_callback: 一个函数, 参数 1 为 html 内容的标题, 参数 2 为带有 ECNU 登录二维码的 html 界面, 此函数用于回调提醒用户登录.

    :return: 如果登陆成功, 返回登录缓存; 如果登录失败或超时, 返回 None.
    """
    driver = Edge()
    try:
        driver.maximize_window()
        driver.get("https://seat-lib.ecnu.edu.cn/h5/#/SeatScreening/1")  # 进入图书馆选座界面, 网站会自动请求座位列表.
        # 此时重定向至 ecnu 统一认证界面, 用户登录后返回至 seat-lib.ecnu.edu.cn 域名下.

        # 获取 ecnu 统一认证界面的登录二维码并通过邮箱或微信发送给用户.
        _click_element(driver, QRCODE_BUTTON, timeout)  # 确保二维码显示出来.
        img_src, img_base64_data = _get_qrcode(driver, timeout)
        qrcode_html_callback(FIRST_QRCODE_TITLE,
                             QRCODE_HTML.format(img=img_base64_data, url=img_src, title=FIRST_QRCODE_TITLE))

        logger.info("library site waiting for login...")
        while not _wait_qrcode_update_or_login(driver, timeout):  # 等待用户成功登录或者二维码超时.
            # 二维码超时刷新.
            logger.info("ecnu login qrcode updated.")
            img_src, img_base64_data = _get_qrcode(driver, timeout)
            qrcode_html_callback(UPDATED_QRCODE_TITLE,
                                 QRCODE_HTML.format(img=img_base64_data, url=img_src, title=UPDATED_QRCODE_TITLE))

        # 等待图书馆网页加载完成.
        # 全部展开后按左侧的普陀校区筛选按钮确保网页发送 quickSelect 请求.
        logger.debug("library site waiting for page loading...")
        _click_element(driver, EXPAND_ALL_SPAN, timeout)
        _click_element(driver, PUTUO_DISTRICT_SPAN, timeout)

        # 提取 quickSelect 请求的请求头和 cookies.
        req = driver.wait_for_request("quickSelect", 60)
        c = {}
        for cookie in driver.get_cookies():
            c[cookie["name"]] = cookie["value"]
        logger.info("got library login cache.")
        cache = LoginCache(req.headers["authorization"], c)
        logger.debug(f"login cache: {cache}")
        return cache
    except TimeoutException:
        logger.error(traceback.format_exc())
    finally:
        driver.quit()
    return None
