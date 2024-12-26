"""
ECNU 统一认证.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def attribute_changes(css_selector: str, attribute_name: str):
    """
    Expected Conditions 方法.

    一个元素的属性发生变化时触发.

    :param css_selector: 对应元素的 css selector, 如果其包含多个元素, 那么只会取第一个元素.
    :param attribute_name: 要监视的元素属性, 如 <img> 元素的 src 属性.
    """
    prev = None

    def _predicate(driver: EC.WebDriverOrWebElement):
        nonlocal prev
        ele = driver.find_element(By.CSS_SELECTOR, css_selector)
        new = ele.get_attribute(attribute_name)
        if prev is None:
            prev = new
        elif prev != new:
            prev = new
            return True
        return False

    return _predicate