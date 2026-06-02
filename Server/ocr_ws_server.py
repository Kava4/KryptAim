import asyncio
import json
import logging
import threading
import time

from Config.config_manager import load_config, save_config
from Recoil.weapon_data import WeaponData
from Server.ocr_state import mark_ocr_connected, mark_ocr_disconnected, record_weapon_detection, update_ocr_state

logger = logging.getLogger('AimSync')

try:
    import websockets
except ImportError:  # pragma: no cover - optional runtime dependency
    websockets = None


class OcrWsServer:
    def __init__(self) -> None:
        self._thread = None
        self._write_cooldown_until = 0.0

    def start(self) -> None:
        if websockets is None:
            logger.warning("OCR WebSocket server not started because 'websockets' is not installed.")
            update_ocr_state(status='dependency_missing')
            return
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()

    def _run_server(self) -> None:
        asyncio.run(self._serve())

    async def _serve(self) -> None:
        server = await websockets.serve(self._handle_connection, '0.0.0.0', 8765, ping_interval=20, ping_timeout=20)
        logger.info("OCR WebSocket server listening on ws://0.0.0.0:8765/ws/ocr")
        try:
            await server.wait_closed()
        finally:
            mark_ocr_disconnected()

    async def _handle_connection(self, websocket) -> None:
        client = getattr(websocket, 'remote_address', None)
        client_label = f"{client[0]}:{client[1]}" if isinstance(client, tuple) and len(client) >= 2 else 'unknown'

        try:
            request = getattr(websocket, 'request', None)
            path = getattr(request, 'path', '/')
            if path != '/ws/ocr':
                await websocket.close(code=1008, reason='invalid_path')
                return

            config = load_config()
            token = config.get('ocr_helper_token', '').strip()
            headers = getattr(request, 'headers', {}) or {}
            header_token = headers.get('Authorization', '').removeprefix('Bearer ').strip()
            if token and header_token != token:
                await websocket.close(code=1008, reason='auth_failed')
                return

            mark_ocr_connected(client=client_label)
            async for message in websocket:
                await self._handle_message(message)
        except Exception as exc:  # pragma: no cover - defensive runtime logging
            logger.error("OCR WebSocket connection error: %s", exc)
        finally:
            mark_ocr_disconnected()

    async def _handle_message(self, message: str) -> None:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            logger.warning("Ignoring invalid OCR payload: not valid JSON")
            return

        event_type = payload.get('type')
        if event_type == 'heartbeat':
            update_ocr_state(
                connected=True,
                status='connected',
                helper_ts=int(payload.get('ts', 0) or 0),
                last_seen_ts=int(time.time() * 1000),
            )
            return
        if event_type == 'status':
            update_ocr_state(
                connected=True,
                status=str(payload.get('status', 'connected')),
                last_seen_ts=int(time.time() * 1000),
            )
            return
        if event_type != 'weapon_detected':
            return

        config = load_config()
        if not config.get('ocr_enabled', False):
            return

        confidence = float(payload.get('confidence', 0.0) or 0.0)
        threshold = float(config.get('ocr_confidence_threshold', 0.7) or 0.7)
        if confidence < threshold:
            return

        helper_ts = int(payload.get('ts', 0) or 0)
        now_ms = int(time.time() * 1000)
        if helper_ts and helper_ts < (now_ms - 5000):
            return

        game_id = str(payload.get('game', 'cs2') or 'cs2').lower()
        weapon = str(payload.get('weapon', '') or '').strip().lower()
        available_weapons = self._get_available_weapons(game_id)
        if weapon not in available_weapons:
            return

        record_weapon_detection(weapon=weapon, confidence=confidence, helper_ts=helper_ts, game=game_id)
        if time.time() < self._write_cooldown_until:
            return

        config['active_game'] = game_id
        config['recoil_game_settings']['weapon'] = weapon
        save_config(config)
        self._write_cooldown_until = time.time() + 0.2

    @staticmethod
    def _get_available_weapons(game_id: str) -> list[str]:
        weapon_data = WeaponData.get_game_data(game_id)
        weapons = [attr for attr in dir(weapon_data) if not attr.startswith('_') and isinstance(getattr(weapon_data, attr), list)]
        weapons.sort()
        return weapons


ocr_ws_server = OcrWsServer()


def start_ocr_ws_server_thread() -> None:
    ocr_ws_server.start()
