import tkinter as tk
import traceback

from selenium.webdriver import Edge
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def alert(title: str, text: str, button: str = "好的", topmost=True, editable=False) -> bool:
    """显示对话弹窗, 如果用户表示同意操作, 返回 True, 如果用户关闭弹窗返回 False."""
    grant = False

    def grant_it():
        nonlocal grant
        grant = True
        root.destroy()

    root = tk.Tk()
    root.title(title)
    root.wm_attributes("-topmost", topmost)
    if not editable:
        tk.Label(root, text=text).pack()
    else:
        txt = tk.Text(root)
        txt.insert("1.0", text)
        txt.pack()
    tk.Button(root, text=button, command=grant_it).pack()
    root.mainloop()
    return grant


def ask_for_room():
    if not alert(title="宿舍信息配置查询",
                 text="请点击确认按钮, 先登录 ECNU 帐号,\n"
                      "然后对自己宿舍的电量进行一次查询,\n"
                      "浏览器会读取宿舍信息并自动关闭."):
        return None
    driver = Edge()
    try:
        driver.get(
            "https://epay.ecnu.edu.cn/epaycas/electric/load4electricbill?elcsysid=1"
        )  # 这个网址会重定向至登录界面.
        # 先等待用户登录.
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
            """)
        WebDriverWait(driver, timeout=60 * 60).until(
            EC.presence_of_element_located((By.ID, "query_clicked"))
        )
        elcbuis = driver.find_element(By.ID, "elcbuis").get_property("value")
        elcarea = driver.find_element(By.ID, "elcarea").get_property("value")
        elcroom = driver.find_element(By.ID, "elcroom").get_property("value")
        return {
            "elcbuis": elcbuis,
            "elcarea": int(elcarea),
            "room_no": elcroom,
        }
    finally:
        driver.quit()


def main():
    try:
        rst = ask_for_room()
        alert("宿舍信息", f"{rst}", editable=True)
    except Exception:
        traceback.print_exc()
        alert("查询失败", f"{traceback.format_exc()}", editable=True)


if __name__ == "__main__":
    main()
