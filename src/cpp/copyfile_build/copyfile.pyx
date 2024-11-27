import os.path
cdef extern from "copyfile_raw.cpp":
    int CopyFileToClipboard(bytes filepath);

def copyfile(filepath: str):
    """
    复制文件或文件夹到剪贴板.

    使用的是 CF_HDROP 格式复制, 执行此方法并不会实质性读取文件内容,
    在粘贴的时候才根据接收方进行文件粘贴操作.

    Returns:
        0 表示复制成功.
        非 0 值表示遇到剪贴板错误.

    Raises:
        TypeError: 传入的参数不是字符串.
        FileNotFoundError: 传入的文件不存在.
        UnicodeEncodeError: 字符串编码错误.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(filepath)
    filepath = os.path.abspath(filepath)
    cdef bytes filepath_bytes = filepath.encode("utf-16le")  # 要传入宽字符串, 故使用 utf-16le 编码.
    return CopyFileToClipboard(filepath_bytes)
