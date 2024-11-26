import unittest

from src.config import init
from src.email import EmailSender
from src.uia.login import get_login_cache


class LoginTest(unittest.TestCase):
    def setUp(self):
        init()

    def test_email_notice_login(self):
        sender = EmailSender(False)
        sender.connect()
        login_cache = get_login_cache(
            qrcode_html_callback=lambda title, html_content: sender.send_html_email(
                title, html_content
            )
        )
        if login_cache:
            sender.send_text_email("Login Successfully", "Login to ECNU successfully.")
