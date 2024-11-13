"""
半自动化登录 ecnu 统一认证.
"""
import traceback
from typing import Optional

import textwrap
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire.webdriver import Edge

from src.config import logger, requires_init

# 图书馆网页中左侧的全部展开按钮.
EXPAND_ALL_SPAN = '#SeatScreening > div:nth-child(1) > div.content > div > div.header > div.extend > p > span'
# 图书馆网页中左侧的普陀校区筛选按钮.
PUTUO_DISTRICT_SPAN = '#SeatScreening > div:nth-child(1) > div.content > div > div.filterCon > div > div:nth-child(1) > div.van-collapse-item__wrapper > div > div > div.selectItem > span'


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


@requires_init
def get_login_cache() -> Optional[LoginCache]:
    """
    使用浏览器的进行图书馆的登录操作,
    并获取相应的登录缓存, 以供爬虫部分使用.

    如果登录失败或者超时抑或者是没有检测到 quickSelect 请求, 返回 None.

    quickSelect 请求在此处为查询图书馆座位的请求.
    """
    driver = Edge()
    try:
        driver.maximize_window()
        driver.get("https://seat-lib.ecnu.edu.cn/h5/#/SeatScreening/1")  # 进入图书馆选座界面, 网站会自动请求座位列表.
        # 此时重定向至 ecnu 统一认证界面, 用户登录后返回至 seat-lib.ecnu.edu.cn 域名下.
        # todo 获取 ecnu 统一认证界面的登录二维码并通过邮箱或微信发送给用户.

        logger.info("library site waiting for login...")
        WebDriverWait(driver, 60 * 60 * 24).until(
            EC.url_matches("https://seat-lib.ecnu.edu.cn")
        )
        # 等待图书馆网页加载完成.
        # 全部展开后按左侧的普陀校区筛选按钮确保网页发送 quickSelect 请求.
        logger.debug("library site waiting for page loading...")
        _click_element(driver, EXPAND_ALL_SPAN, 60 * 60 * 24)
        _click_element(driver, PUTUO_DISTRICT_SPAN, 60 * 60 * 24)

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
        return None
