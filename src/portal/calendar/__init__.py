"""
校历查询.
"""
import requests
from requests import Response

from src.portal import PortalCache
from src.uia.login import LoginError


class Request:
    def __init__(self, cache: PortalCache):
        self.cache = cache
        if self.cache is None:
            raise ValueError("cache cannot be None.")

    @classmethod
    def check_login_and_extract_data(cls, response: Response) -> dict:
        """
        进行返回内容的一系列检查, 并对表示错误的返回值以报错或日志的形式呈现.

        Parameters:
            response: requests 请求的返回返回对象.

        Raises:
            LoginError: 登录失效及请求错误.

        Returns:
            如果执行正常, 返回请求回应中的 json 结构 data 字段.
        """
        if response.status_code != 200:
            raise LoginError(f"response status code: {response.status_code}.")
        if "json" not in response.headers["content-type"]:
            raise LoginError("request was redirected, which means you didn't login.")
        ret = response.json()
        if ret.get("data") is None:
            raise LoginError(f"response has no valid data, {ret}.")
        return ret["data"]

    def query(self, query: str, variables: dict,
              headers: dict = None) -> requests.Response:
        """
        向 calendar-new 提交 POST 请求并自动附加以下内容:

        url: https://portal2023.ecnu.edu.cn/bus/graphql/calendar-new

        headers:
            Authorization: ...
            Content-Type: application/json

        payload(GraphQL): {"query": query, "variables": variables}
        """
        headers_ = {"Authorization": self.cache.authorization, "Content-Type": "application/json"}
        if headers is not None:
            headers_.update(headers)
        return requests.post(
            "https://portal2023.ecnu.edu.cn/bus/graphql/calendar-new",
            headers=headers_,
            json={
                "query": query,
                "variables": variables,
            },  # 这里不能选择 data 的形参, 这里使用 GraphQL 传递数据.
        )
