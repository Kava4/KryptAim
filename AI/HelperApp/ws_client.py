import asyncio
import json
import logging
import time
from urllib.parse import urlsplit, urlunsplit

logger = logging.getLogger('AimSync.Helper')

try:
    import websockets
except ImportError:  # pragma: no cover - optional runtime dependency
    websockets = None


class HelperWsClient:
    def __init__(self, server_url: str, token: str = '') -> None:
        self.server_url = self._normalize_server_url(server_url)
        self.token = token.strip()
        self._socket = None

    async def send_event(self, payload: dict) -> None:
        if websockets is None:
            raise RuntimeError("The 'websockets' package is required for the OCR helper client.")

        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            socket = await self._get_connection(headers)
            await socket.send(json.dumps(payload))
        except Exception:
            await self._close_connection()
            raise

    async def send_heartbeat(self) -> None:
        await self.send_event({'type': 'heartbeat', 'ts': int(time.time() * 1000)})

    async def _get_connection(self, headers: dict):
        if self._socket is not None and getattr(self._socket, 'state', None) is not None:
            if not getattr(self._socket, 'closed', False):
                return self._socket

        self._socket = await websockets.connect(
            self.server_url,
            additional_headers=headers,
            ping_interval=20,
            ping_timeout=20,
        )
        return self._socket

    async def _close_connection(self) -> None:
        if self._socket is not None:
            try:
                await self._socket.close()
            except Exception:
                pass
            self._socket = None

    @staticmethod
    def _normalize_server_url(server_url: str) -> str:
        parsed = urlsplit(server_url)
        hostname = parsed.hostname or ''
        if hostname == '0.0.0.0':
            replacement = '127.0.0.1'
            netloc = parsed.netloc.replace('0.0.0.0', replacement, 1)
            return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))
        return server_url
