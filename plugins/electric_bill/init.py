class Command:
    """
    一个 Command json 格式就像: `{"type": command_type, "args": ...}`.
    返回值就像: `{"retcode": RETCODE, content: ...}`.
    """
    POST_TOKEN = 'post_token'
    POST_ROOM = 'post_room'
    GET_DEGREE = 'get_degree'
    FETCH_DEGREE_FILE = 'fetch_degree_file'


class RetCode:
    Ok = 0
    ErrUnknown = 1
    ErrArgs = 2
    ErrNoFile = 3
