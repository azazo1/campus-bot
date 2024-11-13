import re

class EmailPatterns:
    """邮件常用正则表达式"""
    PAT_FROM = re.compile(b'^From:')
    PAT_TO = re.compile(b'^To:')
    PAT_DATE = re.compile(b'^Date:')
    PAT_SUBJECT = re.compile(b'^Subject:')
    PAT_ATTACHMENT_FILENAME = re.compile(b'filename="?(.+)"?')
    PAT_DECODED_ATTACHMENT_FILENAME = re.compile(r'filename="?(.+)"?')
    PAT_MIME_FORMAT = re.compile(rb'=\?[A-Za-z0-9_-]+\?[BQbq]\?[A-Za-z0-9+/=]+\?=')