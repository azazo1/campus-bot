"""
研修间预约

Tips:
    在研修间预约系统中, 几乎全部请求 url 都是只需要 cookie 中的 ic-cookie 字段即可提交.

Urls:

"""

import json
import os
import requests
from requests import Response
from typing import Optional, Union
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire.webdriver import Edge

from src.log import project_logger
from src.uia.login import LoginError


class StudyRoomCache:
    """StudyRoom 的登录缓存"""

    def __init__(self, cookies: dict):
        """
        :param cookies: studyroom.ecnu.edu.cn 登录后获取的 cookies.
        """
        self.cookies = cookies.copy()

    def __repr__(self):
        cookies_display = {k: v for k, v in self.cookies.items()}
        return f"StudyRoomCache(cookies={cookies_display})"

    @classmethod
    def grab_from_driver(cls, driver: Edge, timeout: float = 60) -> 'StudyRoomCache':
        """从 WebDriver 中获取 StudyRoomCache, 需要 driver 处于 ECNU 登录状态"""
        driver.get("https://studyroom.ecnu.edu.cn")
        project_logger.debug("StudyRoom site waiting for page loading...")

        # 等待 StudyRoom 页面加载完成.
        WebDriverWait(driver, timeout).until(
            EC.url_matches("https://studyroom.ecnu.edu.cn/#/ic/home")
        )

        # 提取 Cookies
        cookies = {}
        for cookie in driver.get_cookies():
            cookies[cookie["name"]] = cookie["value"]

        project_logger.info("got StudyRoom login cache.")
        project_logger.debug(f"cookies: {cookies}")  # Todo: To delete
        return cls(cookies)


class Request:

    def __init__(self, cache: 'StudyRoomCache'):
        if not isinstance(cache, StudyRoomCache):
            raise ValueError("cache must be an instance of StudyRoomCache.")
        self.cache = cache

    @classmethod
    def check_login_and_extract_data(
            cls, response: Response,
            expected_code: int = 0,
    ) -> Union[dict, list]:
        """
        进行返回内容的一系列检查，并对表示错误的返回值以报错或日志的形式呈现。

        Parameters:
            response: 请求的返回内容.
            expected_code: 返回内容 json 结构中的 "code" 字段.

        Raises:
            LoginError: 登录失效及请求错误.

        Returns:
            如果执行正常，返回请求回应中的 json 结构。

        Tips:
            当用户在手机端登录 StudyRoom 后，电脑端的 StudyRoom-Login-Cache 会失效。
            故若出现 10001 时，先删除当前 StudyRoom-Login-Cache，以便后续重新获取。
        """

        def delete_pickle_file(file_path: str):
            """
            删除指定的 pickle 文件。
            """
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    project_logger.info(f"Successfully removed cache file: {file_path}")
                except Exception as e:
                    project_logger.error(f"Failed to remove cache file: {file_path}. Error: {e}")
            else:
                project_logger.error(f"No such file or directory: {file_path}")

        if response.status_code != 200:
            raise LoginError(f"Response status code: {response.status_code}.")
        if "json" not in response.headers.get("content-type", ""):
            raise LoginError("Request was redirected, which means you didn't login.")
        try:
            ret = response.json()
        except json.JSONDecodeError:
            raise LoginError("Failed to decode JSON response.")

        if ret.get("code") != expected_code:
            # 如果返回的 code 是 300
            if ret.get("code") == 300:
                delete_pickle_file("studyroom-login-cache.pickle")
            raise LoginError(f"Result code: {ret.get('code')}, {ret}.")
        return ret

    def post(self, url: str, headers: Optional[dict] = None, json_payload: Optional[dict] = None) -> Response:
        """
        提交 POST 请求并自动附加必要的内容。

        headers:
            Cookie: ...
            Content-Type: application/json

        payload(json): 根据需要传递的数据。

        :param url: 请求的 URL.
        :param headers: 额外的请求头.
        :param json_payload: 请求的 JSON 数据.
        :return: requests.Response 对象.
        """
        headers_ = {}
        if headers:
            headers_.update(headers)
        else:
            headers_['Content-Type'] = 'application/json'

        # 如果 'ic-cookie' 存在于 cookies 中，则添加到请求头
        ic_cookie = self.cache.cookies.get('ic-cookie')
        if ic_cookie:
            headers_['Cookie'] = f"ic-cookie={ic_cookie}"

        return requests.post(
            url,
            headers=headers_,
            json=json_payload,
            cookies=self.cache.cookies,
        )

    def get(self, url: str, headers: Optional[dict] = None) -> Response:
        """
        提交 GET 请求读取内容。

        headers:
            Cookie: ...

        :param url: 请求的 URL.
        :param headers: 额外的请求头.
        :return: requests.Response 对象.
        """
        headers_ = {}
        if headers:
            headers_.update(headers)

        # 如果 'ic-cookie' 存在于 cookies 中，则添加到请求头
        ic_cookie = self.cache.cookies.get('ic-cookie')
        if ic_cookie:
            headers_['Cookie'] = f"ic-cookie={ic_cookie}"

        return requests.get(
            url,
            headers=headers_,
            cookies=self.cache.cookies,
        )
