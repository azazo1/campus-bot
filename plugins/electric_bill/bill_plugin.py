import asyncio
import time
import traceback
from typing import Awaitable, Callable, Self

from PIL.ImageQt import QImage
from PySide6.QtCore import QThreadPool, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, \
    QLineEdit
from matplotlib.backends.backend_agg import FigureCanvasAgg
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire.webdriver import Edge
from websockets import connect

from src.plugin import register_plugin, PluginConfig, TextItem, Routine, Plugin, PluginContext, Task
from src.plugin.config import PasswordItem, NumberItem
from src.uia.login import get_login_cache
from .client import GuardClient
from .visualize_degree import get_figure as generate_bill_figure
from . import visualize_degree

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
        return "EPayCache(...)"

    @classmethod
    def grabber(cls, driver: Edge) -> Self:
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


class DormInfo:
    def __init__(self, elcbuis: str, elcarea: int, room_no: str):
        self.elcbuis = elcbuis
        self.elcarea = elcarea
        self.room_no = room_no

    def __repr__(self):
        return "DormInfo(...)"

    @classmethod
    def grabber(cls, driver: Edge) -> Self:
        driver.get(
            "https://epay.ecnu.edu.cn/epaycas/electric/load4electricbill?elcsysid=1"
        )  # 这个网址会重定向至登录界面.
        # 先等待用户登录.
        time.sleep(1)
        WebDriverWait(driver, timeout=60 * 60).until(
            EC.url_matches(r'https://epay.ecnu.edu.cn')
        )
        # 等待按钮出现, 放置回调函数.
        WebDriverWait(driver, timeout=60 * 60).until(
            EC.presence_of_element_located((By.ID, "queryBill"))
        )
        driver.execute_script("""
                let button = document.querySelector("#queryBill");
                button.onclick = function() {
                    let a = document.createElement("a");
                    a.id = "query_clicked"; // 查询按钮按下时添加新元素, 终结下面的 WebDriverWait.
                    document.body.appendChild(a);
                }
                let h2 = document.querySelector("#inner-headline > div > div > div > h2");
                h2.innerHTML = "请选择你需要查询电费的宿舍信息";
                """)
        WebDriverWait(driver, timeout=60 * 60).until(
            EC.presence_of_element_located((By.ID, "query_clicked"))
        )
        elcbuis = driver.find_element(By.ID, "elcbuis").get_property("value")
        elcarea = driver.find_element(By.ID, "elcarea").get_property("value")
        elcroom = driver.find_element(By.ID, "elcroom").get_property("value")
        return DormInfo(elcbuis=elcbuis, elcarea=int(elcarea), room_no=elcroom)


