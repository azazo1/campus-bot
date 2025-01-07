from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def encrypt(message: str | bytes, key: bytes, iv: bytes) -> bytes:
    _cipher = AES.new(key, AES.MODE_CBC, iv=iv)  # 不能提出去, 似乎是一次性的对象.
    if isinstance(message, str):
        message = message.encode('utf-8')
    return _cipher.encrypt(pad(message, AES.block_size))


def decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    _cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    return unpad(_cipher.decrypt(data), AES.block_size)
