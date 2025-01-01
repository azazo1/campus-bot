import json
import logging
from typing import Optional
from websockets.asyncio.client import ClientConnection
from .init import Command
from .encryption import decrypt, encrypt


class GuardClient:
    """
    保证 server 始终取得正确的 token 和 cookies.
    需要手动关闭 client (ClientConnection).
    """

    def __init__(self, client: ClientConnection, key: bytes, iv: bytes, logger: logging.Logger):
        self.client = client
        self.key = key
        self.iv = iv
        self.logger = logger

    async def _send_command(self, type_: str, args: Optional[object] = None):
        dic = {"type": type_}
        if args is not None:
            dic["args"] = args
        await self.client.send(encrypt(
            json.dumps(dic), self.key, self.iv
        ))

    async def _recv_ret(self):
        return json.loads(decrypt(await self.client.recv(), self.key, self.iv))

    async def post_token(self, x_csrf_token: str, cookies: dict[str, str]):
        await self._send_command(
            Command.POST_TOKEN,
            {"x_csrf_token": x_csrf_token, "cookies": cookies}
        )
        ret = await self._recv_ret()
        if ret["retcode"] != 0:
            self.logger.error(f"retcode is not zero: {ret}.")

    async def fetch_degree(self) -> float:
        await self._send_command(Command.GET_DEGREE)
        ret = await self._recv_ret()
        if ret["retcode"] != 0:
            self.logger.error(f"retcode is not zero: {ret}.")
        return ret["content"]

    async def post_room(self, roomNo: str, elcarea: int, elcbuis: str):
        await self._send_command(
            Command.POST_ROOM,
            {"roomNo": roomNo, "elcarea": elcarea, "elcbuis": elcbuis}
        )
        ret = await self._recv_ret()
        if ret["retcode"] != 0:
            self.logger.error(f"retcode is not zero: {ret}.")

    async def fetch_degree_file(self) -> str | None:
        await self._send_command(Command.FETCH_DEGREE_FILE)
        ret = await self._recv_ret()
        if ret["retcode"] != 0:
            self.logger.error(f"retcode is not zero: {ret}.")
        return ret['content']
