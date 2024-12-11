from __future__ import annotations

import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from typing import Optional


class EmailSender:
    def __init__(self, sender: str, password: str, receiver: str, smtp_host: tuple[str, int],
                 debug=False):
        """
        初始化邮件发送类
        :param sender: 发送方邮件地址.
        :param password: 发送方 smtp 密码.
        :param receiver: 接收方邮件地址.
        :param smtp_host: smtp 服务器 地址, 常用的有: ("smtp.qq.com", 465)
        :param debug: 是否开启 SMTP 调试模式
        """
        self.sender = sender
        self.sender_name = self.sender.split('@')[0]
        self.sender_password = password
        self.receiver = receiver
        self.receiver_name = self.receiver.split('@')[0]
        self.debug = debug
        self.smtp_obj: Optional[smtplib.SMTP_SSL] = None
        self.smtp_host = smtp_host

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
            self.smtp_obj = smtplib.SMTP_SSL(self.smtp_host[0], self.smtp_host[1])
            if self.debug:
                self.smtp_obj.set_debuglevel(1)
            self.smtp_obj.login(self.sender, self.sender_password)
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
            Header(self.sender_name, 'utf-8').encode(),
            self.sender
        ))
        message["To"] = formataddr((
            Header(self.receiver_name, 'utf-8').encode(), self.receiver
        ))
        message["Subject"] = Header(subject, 'utf-8')
        self.smtp_obj.sendmail(self.sender, [self.receiver], message.as_string())

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
            Header(self.sender_name, 'utf-8').encode(),
            self.sender
        ))
        message["To"] = formataddr((
            Header(self.receiver_name, 'utf-8').encode(), self.receiver
        ))
        message["Subject"] = Header(subject, 'utf-8')

        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(html_part)

        self.smtp_obj.sendmail(self.sender, [self.receiver], message.as_string())

    def send_html_with_attachments(self, subject: str, html_content: str,
                                   files: list[str | tuple[str, str]]):
        """
        发送带附件的邮件
        :param subject: 邮件主题
        :param html_content: 邮件正文内容
        :param files: 附件文件列表, 列表元素可以为单独的文件路径, 也可以为 (文件路径, 文件 Content-ID) 元组.
                指定文件的 Content-ID(不需要尖括号), 以便在 html 中引用,
                可以设置为 None, 则对应附件不会有 Content-ID.
        """
        self.connect()
        message = MIMEMultipart()
        message["From"] = formataddr((
            Header(self.sender_name, 'utf-8').encode(), self.sender
        ))
        message["To"] = formataddr((
            Header(self.receiver_name, 'utf-8').encode(), self.receiver
        ))
        message["Subject"] = Header(subject, 'utf-8')

        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(html_part)

        # 遍历附件列表并附加
        for item in files:
            if isinstance(item, tuple):
                file_path = item[0]
                cid = item[1]
            else:
                file_path = item
                cid = None
            try:
                with open(file_path, "rb") as attachment_file:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment_file.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(file_path)}"  # 仅文件名
                )
                if cid is not None:
                    part.add_header("Content-ID", f"<{cid}>")
                message.attach(part)
            except FileNotFoundError:
                raise FileNotFoundError(f"Attachment file {file_path} not found.")
        self.smtp_obj.sendmail(self.sender, [self.receiver], message.as_string())
