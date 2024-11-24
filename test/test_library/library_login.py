from src.config import init
from src.email import EmailSender
from src.library.login import get_login_cache


def main():
    init()
    sender = EmailSender(False)
    sender.connect()
    login_cache = get_login_cache(qrcode_html_callback=lambda title, html_content: sender.send_html_email(
        title, html_content
    ))
    if login_cache:
        sender.send_text_email("Login Successfully", "Login to ECNU successfully.")


if __name__ == '__main__':
    main()
