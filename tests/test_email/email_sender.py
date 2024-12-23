import unittest

from src.config import init
from src.email.sender import EmailSender


class TestEmailSender(unittest.TestCase):
    """填入相关信息后才能运行测试"""

    def setUp(self):
        init()

    def test_email_sender(self):
        email_sender = EmailSender(sender="", password="", receiver="", smtp_host=("smtp.qq.com", 465))
        email_sender.connect()
        email_sender.send_text_email("Test Text Subject", "Hello, World!")
        email_sender.send_html_email("Test Html Subject", "<h1>Hello, World!</h1>")
        email_sender.send_html_with_attachments("Test Attachment Subject",
                                                "<h1>Test Attachment Content</h1>",
                                                ["assets/development-references/ecnu_logo.png", "assets/development-references/ecnu_logo.png"])

    def test_send_open_wx_link(self):
        email_sender = EmailSender(sender="", password="", receiver="", smtp_host=("smtp.qq.com", 465))
        email_sender.connect()
        email_sender.send_html_email("Open WX", "<a href='weixin://'>打开微信</a>")
