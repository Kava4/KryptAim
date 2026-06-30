"""Daily Vision AI time limit for free tier (persists across restarts)."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import threading
import time
from datetime import date
from pathlib import Path

from app.core.config import config_dir
from app.core.env import env_flag, env_get

logger = logging.getLogger('KryptAim.ai_quota')

_LOCK = threading.Lock()
_MANAGER: 'AiFreeQuotaManager | None' = None

DEFAULT_DAILY_MINUTES = 120
_USAGE_VERSION = 1
_QUOTA_SEAL_MATERIAL = b'kryptaim-ai-quota-v1'


def _daily_limit_seconds() -> int:
    raw = env_get('AI_FREE_DAILY_MINUTES', '').strip()
    if raw:
        try:
            return max(1, int(float(raw))) * 60
        except ValueError:
            pass
    return DEFAULT_DAILY_MINUTES * 60


def quota_feature_enabled(*, premium_required: bool) -> bool:
    if premium_required:
        return False
    if env_flag('AI_FREE_QUOTA_OFF'):
        return False
    return True


def cloud_quota_enabled() -> bool:
    if env_flag('AI_FREE_QUOTA_CLOUD_OFF'):
        return False
    return True


def _usage_path() -> Path:
    return config_dir() / 'ai_free_usage.json'


def _quota_sign_key() -> bytes:
    from app.core.feedback import get_hwid

    env = (
        env_get('KRYPTAIM_SEAL_KEY', '').strip()
        or env_get('AIMSYNC_SEAL_KEY', '').strip()
    )
    seed = _QUOTA_SEAL_MATERIAL + env.encode('utf-8') + get_hwid().encode('utf-8')
    return hashlib.pbkdf2_hmac('sha256', seed, b'kryptaim-quota', 100_000, dklen=32)


def _sign_usage(*, usage_date: str, used_seconds: float, updated_at: float) -> str:
    body = f'{usage_date}\n{used_seconds:.4f}\n{updated_at:.6f}'.encode('utf-8')
    return hmac.new(_quota_sign_key(), body, hashlib.sha256).hexdigest()


def _verify_usage(data: dict) -> bool:
    sig = str(data.get('sig') or '')
    if not sig:
        return False
    try:
        usage_date = str(data.get('date') or '')
        used_seconds = float(data.get('used_seconds') or 0)
        updated_at = float(data.get('updated_at') or 0)
    except (TypeError, ValueError):
        return False
    expected = _sign_usage(
        usage_date=usage_date,
        used_seconds=used_seconds,
        updated_at=updated_at,
    )
    return hmac.compare_digest(sig, expected)


class AiFreeQuotaManager:
    def __init__(self) -> None:
        self._limit_seconds = _daily_limit_seconds()
        self._usage_date = date.today().isoformat()
        self._used_seconds = 0.0
        self._engine_on = False
        self._session_started: float | None = None
        self._cloud_synced = False
        self._last_cloud_sync = 0.0
        self._load()
        self._refresh_from_cloud(force=True)

    def _refresh_from_cloud(self, *, force: bool = False) -> bool:
        if not cloud_quota_enabled():
            return False
        now = time.time()
        if not force and now - self._last_cloud_sync < 15.0:
            return self._cloud_synced
        from app.core.cloud import fetch_ai_quota_status
        from app.core.feedback import get_hwid

        local_used = self._used_seconds
        data, error = fetch_ai_quota_status(hwid=get_hwid())
        self._last_cloud_sync = now
        if error or not data:
            logger.debug('Cloud quota refresh skipped: %s', error)
            return False
        try:
            cloud_used = max(0.0, float(data.get('used_seconds') or 0))
        except (TypeError, ValueError):
            cloud_used = 0.0
        if local_used > cloud_used + 0.5:
            if self._push_cloud_delta(local_used - cloud_used):
                return True
        self._apply_cloud_payload(data)
        self._cloud_synced = True
        return True

    def _apply_cloud_payload(self, data: dict) -> None:
        if data.get('unlimited'):
            return
        usage_date = str(data.get('date') or date.today().isoformat())
        if usage_date != date.today().isoformat():
            self._roll_day_if_needed()
            return
        self._usage_date = usage_date
        try:
            limit = int(data.get('limit_seconds') or self._limit_seconds)
            if limit > 0:
                self._limit_seconds = limit
        except (TypeError, ValueError):
            pass
        try:
            cloud_used = max(0.0, float(data.get('used_seconds') or 0))
        except (TypeError, ValueError):
            cloud_used = 0.0
        # Cloud is authoritative when online — prevents local file tampering.
        self._used_seconds = min(float(self._limit_seconds), cloud_used)
        self._persist(force=True)

    def _push_cloud_delta(self, delta: float) -> bool:
        if not cloud_quota_enabled() or delta <= 0:
            return False
        from app.core.cloud import post_ai_quota_tick
        from app.core.feedback import get_hwid

        data, error = post_ai_quota_tick(hwid=get_hwid(), delta_seconds=delta)
        self._last_cloud_sync = time.time()
        if error or not data:
            logger.debug('Cloud quota tick failed: %s', error)
            return False
        self._apply_cloud_payload(data)
        self._cloud_synced = True
        return True

    def _load(self) -> None:
        path = _usage_path()
        if not path.is_file():
            return
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError, TypeError):
            logger.warning('Could not read AI usage file — starting fresh')
            return
        if not isinstance(data, dict):
            return
        stored_date = str(data.get('date') or '')
        if stored_date != date.today().isoformat():
            self._usage_date = date.today().isoformat()
            self._used_seconds = 0.0
            self._persist(force=True)
            return
        self._usage_date = stored_date
        version = data.get('v')
        if version == _USAGE_VERSION:
            if not _verify_usage(data):
                logger.warning('AI usage file failed integrity check — quota exhausted for today')
                self._used_seconds = float(self._limit_seconds)
                self._persist(force=True)
                return
        elif version is None and not data.get('sig'):
            # One-time migration from unsigned legacy files.
            try:
                self._used_seconds = max(0.0, float(data.get('used_seconds') or 0))
            except (TypeError, ValueError):
                self._used_seconds = 0.0
            self._used_seconds = min(self._limit_seconds, self._used_seconds)
            self._persist(force=True)
            return
        else:
            logger.warning('AI usage file has unknown format — quota exhausted for today')
            self._used_seconds = float(self._limit_seconds)
            self._persist(force=True)
            return
        try:
            self._used_seconds = max(0.0, float(data.get('used_seconds') or 0))
        except (TypeError, ValueError):
            self._used_seconds = 0.0
        self._used_seconds = min(self._limit_seconds, self._used_seconds)

    def _persist(self, *, force: bool = False) -> None:
        path = _usage_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            updated_at = time.time()
            payload = {
                'v': _USAGE_VERSION,
                'date': self._usage_date,
                'used_seconds': round(self._used_seconds, 2),
                'updated_at': updated_at,
            }
            payload['sig'] = _sign_usage(
                usage_date=self._usage_date,
                used_seconds=float(payload['used_seconds']),
                updated_at=updated_at,
            )
            path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        except OSError:
            if force:
                logger.exception('Failed to persist AI free usage')

    def _session_elapsed(self) -> float:
        if not self._engine_on or self._session_started is None:
            return 0.0
        return max(0.0, time.monotonic() - self._session_started)

    def total_used_seconds(self) -> float:
        return min(self._limit_seconds, self._used_seconds + self._session_elapsed())

    def remaining_seconds(self) -> float:
        return max(0.0, self._limit_seconds - self.total_used_seconds())

    def is_exhausted(self) -> bool:
        return self.remaining_seconds() <= 0.0

    def sync_engine_state(self, enabled: bool) -> None:
        with _LOCK:
            enabled = bool(enabled)
            if enabled and not self._engine_on:
                self._roll_day_if_needed()
                self._refresh_from_cloud(force=True)
                if self.is_exhausted():
                    return
                self._engine_on = True
                self._session_started = time.monotonic()
                return
            if not enabled and self._engine_on:
                self._flush_session_locked()
                self._engine_on = False
                self._session_started = None

    def tick(self) -> bool:
        """Record ~1s of usage while engine runs. Returns True if quota just exhausted."""
        with _LOCK:
            self._roll_day_if_needed()
            if not self._engine_on:
                return False
            if self._session_elapsed() >= 15.0 and cloud_quota_enabled():
                self._refresh_from_cloud(force=False)
            if self.is_exhausted():
                self._flush_session_locked()
                self._engine_on = False
                self._session_started = None
                return True
            if self._session_elapsed() >= 30.0:
                self._flush_session_locked()
                if self.is_exhausted():
                    self._engine_on = False
                    self._session_started = None
                    return True
                self._session_started = time.monotonic()
            return False

    def _roll_day_if_needed(self) -> None:
        today = date.today().isoformat()
        if self._usage_date == today:
            return
        self._usage_date = today
        self._used_seconds = 0.0
        self._persist(force=True)

    def _flush_session_locked(self) -> None:
        if self._session_started is None:
            return
        elapsed = self._session_elapsed()
        self._session_started = None
        if elapsed <= 0:
            return
        if cloud_quota_enabled():
            if not self._push_cloud_delta(elapsed):
                self._used_seconds = min(self._limit_seconds, self._used_seconds + elapsed)
                self._persist()
            return
        self._used_seconds = min(self._limit_seconds, self._used_seconds + elapsed)
        self._persist()

    def shutdown(self) -> None:
        with _LOCK:
            if self._engine_on:
                self._flush_session_locked()
                self._engine_on = False
                self._session_started = None
            if cloud_quota_enabled():
                self._refresh_from_cloud(force=True)

    def public_status(self) -> dict:
        with _LOCK:
            self._roll_day_if_needed()
            remaining = self.remaining_seconds()
            used = self.total_used_seconds()
            limit_min = max(1, int(round(self._limit_seconds / 60)))
            remaining_min = max(0, int(round(remaining / 60)))
            return {
                'applies': True,
                'unlimited': False,
                'limit_minutes': limit_min,
                'used_minutes': max(0, int(round(used / 60))),
                'remaining_minutes': remaining_min,
                'remaining_seconds': int(round(remaining)),
                'exhausted': remaining <= 0,
                'engine_running': self._engine_on,
                'cloud_synced': self._cloud_synced,
            }


def get_ai_free_quota_manager() -> AiFreeQuotaManager:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = AiFreeQuotaManager()
    return _MANAGER


def unlimited_quota_status(*, donor: bool = False, plan: str = 'unlimited', days_left: int | None = None) -> dict:
    unlimited = plan == 'unlimited'
    return {
        'applies': False,
        'unlimited': unlimited,
        'donor': donor,
        'plan': plan,
        'days_left': days_left,
        'limit_minutes': 0,
        'used_minutes': 0,
        'remaining_minutes': 0,
        'remaining_seconds': 0,
        'exhausted': False,
        'engine_running': False,
    }
