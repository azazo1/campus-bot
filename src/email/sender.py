import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from typing import Optional

from .. import config


class EmailSender:
    def __init__(self, debug=False):
        """
        初始化邮件发送类
        :param debug: 是否开启 SMTP 调试模式
        """
        self.sender = config.SMTP_USER
        self.receivers = [config.SMTP_TO[1]]
        self.debug = debug
        self.smtp_obj: Optional[smtplib.SMTP_SSL] = None

    def __del__(self):
        self.quit()

    def quit(self):
        """关闭 smtp 会话, 可多次调用而不报错."""
        if self.smtp_obj:
            self.smtp_obj.quit()
            self.smtp_obj = None

    def connect(self):
        """
        连接到 SMTP 服务器, 对于 smtp.qq.com, 每次发送邮件都要重新连接.
        """
        try:
            self.quit()
            self.smtp_obj = smtplib.SMTP_SSL(config.SMTP_HOST, 465)
            if self.debug:
                self.smtp_obj.set_debuglevel(1)
            self.smtp_obj.login(config.SMTP_USER, config.SMTP_PASS)
        except Exception as e:
            raise ConnectionError(f"SMTP Connect Error: {e}")

    def send_text_email(self, subject: str, text_content: str):
        """
        发送纯文本邮件
        :param subject: 邮件主题
        :param text_content: 邮件正文内容
        """
        self.connect()
        message = MIMEText(text_content, "plain", "utf-8")
        message["From"] = formataddr((
            Header(config.SMTP_FROM[0], 'utf-8').encode(),
            config.SMTP_FROM[1]
        ))
        message["To"] = formataddr((Header(config.SMTP_TO[0], 'utf-8').encode(), config.SMTP_TO[1]))
        message["Subject"] = Header(subject, 'utf-8')
        self.smtp_obj.sendmail(self.sender, self.receivers, message.as_string())

    def send_html_email(self, subject: str, html_content: str):
        """
        发送 HTML 邮件
        :param subject: 邮件主题
        :param html_content: HTML 格式的邮件正文内容
        """
        self.connect()
        # 要发送 HTML 格式的邮件，需要先格式化为 Multipart
        message = MIMEMultipart("alternatives")
        message["From"] = formataddr((
            Header(config.SMTP_FROM[0], 'utf-8').encode(),
            config.SMTP_FROM[1]
        ))
        message["To"] = formataddr((Header(config.SMTP_TO[0], 'utf-8').encode(), config.SMTP_TO[1]))
        message["Subject"] = Header(subject, 'utf-8')

        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(html_part)

        self.smtp_obj.sendmail(self.sender, self.receivers, message.as_string())

    def send_attachments(self, subject: str, html_content: str, file_paths: list):
        """
        发送带附件的邮件
        :param subject: 邮件主题
        :param html_content: 邮件正文内容
        :param file_paths: 附件文件路径，传入一个列表，具体查看 test/test_email.py
        """
        self.connect()
        message = MIMEMultipart()
        message["From"] = formataddr(
            (Header(config.SMTP_FROM[0], 'utf-8').encode(), config.SMTP_FROM[1]))
        message["To"] = formataddr((Header(config.SMTP_TO[0], 'utf-8').encode(), config.SMTP_TO[1]))
        message["Subject"] = Header(subject, 'utf-8')

        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(html_part)

        # 遍历附件列表并附加
        for file_path in file_paths:
            try:
                with open(file_path, "rb") as attachment_file:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment_file.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(file_path)}"  # 仅文件名
                )
                message.attach(part)
            except FileNotFoundError:
                raise FileNotFoundError(f"Attachment file {file_path} not found.")

        self.smtp_obj.sendmail(self.sender, self.receivers, message.as_string())
