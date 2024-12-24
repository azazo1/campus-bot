"""
提交加密登录请求.
"""
import base64
import io
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire.webdriver import Edge

stdout = sys.stdout
sys.stdout = io.StringIO()  # 禁用标准输出
import ddddocr

ocr = ddddocr.DdddOcr()
sys.stdout = stdout  # 恢复标准输出
del stdout

CAPTCHA_IMG_SELECTOR = "#login-normal > div > form > app-verification > nz-input-group > span.ant-input-suffix.ng-star-inserted > div > img"
STUDENT_NUMBER_SELECTOR = "#login-normal > div > form > div.login-normal-item.ant-row.ng-star-inserted > nz-input-group > input"
PASSWORD_SELECTOR = "#login-normal > div > form > div.login-normal-item.passwordInput.ant-row > nz-input-group > input"
CAPTCHA_INPUT_SELECTOR = "#login-normal > div > form > app-verification > nz-input-group > input"
SUBMIT_BUTTON_SELECTOR = "#login-normal > div > form > div.login-normal-button.ant-row > div > button"

EXTRACT_CAPTCHA_IMG_JS = """
let img = document.querySelector("#login-normal > div > form > app-verification > nz-input-group > span.ant-input-suffix.ng-star-inserted > div > img");
let canvas = document.createElement('canvas');
let ctx = canvas.getContext('2d');

canvas.width = img.width;
canvas.height = img.height;

ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
return canvas.toDataURL('image/png');
"""


def wait_for(driver, css_selector: str, timeout):
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR,
            css_selector
        ))
    )


def get_captcha_img(driver: Edge):
    return driver.execute_script(EXTRACT_CAPTCHA_IMG_JS)


def get_captcha_img_stream(img_base64_data: str) -> io.BytesIO:
    """
    根据 base64 (Data URI Scheme) 创建图片数据流.
    """
    b = io.BytesIO()
    b.write(base64.b64decode(img_base64_data.split(",")[1]))
    b.seek(0)
    return b


# todo 如果识别出来的验证码不是 4 位则刷新验证码重新识别.
def submit_login(driver: Edge, stu_number: str, password: str, timeout=24 * 60):
    wait_for(driver, CAPTCHA_IMG_SELECTOR, timeout)
    wait_for(driver, PASSWORD_SELECTOR, timeout)
    wait_for(driver, CAPTCHA_INPUT_SELECTOR, timeout)
    wait_for(driver, STUDENT_NUMBER_SELECTOR, timeout)
    wait_for(driver, SUBMIT_BUTTON_SELECTOR, timeout)

    captcha = ocr.classification(
        get_captcha_img_stream(get_captcha_img(driver)).read()
    )
    driver.execute_script(f"""
    const stu = document.querySelector('{STUDENT_NUMBER_SELECTOR}');
    stu.value = "";
    """)  # 先清空学号输入栏.
    driver.find_element(By.CSS_SELECTOR, PASSWORD_SELECTOR).send_keys(password)
    driver.find_element(By.CSS_SELECTOR, STUDENT_NUMBER_SELECTOR).send_keys(stu_number)
    driver.find_element(By.CSS_SELECTOR, CAPTCHA_INPUT_SELECTOR).send_keys(captcha)
    driver.find_element(By.CSS_SELECTOR, SUBMIT_BUTTON_SELECTOR).click()
