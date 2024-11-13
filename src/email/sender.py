import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from ..config import SMTP_USER, SMTP_HOST, SMTP_PASS, SMTP_FROM, SMTP_TO

class EmailSender:
    def __init__(self, subject, content, debug=False):
        self.sender = SMTP_USER
        self.receivers = [SMTP_TO[1]]
        self.message = MIMEText(content, "plain", "utf-8")
        self.message["From"] = formataddr((Header(SMTP_FROM[0], 'utf-8').encode(), SMTP_FROM[1]))
        self.message["To"] = formataddr((Header(SMTP_TO[0], 'utf-8').encode(), SMTP_TO[1]))
        self.message["Subject"] = Header(subject, 'utf-8')
        self.debug = debug

    def smtp_connect(self):
        try:
            self.smtp_obj = smtplib.SMTP_SSL(SMTP_HOST, 465)
            if self.debug:
                self.smtp_obj.set_debuglevel(1)
            self.smtp_obj.login(SMTP_USER, SMTP_PASS)
        except Exception as e:
            raise ConnectionError(f"SMTP Connect Error: {e}")

    def smtp_send_text_email(self):
        self.smtp_connect()
        self.smtp_obj.sendmail(self.sender, self.receivers, self.message.as_string())
