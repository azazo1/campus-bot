"""
Windows 微信消息自动化脚本.

测试环境:
- Windows 11.
- 系统语言为中文.
- 微信 3.9.10.27
"""
from __future__ import annotations
import ctypes
import time
from asyncio import InvalidStateError
from typing import Self

import psutil
import uiautomation


class WeChatNotForegroundError(Exception):
    """微信不在前台"""
    pass


class ProcessNotFoundError(Exception):
    """没有微信进程"""
    pass


class WeChatNotLoginError(Exception):
    """微信没有登录"""
    pass


class ReserveCursorFocus:
    """
    在执行某个操作后恢复鼠标指针位置和焦点.

    Examples:

    >>> # 1
    >>> with ReserveCursorFocus():
    ...     print("Hello World") # 替换成其他会改变鼠标位置或者焦点的操作.
    Hello World
    >>> # 2
    >>> reserve = ReserveCursorFocus()
    >>> reserve.save() # 此行可选, 也可调用多次.
    >>> print("Hello World") # 替换成其他会改变鼠标位置或者焦点的操作.
    Hello World
    >>> reserve.restore() # 此行可调用多次.
    """

    def __init__(self):
        self.cursor: tuple[int, int] = (-1, -1)
        self.focus: int = -1
        self.save()

    def save(self):
        self.cursor = uiautomation.GetCursorPos()
        self.focus = uiautomation.GetForegroundWindow()

    def restore(self):
        uiautomation.ControlFromHandle(self.focus).SetFocus()
        uiautomation.SetCursorPos(*self.cursor)
        time.sleep(0.01)  # 确保焦点已经完全转移, 否则再次调用 GetForegroundWindow 会返回 None.

    def __enter__(self):
        self.save()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore()


def reserve_cursor_focus(func):
    """
    在执行某个函数后恢复鼠标指针位置和焦点.

    此装饰器针对需要修改鼠标指针位置或者需要修改焦点的函数.
    """

    def wrapper(*args, **kwargs):
        with ReserveCursorFocus():
            func(*args, **kwargs)

    return wrapper


def get_pid_by_name(name: str, ignore_case=False) -> int:
    """
    查找并获取进程 pid, 如果有多个同名进程, 只会返回第一个匹配名称的进程 pid.

    Parameters:
        name: 要查找的进程名称.
        ignore_case: 查找是否无视大小写.

    Returns:
        如果找不到该进程, 返回 -1.
    """
    for proc in psutil.process_iter():
        if ignore_case:
            if proc.name().lower() == name.lower():
                return proc.pid
        else:
            if proc.name() == name:
                return proc.pid
    return -1


def wechat_window() -> uiautomation.WindowControl:
    """
    获取微信主窗口 Control.

    但是此方法无法获取在后台运行的微信.

    Returns:
        微信主窗口 WindowControl 对象.

    Raises:
        ProcessNotFoundError: 微信没启动.
        WeChatNotLoginError: 微信没有登录, 如果电脑上有微信多开可能出现预期外的情况.
        WeChatNotForegroundError: 微信不在前台.
    """
    if get_pid_by_name("Wechat.exe", True) < 0:
        raise ProcessNotFoundError("Wechat.exe")
    wechat_main = uiautomation.WindowControl(searchDepth=1, Name="微信",
                                             ClassName="WeChatMainWndForPC")
    wechat_login = uiautomation.PaneControl(searchDepth=1, Name="微信",
                                              ClassName="WeChatLoginWndForPC")
    if wechat_login.Exists(0, 0):
        raise WeChatNotLoginError()  # 在微信的登录界面, 没有登录, 无法使用后续功能.
    if wechat_main.Exists(0, 0):
        return wechat_main
    # 进入此处说明微信正在运行且不是未登录状态, 并且任务栏没有微信窗口, 那么就说明微信在后台.
    raise WeChatNotForegroundError()