@register_plugin(
    name=PLUGIN_NAME,
    description="    宿舍电量自动查询插件, 需要和 GitHub 仓库 https://github.com/azazo1/ecnu-query-electric-bill 配套的服务器共同使用.\n"
                "    `检查连接`: 可以通过检查服务器连接情况来检查当前与服务器的配置是否正确\n"
                "    `可视化电量使用情况`: 可以视化宿舍电量随时间的变化\n"
                "    `获取宿舍配置`: 在弹出的浏览器窗口中选择宿舍信息并获得宿舍配置 1, 2, 3 填写内容",
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
    ,
    routine=Routine.MINUTELY,
    ecnu_cache_grabber=EPayCache.grabber
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
        self.notified = False  # 是否发送了提醒

        self._fig_widget = None  # 电量图表窗口
        self._room_info_widget = None  # 宿舍配置消息结果窗口

    @property
    def prev_degree(self):
        try:
            return self.ctx.get_cache().get("prev_degree")
        except KeyError:
            return -1

    @prev_degree.setter
    def prev_degree(self, value):
        self.ctx.get_cache().set("prev_degree", value)

    def check_server(self):
        @Slot(bool)
        def checked_result(rst: bool):
            title = "连接" + ("成功" if rst else "失败")
            text = "与服务器连接" + title
            QMessageBox.information(None, title, text)

        def parallel():
            try:
                self.async_client(lambda cli: cli.fetch_degree())
                return True
            except Exception:
                return False

        task = Task(parallel)
        task.signals.finished.connect(checked_result)
        QThreadPool.globalInstance().start(task)

    def visualize_degree(self):
        @Slot(str)
        def file_arrived(file: str):
            if file == "error":
                QMessageBox.information(None, "发生了错误", "请在日志文件查看详情")
            else:
                # 关闭原有的图表窗口
                if self._fig_widget:
                    self._fig_widget.destroy()
                # 传递配置
                visualize_degree.server_address = self.server_address
                visualize_degree.key = self.key
                visualize_degree.iv = self.iv
                visualize_degree.logger = self.ctx.get_logger()
                # 生成新的图表
                fig = generate_bill_figure()
                canvas = FigureCanvasAgg(fig)
                canvas.draw()
                buf = canvas.buffer_rgba()
                width, height = fig.canvas.get_width_height()
                image = QImage(buf, width, height, QImage.Format_RGBA8888)
                # 显示图表图片
                img_label = QLabel()
                img_label.setPixmap(QPixmap.fromImage(image))
                # 生成新的图表窗口
                self._fig_widget = QWidget()
                self._fig_widget.setWindowTitle("电量使用情况")
                layout = QVBoxLayout()
                layout.addWidget(img_label)
                btn = QPushButton("关闭")
                btn.clicked.connect(self._fig_widget.destroy)
                layout.addWidget(btn)
                self._fig_widget.closeEvent = lambda evt: (evt.ignore(), self._fig_widget.destroy())
                self._fig_widget.setLayout(layout)
                self._fig_widget.show()

        def parallel():
            try:
                return self.async_client(lambda cli: cli.fetch_degree_file())
            except Exception:
                self.ctx.get_logger().error(traceback.format_exc())
                return "error"

        task = Task(parallel)
        task.signals.finished.connect(file_arrived)
        QThreadPool.globalInstance().start(task)

    def ask_for_room(self):
        """在浏览器中获取用户宿舍配置消息, 不能直接调用, 需要在子线程中调用"""
        try:
            dorm_info = get_login_cache((DormInfo.grabber,)).get_cache(DormInfo)
            return {
                "elcbuis": dorm_info.elcbuis,
                "elcarea": dorm_info.elcarea,
                "room_no": dorm_info.room_no,
            }
        except Exception as e:
            self.ctx.get_logger().error(traceback.format_exc())
            return {"错误发生了": str(e)}

    def get_dorm_info(self):
        # noinspection PyTypeChecker
        if QMessageBox.question(
                None,
                "宿舍配置获取",
                "请点击确认按钮, 弹出 Edge 浏览器页面.\n"
                "登录 ECNU 帐号,\n"
                "然后对自己宿舍的电量进行一次查询,\n"
                "浏览器会读取宿舍信息并自动关闭.\n"
                "浏览器关闭之后请稍等一段时间,\n"
                "不要重复点击按钮.",
                QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return None

        @Slot(dict)
        def room_info_got(info: dict):
            if self._room_info_widget:
                self._room_info_widget.destroy()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("请对照填写到插件配置中"))
            for key, value in info.items():
                label = QLabel(str(key))
                edit = QLineEdit(str(value))
                row = QHBoxLayout()
                row.addWidget(label)
                row.addWidget(edit)
                row_widget = QWidget()
                row_widget.setLayout(row)
                layout.addWidget(row_widget)
            self._room_info_widget = QWidget()
            self._room_info_widget.setWindowTitle("宿舍配置")
            self._room_info_widget.setLayout(layout)
            self._room_info_widget.closeEvent = lambda evt: (
                evt.ignore(),
                self._room_info_widget.destroy()
            )
            self._room_info_widget.show()

        task = Task(self.ask_for_room)
        task.signals.finished.connect(room_info_got)
        QThreadPool.globalInstance().start(task)

    def on_load(self, ctx: PluginContext):
        self.ctx = ctx
        ctx.bind_action("检查连接", self.check_server)
        ctx.bind_action("可视化电量使用情况", self.visualize_degree)
        ctx.bind_action("获取宿舍配置", self.get_dorm_info)

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

        QThreadPool.globalInstance().start(Task(parallel))

    def fetch_degree(self) -> None:
        def parallel():
            try:
                rst = self.async_client(lambda client: client.fetch_degree())
            except Exception:
                rst = -3
            return rst

        task = Task(parallel)
        task.signals.finished.connect(self.on_degree_arrived)
        QThreadPool.globalInstance().start(task)

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
        self.ctx.send_message("email_notifier", ("text", title, text))

    def on_routine(self, ctx: PluginContext):
        self.fetch_degree()

    @Slot(float)
    def on_degree_arrived(self, degree: float):
        if degree == -1:
            self.ctx.report_cache_invalid()
        elif degree == -2:
            self.ctx.get_logger().warning("room info missing")
        elif degree == -3:
            self.ctx.get_logger().warning("communicating with server failed")
        elif degree >= 0:
            self.ctx.get_logger().info(f"{degree=}.")
            if degree < self.alert_degree:
                self.alert(
                    title="电量不足",
                    text=f"电量剩余: {degree}, 请及时进行电量的充值, 以防止意外断电的情况"
                )
                self.notified = True
            else:
                self.notified = False

            if degree > self.prev_degree > 0:  # prev_degree < 0 为特殊情况.
                self.alert(
                    title="电量充值",
                    text=f"检测到电量增加: 增加度数为 {degree - self.prev_degree:.2f}"
                )
            self.prev_degree = degree
