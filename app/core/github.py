"""GitHub API + raw download helpers."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger('KryptAim.github')

USER_AGENT = 'KryptAim'
DEFAULT_TIMEOUT = 15.0
DOWNLOAD_TIMEOUT = 300.0


def _github_token() -> str:
    return (
        os.environ.get('KRYPTAIM_GITHUB_TOKEN', '').strip()
        or os.environ.get('AIMSYNC_GITHUB_TOKEN', '').strip()
        or os.environ.get('GITHUB_TOKEN', '').strip()
        or os.environ.get('GH_TOKEN', '').strip()
    )


def _request(url: str, *, timeout: float = DEFAULT_TIMEOUT) -> tuple[bytes | None, str | None]:
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/vnd.github+json',
    }
    token = _github_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read(), None
    except urllib.error.HTTPError as exc:
        return None, f'HTTP {exc.code}'
    except Exception as exc:
        logger.warning('GitHub request failed for %s: %s', url, exc)
        return None, str(exc) or 'Request failed'


def get_json(url: str, *, timeout: float = DEFAULT_TIMEOUT) -> tuple[Any | None, str | None]:
    raw, err = _request(url, timeout=timeout)
    if err or raw is None:
        return None, err
    try:
        return json.loads(raw.decode('utf-8', errors='replace')), None
    except json.JSONDecodeError:
        return None, 'Invalid JSON'


def list_repo_contents(repo: str, path: str, *, ref: str) -> tuple[list[dict[str, Any]], str | None]:
    safe_path = '/'.join(urllib.parse.quote(part) for part in path.strip('/').split('/'))
    url = f'https://api.github.com/repos/{repo}/contents/{safe_path}?ref={urllib.parse.quote(ref)}'
    data, err = get_json(url)
    if err:
        return [], err
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)], None
    if isinstance(data, dict):
        return [data], None
    return [], 'Unexpected GitHub response'


def raw_github_url(repo: str, ref: str, path: str) -> str:
    safe_path = '/'.join(urllib.parse.quote(part) for part in path.strip('/').split('/'))
    return f'https://raw.githubusercontent.com/{repo}/{ref}/{safe_path}'


def download_bytes(url: str, *, timeout: float = DOWNLOAD_TIMEOUT) -> tuple[bytes | None, str | None]:
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()
            if len(data) < 1024:
                return None, 'Download too small — file may be missing'
            return data, None
    except Exception as exc:
        logger.warning('Download failed for %s: %s', url, exc)
        return None, str(exc) or 'Download failed'
