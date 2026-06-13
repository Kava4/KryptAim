"""App identity."""

from __future__ import annotations

import json
from pathlib import Path

APP_NAME = 'AimSync'
APP_DISPLAY_NAME = 'AimSync'
APP_STORAGE_DIR = 'AimSync'
APP_VERSION_LABEL = 'Early Access'


def _read_shipped_version() -> tuple[str, str]:
    candidates = [
        Path(__file__).resolve().parents[2] / 'release' / 'version.json',
        Path(__file__).resolve().parents[1] / 'release' / 'version.json',
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            version = str(data.get('version') or '').strip()
            label = str(data.get('label') or APP_VERSION_LABEL).strip()
            if version:
                return version, label
        except Exception:
            pass
    return '0.1.0-dev', APP_VERSION_LABEL


APP_VERSION, APP_VERSION_LABEL = _read_shipped_version()
