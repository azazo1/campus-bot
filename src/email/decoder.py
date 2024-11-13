import os
import base64
from email.quoprimime import decode as q_decode
from .patterns import EmailPatterns

class EmailDecoder:
    @staticmethod
    def decode_attachment_base64(attachment_bin_data: bytes, attachment_name: str) -> None:
        attachment_name = attachment_name.replace('"', '')
        output_dir = "Output_Attachment"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_path = os.path.join(output_dir, attachment_name)
        with open(output_path, "wb") as file:
            file.write(attachment_bin_data)

    @staticmethod
    def decode_content_base64(content_base64_data: bytes, charset: str) -> str:
        return base64.b64decode(content_base64_data).decode(f"{charset}")

    @staticmethod
    def decode_mime_header(header: bytes) -> str:
        start = header.find(b'=?')
        end = header.find(b'?=', start) + 2
        mime_encoded_part = header[start:end]
        parts = mime_encoded_part.split(b'?')
        charset = parts[1].decode('utf-8')
        encoding = parts[2].decode('utf-8')
        encoded_data = parts[3].decode('utf-8')
        if encoding.upper() == 'B':
            decoded_bytes = base64.b64decode(encoded_data)
            decoded_string = decoded_bytes.decode(charset)
            return header.replace(mime_encoded_part, decoded_string.encode('utf-8')).decode('utf-8')
        elif encoding.upper() == 'Q':
            return q_decode(encoded_data)
        else:
            raise ValueError("不支持的编码方式")