def wechat(taskbar: Taskbar | None = None) -> uiautomation.WindowControl:
    """
    获取微信主窗口 Control.

    如果微信启动了, 但是窗口没有在任务栏中, 首先在任务栏托盘中点击图标进行窗口唤出.
    如果任务栏托盘中微信图标没有固定, 那么展开任务栏托盘再寻找微信图标并唤出窗口.

    正常情况下只需要调用此方法一次, 然后缓存 WindowControl 对象,
    如果后续微信窗口变更了, 只需要调用 WindowControl 的 Refind 方法即可.

    但是有可能微信窗口又回到了任务栏, 此情况需要再次调用此函数.

    Parameters:
        taskbar: 用于在微信窗口不存在时对任务栏的操作, 如果提供为 None, 则在内部再次创建 Taskbar 对象,
            可能会增加此函数调用的时间.

    Returns:
        微信主窗口 WindowControl 对象.

    Raises:
        ProcessNotFoundError: 微信没启动.
        WeChatNotLoginError: 微信没有登录, 如果电脑上有微信多开可能出现预期外的情况.
        InvalidStateError: 异常情况, 微信在运行, 但是无法找到并打开微信窗口,
            导致这种情况的可能原因是用户在脚本执行操作的时候动了鼠标.
    """
    try:
        return wechat_window()
    except WeChatNotForegroundError:
        # 到此处表明微信正在运行, 但是不在前台运行.
        taskbar = taskbar or Taskbar.get_taskbar()
        icon = taskbar.find_icon("微信")
        if icon:  # 任务栏固定图标中找到了微信.
            icon.Click(simulateMove=False)
        else:  # 在任务栏隐藏图标中寻找微信.
            with taskbar.with_icon_expand() as tray:
                click_rst = tray.click("微信")
            if not click_rst:
                # 没有找到微信图标, 通常不会出现此情况.
                raise InvalidStateError("Can't open wechat window, unknown error.")
        return wechat_window()


class Taskbar:
    def __init__(self, taskbar_control: uiautomation.Control):
        self.control = taskbar_control  # 任务栏 control.
        self.expand_button = self._get_expand_tray_button()  # '显示隐藏图标' 按钮.
        assert self.expand_button.Exists(0, 0)

    def _get_expand_tray_button(self) -> uiautomation.ButtonControl:
        return self.control.ButtonControl(
            ClassName="SystemTray.NormalButton",
            Name="显示隐藏的图标",
            searchDepth=3
        )

    @classmethod
    def get_taskbar(cls) -> Taskbar:
        """
        >>> Taskbar.get_taskbar() is not None
        True
        """
        return cls(uiautomation.ControlFromHandle(
            ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        ))

    def find_icon(
            self,
            name: str,
            control: uiautomation.Control | None = None
    ) -> uiautomation.ButtonControl | None:
        """
        查找任务栏中的图标按钮.

        任务栏托盘中固定的图标 Control 属性有这些:
        ```
        ControlType: ButtonControl
        ClassName: SystemTray.NormalButton
        AutomationId: NotifyItemIcon
        Name: name
        ```

        :param name: 搜索的图标的 name.
        :param control: 在指定的 Control 中搜索, 如果提供 None 那么在任务栏中搜索.
        """
        control = control or self.control
        icon = control.ButtonControl(
            ClassName="SystemTray.NormalButton",
            AutomationId="NotifyItemIcon",
            Name=name,
            searchDepth=3
        )
        if icon.Exists(0, 0):
            return icon
        else:
            return None

    def with_icon_expand(self):
        """
        在展开的任务栏托盘中执行操作.

        Examples:

        >>> with Taskbar.get_taskbar().with_icon_expand() as tray:
        ...     tray.click(name="微信")
        True

        在上下文操作中使用额外操作控制任务栏托盘(比如焦点改变导致托盘缩回)可能会导致意料之外的行为.
        """
        return self.IconExpandedTray(self)

    class IconExpandedTray:
        """
        任务栏托盘展开上下文.

        任务栏托盘隐藏图标所在的 Control 属性有这些:
        ```
        ControlType: PaneControl
        ClassName: TopLevelWindowForOverflowXamlIsland
        Name: "系统托盘溢出窗口。"
        ```
        """

        def __init__(self, tb: Taskbar):
            self.tb = tb
            self.tray_control = uiautomation.PaneControl(
                ClassName="TopLevelWindowForOverflowXamlIsland",
                Name="系统托盘溢出窗口。",
                searchDepth=1,
            )

        def __enter__(self) -> Self:
            if not self.tray_control.Exists(0, 0):
                # 如果托盘没展开就点击按钮展开.
                self.tb.expand_button.Click(simulateMove=False)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.tray_control.Exists(0, 0):
                self.tb.expand_button.Click(simulateMove=False)

        def click(self, name: str) -> bool:
            """
            点击任务栏托盘中的图标.

            :returns: 如果成功点击图标, 返回 True, 如果图标不存在或者点击失败, 返回 False.
            此函数不会报找不到图标的错误.
            """
            icon = self.tb.find_icon(name, self.tray_control)
            if not icon:
                return False
            icon.Click(simulateMove=False)
            return True


def main():
    with ReserveCursorFocus():
        wx = wechat()
        wx.SetFocus()


if __name__ == '__main__':
    main()
