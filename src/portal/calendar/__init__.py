"""
校历查询.
"""
import os

import requests
from requests import Response

from src.log import project_logger
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
            raise LoginError(f"response status code: {response.status_code}.")
        if "json" not in response.headers["content-type"]:
            raise LoginError("request was redirected, which means you didn't login.")
        ret = response.json()

        errors = ret.get("errors", [])
        if ret.get("data") is None:
            # 获取第一个错误的扩展信息
            error_extensions = errors[0].get("extensions", {})
            code = error_extensions.get("code")

            # 检查 code 是否为 "ACCESS_TOKEN_INVALID"
            if code == "ACCESS_TOKEN_INVALID":
                delete_pickle_file("portal-login-cache.pickle")

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
