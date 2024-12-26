"""
图书馆座位提醒模块.
"""
from __future__ import annotations
import json
import os
import textwrap
from typing import Self

import requests
from requests import Response
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire.webdriver import Edge

from src.log import project_logger
from src.uia.login import LoginError, click_element

# 图书馆网页中左侧的全部展开按钮.
EXPAND_ALL_SPAN = '#SeatScreening > div:nth-child(1) > div.content > div > div.header > div.extend > p > span'
# 图书馆网页中左侧的普陀校区筛选按钮.
PUTUO_DISTRICT_SPAN = '#SeatScreening > div:nth-child(1) > div.content > div > div.filterCon > div > div:nth-child(1) > div.van-collapse-item__wrapper > div > div > div.selectItem > span'


class LibCache:
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

        return f"LibCache(authorization='{auth_display}', cookies={cookies_display})"

    @classmethod
    def grab_from_driver(cls, driver: Edge, timeout: float = 24 * 60) -> Self:
        """从 WebDriver 中获取 LibCache, 需要 driver 处于 ECNU 登录状态"""
        driver.get("https://seat-lib.ecnu.edu.cn/h5/#/SeatScreening/1")  # 进入图书馆选座界面, 网站会自动请求座位列表.
        # 等待图书馆网页加载完成.
        project_logger.debug("library site waiting for page loading...")
        WebDriverWait(driver, timeout).until(
            EC.url_matches("https://seat-lib.ecnu.edu.cn/")
        )
        # 全部展开后按左侧的普陀校区筛选按钮确保网页发送 quickSelect 请求.
        click_element(driver, EXPAND_ALL_SPAN, timeout)
        click_element(driver, PUTUO_DISTRICT_SPAN, timeout)

        req = driver.wait_for_request("quickSelect", 60)
        c = {}
        for cookie in driver.get_cookies():
            c[cookie["name"]] = cookie["value"]
        project_logger.info("got library login cache.")
        return cls(req.headers["authorization"], c)


class Request:
    """
    自动为 library 的请求添加必要的验证参数, 可以通过继承此类或者拥有此类对象来使用

    Examples:
        >>> # 以下代码仅供参考, 无法运行.
        >>> class A(Request):
        ...     def __init__(self, cache: LibCache):
        ...         super().__init__(cache)
        ...     def do_something(self):
        ...         self.post(...)

        >>> r = Request(cache=...)
        ... r.post(...)

    """

    def __init__(self, cache: LibCache):
        self.cache = cache
        if cache is None:
            raise ValueError("cache cannot be None.")

    @classmethod
    def check_login_and_extract_data(
            cls, response: Response,
            expected_code: int = 0,
    ) -> dict | list:
        """
        进行返回内容的一系列检查, 并对表示错误的返回值以报错或日志的形式呈现.

        Parameters:
            response: 请求的返回内容.
            expected_code: 返回内容 json 结构中的 "code" 字段.

        Raises:
            LoginError: 登录失效及请求错误.

        Returns:
            如果执行正常, 返回请求回应中的 json 结构.

        Tips:
            当用户在手机端登录 Lib 后, 电脑端的 Lib-Login-Cache 会失效.
        """

        if response.status_code != 200:
            raise LoginError(f"response status code: {response.status_code}.")
        if "json" not in response.headers["content-type"]:
            raise LoginError("request was redirected, which means you didn't login.")
        ret = json.loads(response.text)
        if ret["code"] != expected_code:
            raise LoginError(f"result code: {ret['code']}, {ret}.")
        return ret

    def post(self, url: str, headers: dict = None, payload: dict = None) -> requests.Response:
        """
        提交 POST 请求并自动附加以下内容:

        headers:
            Authorization: ...
            Content-Type: application/json

        cookies: ...

        payload(json): {
            "authorization": ...,
        }
        """
        headers_ = {"Authorization": self.cache.authorization, "Content-Type": "application/json"}
        if headers is not None:
            headers_.update(headers)
        data_ = {'authorization': self.cache.authorization}
        if payload is not None:
            data_.update(payload)
        return requests.post(
            url,
            headers=headers_,
            json=payload,  # 这里不能选择 data 的形参, 因为 data 形参对应的是 x-www-form-urlencodeed.
            cookies=self.cache.cookies,
        )

    def get(self, url: str):
        """提交 GET 请求读取内容, 此方法未经测试, 可能不符合预期"""
        return requests.get(
            url,
            headers={"Authorization": self.cache.authorization},
            cookies=self.cache.cookies,
        )
