import unittest

from src.config import init
from src.email.sender import EmailSender


class TestEmailSender(unittest.TestCase):
    def setUp(self):
        init()

    def test_email_sender(self):
        email_sender = EmailSender(debug=True)
        email_sender.connect()
        email_sender.send_text_email("Test Text Subject", "Hello, World!")
        email_sender.send_html_email("Test Html Subject", "<h1>Hello, World!</h1>")
        email_sender.send_attachments("Test Attachment Subject",
                                      "<h1>Test Attachment Content</h1>",
                                      ["test/test_email/ecnu_logo.png",
                                       "test/test_email/ecnu_logo_2.png"])

    def test_send_open_wx_link(self):
        email_sender = EmailSender()
        email_sender.connect()
        email_sender.send_html_email("Open WX", "<a href='weixin://'>打开微信</a>")
