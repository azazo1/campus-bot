"""
ECNU 公用数据库.
"""
import textwrap
from typing import Self

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire.webdriver import Edge

from src.config import project_logger


class PortalCache:
    def __init__(self, authorization: str):
        self.authorization = authorization

    def __repr__(self):
        auth_display = textwrap.shorten(self.authorization, width=10)
        return f"PortalCache(authorization='{auth_display}')"

    @classmethod
    def grab_from_driver(cls, driver: Edge, timeout: float = 24 * 60) -> Self:
        driver.get("https://portal2023.ecnu.edu.cn/portal/home")
        project_logger.debug("portal site waiting for page loading...")
        WebDriverWait(driver, timeout).until(
            EC.url_matches("https://portal2023.ecnu.edu.cn/")
        )
        req = driver.wait_for_request("calendar-new", 60)
        project_logger.info(f"got portal login cache.")
        return cls(req.headers['Authorization'])

