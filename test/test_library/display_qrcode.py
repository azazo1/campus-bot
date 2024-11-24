import base64

from PIL import Image
from io import BytesIO


def display_qrcode():
    with open("assets/login_qrcode_base64.txt", 'r') as f:
        base64_data = f.read().split(',')[1]
    base64_data = base64.b64decode(base64_data)
    img = Image.open(BytesIO(base64_data))
    img.show()


if __name__ == '__main__':
    display_qrcode()
