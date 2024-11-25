import base64
import pyzbar.pyzbar
from PIL import Image
from io import BytesIO


def display_qrcode():
    with open("assets/login_qrcode_base64.txt", 'r') as f:
        base64_data = f.read().split(',')[1]
    base64_data = base64.b64decode(base64_data)
    img = Image.open(BytesIO(base64_data))
    img.show()

def decode_qrcode():
    with open("assets/login_qrcode_base64.txt", 'r') as f:
        base64_data = f.read().split(',')[1]
    base64_data = base64.b64decode(base64_data)
    img = Image.open(BytesIO(base64_data))
    content = pyzbar.pyzbar.decode(img)
    print(content[0].data)


if __name__ == '__main__':
    decode_qrcode()
