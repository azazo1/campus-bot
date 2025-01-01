import asyncio
import threading
import time
import traceback
from pathlib import Path
from typing import Awaitable, Callable

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire.webdriver import Edge
from websockets import connect

from src.plugin import register_plugin, PluginConfig, TextItem, Routine, Plugin, PluginContext
from src.plugin.config import PasswordItem, NumberItem
from .client import GuardClient

get_room_info_py = Path(__file__).parent / "get_room_info.py"
visualize_degree_py = Path(__file__).parent / "visualize_degree.py"

PLUGIN_NAME = "query_electric_bill_client"


def byte_len_eq(expected_len: int, accept_empty=False):
    def j(s: str):
        try:
            return (accept_empty and len(s) == 0) or len(s.encode("utf-8")) == expected_len
        except (UnicodeEncodeError, AttributeError):
            return False

    return j


class EPayCache:
    def __init__(self, x_csrf_token: str, cookies: dict):
        self.x_csrf_token = x_csrf_token
        self.cookies = cookies

    def __repr__(self):
        return f"EPayCache(...)"


def grabber(driver: Edge) -> EPayCache:
    driver.get(
        "https://epay.ecnu.edu.cn/epaycas/electric/load4electricbill?elcsysid=1"
    )  # 这个网址可能会重定向至登录界面, 但是 plugin loader 应该已经处理好了.
    time.sleep(1)
    WebDriverWait(driver, timeout=60 * 60).until(
        EC.url_matches(r'https://epay.ecnu.edu.cn')  # 等待重定向.
    )
    j_session_id = driver.get_cookie("JSESSIONID")['value']
    cookie = driver.get_cookie("cookie")['value']
    # 在 main frame 中以获取 x_csrf_token.
    meta = driver.find_element(By.XPATH, "/html/head/meta[4]")
    x_csrf_token = meta.get_property("content")
    return EPayCache(
        x_csrf_token=x_csrf_token,
        cookies={
            "JSESSIONID": j_session_id,
            "cookie": cookie
        }
    )


@register_plugin(
    name=PLUGIN_NAME,
    description="宿舍电量自动查询插件, 需要和 GitHub 仓库 https://github.com/azazo1/ECNUQueryElectricBill 配套的服务器共同使用.\n\n"
                "`检查与服务器的连接`: 可以通过检查服务器连接情况来检查当前配置是否正确\n"
                "`可视化电量使用情况`: 可以视化宿舍电量随时间的变化\n"
                "`获取宿舍信息`: 启动单独的应用来获得宿舍配置 1, 2, 3 填写内容",
    configuration=PluginConfig()
    .add(TextItem("server_address", "127.0.0.1:30530",
                  "query degree 服务器套接字地址"))
    .add(PasswordItem("key", "",
                      "和 query degree 服务器通信的加密密钥, utf-8 编码后必须 32 个字节",
                      byte_len_eq(32, True)))
    .add(PasswordItem("iv", "",
                      "和 query degree 服务器通信的初始化向量, utf-8 编码后必须 16 个字节",
                      byte_len_eq(16, True)))
    .add(NumberItem("alert_degree", 10, "警告电量, 当宿舍电量低于指定电量的时候发出邮件提醒",
                    lambda a: 0 <= a))
    .add(TextItem("elcbuis", "", f"宿舍配置 1"))
    .add(NumberItem("elcarea", -1, "宿舍配置 2"))
    .add(TextItem("room_no", "", "宿舍配置 3"))
    # todo visualize_degree.py get_room_info.py 集成到主窗口, 提供注册一个页面功能
    # todo 插件 description 字段
    ,
    routine=Routine.MINUTELY,
    ecnu_cache_grabber=grabber
)
class QueryBillClientPlugin(Plugin):
    def __init__(self):
        self.epay_cache: EPayCache | None = None
        self.iv: bytes | None = None
        self.key: bytes | None = None
        self.elcbuis: str | None = None
        self.room_no: str | None = None
        self.elcarea: int | None = None
        self.alert_degree: int | None = None
        self.server_address: str | None = None
        self.ctx: PluginContext | None = None
        self.degree = -4  # -4 表示未初始化, degree 表示 self.fetch_degree 的返回值
        self.notified = False  # 是否发送了提醒

    @property
    def prev_degree(self):
        try:
            return self.ctx.get_cache().get("prev_degree")
        except KeyError:
            return -1

    @prev_degree.setter
    def prev_degree(self, value):
        self.ctx.get_cache().set("prev_degree", value)

    def on_load(self, ctx: PluginContext):
        self.ctx = ctx

    def async_client(self, job: Callable[[GuardClient], Awaitable]):
        async def j():
            async with connect(f"ws://{self.server_address}/") as client:
                return await job(GuardClient(client, self.key, self.iv, self.ctx.get_logger()))

        return asyncio.run(j())

    def post_room(self):
        dic = dict(roomNo=self.room_no, elcarea=self.elcarea, elcbuis=self.elcbuis)
        self.ctx.get_logger().info("posting room: {}.".format(dic))

        def parallel():
            try:
                self.async_client(lambda client: client.post_room(**dic))
            except Exception as e:
                self.ctx.get_logger().error((type(e), e))

        threading.Thread(target=parallel).start()

    def fetch_degree(self) -> None:
        def parallel():
            try:
                self.degree = self.async_client(lambda client: client.fetch_degree())
            except Exception:
                self.degree = -3

        threading.Thread(target=parallel).start()

    def post_token(self):
        def pt(client: GuardClient):
            return client.post_token(self.epay_cache.x_csrf_token, self.epay_cache.cookies)

        self.async_client(pt)

    def on_uia_login(self, ctx: PluginContext):
        self.epay_cache = ctx.get_uia_cache().get_cache(EPayCache)
        self.post_token()

    def on_config_load(self, ctx: PluginContext, cfg: PluginConfig):
        self.key = cfg.get_item("key").current_value.encode("utf-8")
        self.iv = cfg.get_item("iv").current_value.encode("utf-8")
        self.room_no = cfg.get_item("room_no").current_value
        self.elcbuis = cfg.get_item("elcbuis").current_value
        self.elcarea = cfg.get_item("elcarea").current_value
        self.alert_degree = cfg.get_item("alert_degree").current_value
        self.server_address = cfg.get_item("server_address").current_value

        if self.elcbuis and self.elcarea > 0 and self.room_no:
            self.ctx = ctx
            self.post_room()

    def on_config_save(self, ctx: PluginContext, cfg: PluginConfig):
        self.on_config_load(ctx, cfg)

    def alert(self, title: str, text: str):
        self.ctx.send_message("email_notifier", (title, text))

    def on_routine(self, ctx: PluginContext):
        self.fetch_degree()  # 这个函数的输出值 self.degree 不是立即生效的, 但是这里的时序并不重要
        if self.degree == -1:
            ctx.report_cache_invalid()
        elif self.degree == -2:
            ctx.get_logger().warning("room info missing")
        elif self.degree == -3:
            ctx.get_logger().warning("communicating with server failed")
        elif self.degree >= 0:
            ctx.get_logger().info(f"{self.degree=}.")
            if self.degree < self.alert_degree:
                self.alert(
                    title="电量不足",
                    text=f"电量剩余: {self.degree}, 请及时进行电量的充值, 以防止意外断电的情况"
                )
                self.notified = True
            else:
                self.notified = False

            if self.degree > self.prev_degree > 0:  # prev_degree < 0 为特殊情况.
                self.alert(
                    title="电量充值",
                    text=f"检测到电量增加: 增加度数为 {self.degree - self.prev_degree:.2f}"
                )
            self.prev_degree = self.degree
