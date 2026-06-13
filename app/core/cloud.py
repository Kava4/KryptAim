"""AimSync cloud API client (patterns, community models)."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger('AimSync.cloud')

DEFAULT_CLOUD_API = 'https://project-mkgdr.vercel.app/api'


def cloud_api_base() -> str:
    return os.environ.get('AIMSYNC_CLOUD_API', DEFAULT_CLOUD_API).rstrip('/')


def _get_json(path: str, *, timeout: float = 12) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
    url = f'{cloud_api_base()}/{path.lstrip("/")}'
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read().decode('utf-8', errors='replace')
            return json.loads(raw), None
    except urllib.error.HTTPError as exc:
        return None, f'HTTP {exc.code}'
    except Exception as exc:
        logger.warning('Cloud GET %s failed: %s', url, exc)
        return None, str(exc) or 'Cloud unreachable'


def _post_json(path: str, payload: dict, *, timeout: float = 12) -> tuple[dict[str, Any] | None, str | None]:
    url = f'{cloud_api_base()}/{path.lstrip("/")}'
    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode('utf-8', errors='replace')
            data = json.loads(raw)
            return data if isinstance(data, dict) else {'data': data}, None
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode('utf-8', errors='replace')[:200]
        except Exception:
            detail = ''
        return None, f'HTTP {exc.code}' + (f': {detail}' if detail else '')
    except Exception as exc:
        logger.warning('Cloud POST %s failed: %s', url, exc)
        return None, str(exc) or 'Cloud unreachable'


def fetch_patterns() -> dict[str, Any]:
    data, error = _get_json('patterns')
    if error:
        return {'patterns': [], 'online': False, 'error': error}
    patterns = []
    if isinstance(data, dict):
        patterns = data.get('patterns', []) or []
    return {'patterns': patterns, 'online': True, 'error': None}


def fetch_community_models() -> dict[str, Any]:
    data, error = _get_json('models')
    if error:
        return {'models': [], 'online': False, 'error': error}
    models_raw: list[Any] = []
    if isinstance(data, dict):
        models_raw = data.get('models', []) or []
    elif isinstance(data, list):
        models_raw = data
    return {'models': models_raw, 'online': True, 'error': None}


def download_community_model_bytes(name: str, *, download_url: str = '') -> tuple[bytes | None, str | None]:
    safe = urllib.parse.quote(name, safe='')
    if download_url:
        url = download_url
    else:
        url = f'{cloud_api_base()}/model/download?name={safe}'
    try:
        with urllib.request.urlopen(url, timeout=300) as response:
            data = response.read()
            if data[:1] == b'{':
                try:
                    payload = json.loads(data.decode('utf-8', errors='replace'))
                    if isinstance(payload, dict) and payload.get('error'):
                        return None, str(payload['error'])
                except json.JSONDecodeError:
                    pass
            if len(data) < 1024:
                return None, 'Download too small — file may be missing on the server'
            return data, None
    except Exception as exc:
        logger.warning('Model download failed for %s: %s', name, exc)
        return None, str(exc) or 'Download failed'
