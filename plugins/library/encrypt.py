"""
ECNU 图书馆网站加密实现, 这里的实现可能会根据网络管理员对网站的更改而失效.

加密算法分析见 assets/development-references/confirm_subscribe.js
"""
import base64
import time
import json
from Crypto.Cipher import AES

AES_IV = "ZZWBKJ_ZHIHUAWEI"


def day_str():
    """对原 js exchangeDataTime 的部分实现"""
    return time.strftime("%Y%m%d", time.localtime())


def pkcs7_pad(data, block_size):
    padding_len = block_size - len(data) % block_size
    if padding_len == 0:  # 如果符合 block_size 边界, 那么添加一个数据块.
        padding_len = block_size
    padding = bytes([padding_len] * padding_len)
    return data + padding


def pkcs7_unpad(data):
    padding_len = data[-1]  # 填充的最后一字节表示填充长度
    if padding_len > len(data):
        raise ValueError("Invalid padding.")
    return data[:-padding_len]


class Encryptor:
    @classmethod
    def encrypt(cls, json_data: dict, key: str = None) -> str:
        """
        加密 json 数据, 返回加密的 base64 字符串.

        Parameters:
            json_data: 要加密的数据.
            key: 加密密钥, 默认和原 js 相同.

        >>> Encryptor.encrypt({"seat_id": "3361", "segment": "1508173"}, "2024112882114202")
        '6l1+11NSwbo9Rje1/+pnuSqexfDXg/pPDTK0KJEG/uOIZyucecgEo7VO8ggVRom9'
        """
        if key is None:  # 这个默认值
            key = day_str()
            key = key + key[::-1]
        to_encrypt = json.dumps(json_data, separators=(",", ":")).encode("utf-8")
        en = AES.new(
            key=key.encode("utf-8"),
            mode=AES.MODE_CBC,
            iv=AES_IV.encode("utf-8"),
        )
        return base64.b64encode(
            en.encrypt(pkcs7_pad(to_encrypt, AES.block_size))
        ).decode('utf-8')

    @classmethod
    def decrypt(cls, base64_str: str, key: str = None) -> dict:
        """
        encrypt 函数反函数.

        >>> Encryptor.decrypt('6l1+11NSwbo9Rje1/+pnuSqexfDXg/pPDTK0KJEG/uOIZyucecgEo7VO8ggVRom9', "2024112882114202")
        {'seat_id': '3361', 'segment': '1508173'}
        """
        if key is None:
            key = day_str()
            key = key + key[::-1]
        de = AES.new(
            key=key.encode("utf-8"),
            mode=AES.MODE_CBC,
            iv=AES_IV.encode("utf-8"),
        )
        return json.loads(
            pkcs7_unpad(de.decrypt(
                base64.b64decode(base64_str)
            ))
        )
