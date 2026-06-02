import threading
import time


HEARTBEAT_STALE_MS = 5000
_state_lock = threading.Lock()
_state = {
    'connected': False,
    'last_weapon': '',
    'confidence': 0.0,
    'last_update_ts': 0,
    'helper_ts': 0,
    'last_seen_ts': 0,
    'game': 'cs2',
    'client': '',
    'status': 'disconnected',
}


def get_ocr_state() -> dict:
    with _state_lock:
        state = dict(_state)
    last_seen_ts = int(state.get('last_seen_ts', 0) or 0)
    if last_seen_ts and (int(time.time() * 1000) - last_seen_ts) <= HEARTBEAT_STALE_MS:
        state['connected'] = True
        if state.get('status') == 'disconnected':
            state['status'] = 'connected'
    else:
        state['connected'] = False
        state['status'] = 'disconnected'
    return state


def update_ocr_state(**updates) -> dict:
    with _state_lock:
        _state.update(updates)
        return dict(_state)


def mark_ocr_disconnected() -> dict:
    return update_ocr_state(status='disconnected')


def mark_ocr_connected(client: str = '') -> dict:
    return update_ocr_state(
        connected=True,
        status='connected',
        client=client,
        last_seen_ts=int(time.time() * 1000),
    )


def record_weapon_detection(weapon: str, confidence: float, helper_ts: int, game: str = 'cs2') -> dict:
    now_ms = int(time.time() * 1000)
    return update_ocr_state(
        connected=True,
        status='connected',
        last_weapon=weapon,
        confidence=confidence,
        last_update_ts=now_ms,
        last_seen_ts=now_ms,
        helper_ts=helper_ts,
        game=game,
    )
