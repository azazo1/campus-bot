"""
图书馆座位提醒模块.

todo 研讨间预约, 不要放在 library 下, 放在 studyroom 包, https://studyroom.ecnu.edu.cn/
"""
from __future__ import annotations
import json
import requests
from requests import Response

from src.uia.login import LoginError, LibCache


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
