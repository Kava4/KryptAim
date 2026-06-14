"""Community YOLO models — KryptAim GitHub + Aimmy CS2 catalog."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.ai.model_sources import fetch_all_community_models, download_model_from_url
from app.core.config import config_dir

logger = logging.getLogger('KryptAim.ai.community')

MODEL_EXTENSIONS = ('.onnx', '.pt', '.engine')


def models_dir() -> Path:
    path = config_dir() / 'models'
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_local_model_names() -> list[str]:
    names: set[str] = set()
    for ext in MODEL_EXTENSIONS:
        names.update(p.name for p in models_dir().glob(f'*{ext}'))
    return sorted(names)


def _normalize_entry(raw: Any) -> dict[str, Any] | None:
    if isinstance(raw, str):
        name = Path(raw.strip()).name
        if not name or Path(name).suffix.lower() not in MODEL_EXTENSIONS:
            return None
        return {
            'filename': Path(name).name,
            'title': Path(name).stem,
            'description': '',
            'size_bytes': 0,
            'download_url': '',
            'game': 'cs2',
            'source': 'unknown',
        }
    if not isinstance(raw, dict):
        return None
    filename = (
        raw.get('filename')
        or raw.get('name')
        or raw.get('file')
        or ''
    )
    filename = str(filename).strip()
    if not filename:
        return None
    filename = Path(filename).name
    if Path(filename).suffix.lower() not in MODEL_EXTENSIONS:
        return None
    return {
        'filename': filename,
        'title': str(raw.get('title') or raw.get('label') or Path(filename).stem),
        'description': str(raw.get('description') or raw.get('desc') or ''),
        'size_bytes': int(raw.get('size_bytes') or raw.get('size') or 0),
        'download_url': str(raw.get('download_url') or raw.get('url') or ''),
        'game': str(raw.get('game') or 'cs2'),
        'source': str(raw.get('source') or 'unknown'),
    }


def community_models_status() -> dict[str, Any]:
    local = set(list_local_model_names())
    remote_payload = fetch_all_community_models()
    online = bool(remote_payload.get('online'))
    error = remote_payload.get('error')

    catalog: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in remote_payload.get('models', []):
        entry = _normalize_entry(raw)
        if entry is None or entry['filename'] in seen:
            continue
        seen.add(entry['filename'])
        entry['installed'] = entry['filename'] in local
        catalog.append(entry)

    available = [m for m in catalog if not m['installed']]
    installed = [m for m in catalog if m['installed']]

    all_ready = online and bool(catalog) and not available

    return {
        'online': online,
        'error': error,
        'catalog': catalog,
        'available': available,
        'installed': installed,
        'local_models': sorted(local),
        'all_installed': all_ready,
        'empty_catalog': online and not catalog,
        'sources': remote_payload.get('sources', {}),
    }


def download_community_model(filename: str) -> tuple[Path | None, str]:
    name = Path(filename).name
    if Path(name).suffix.lower() not in MODEL_EXTENSIONS:
        return None, 'Unsupported model type'

    dest = models_dir() / name
    if dest.is_file() and dest.stat().st_size > 1024:
        return dest, 'Already installed'

    download_url = ''
    status = community_models_status()
    for entry in status.get('catalog', []):
        if entry.get('filename') == name:
            download_url = str(entry.get('download_url') or '')
            break

    if not download_url:
        return None, 'Model not found in catalog'

    data, err = download_model_from_url(download_url)
    if data is None:
        return None, err or 'Download failed'

    dest.write_bytes(data)
    logger.info('Community model saved: %s (%d bytes)', dest, len(data))
    return dest, 'Downloaded'
