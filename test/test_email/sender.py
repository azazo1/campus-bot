from src.config import init
from src.email.sender import EmailSender


def main():
    init()
    email_sender = EmailSender(debug=True)
    email_sender.smtp_send_text_email("Test Text Subject", "Hello, World!")
    email_sender.smtp_send_html_email("Test Html Subject", "<h1>Hello, World!</h1>")
    email_sender.smtp_send_attachments("Test Attachment Subject",
                                       "<h1>Test Attachment Content</h1>",
                                       ["test/test_email/ecnu_logo.png", "test/test_email/ecnu_logo_2.png"])


if __name__ == '__main__':
    main()
