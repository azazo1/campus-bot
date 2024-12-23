import base64
import unittest

import pyzbar.pyzbar
from PIL import Image
from io import BytesIO

from src.config import init


class QRCodeTest(unittest.TestCase):

    def setUp(self):
        init()

    def test_display_qrcode(self):
        with open("assets/development-references/login_qrcode_base64.txt", 'r') as f:
            base64_data = f.read().split(',')[1]
        base64_data = base64.b64decode(base64_data)
        img = Image.open(BytesIO(base64_data))
        img.show()

    def test_decode_qrcode(self):
        with open("assets/development-references/login_qrcode_base64.txt", 'r') as f:
            base64_data = f.read().split(',')[1]
        base64_data = base64.b64decode(base64_data)
        img = Image.open(BytesIO(base64_data))
        content = pyzbar.pyzbar.decode(img)
        print(content[0].data)
