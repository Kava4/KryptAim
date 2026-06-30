"""Community model catalogs — AimSync GitHub + Aimmy CS2 models."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from app.core.github import download_bytes, get_json, list_repo_contents, raw_github_url

logger = logging.getLogger('AimSync.ai.model_sources')

AIMMY_REPO = 'Babyhamsta/Aimmy'
AIMMY_REF = 'Aimmy-V2'
AIMMY_MODELS_PATH = 'models'

KRYPTAIM_REPO = os.environ.get('KRYPTAIM_MODELS_REPO', 'Kava4/AimSync')
KRYPTAIM_REF = os.environ.get('KRYPTAIM_MODELS_REF', 'main')
KRYPTAIM_CATALOG_PATH = os.environ.get('KRYPTAIM_MODELS_CATALOG', 'models/catalog.json')
KRYPTAIM_MODELS_PATH = 'models'

MODEL_EXTENSIONS = ('.onnx', '.pt', '.engine')

CS2_KEYWORDS = (
    'cs2',
    'counter-strike',
    'counter strike',
    'counterstrike',
    'cstest',
)


def is_cs2_model_name(name: str) -> bool:
    lowered = name.lower()
    return any(keyword in lowered for keyword in CS2_KEYWORDS)


def _model_entry(
    *,
    filename: str,
    title: str,
    description: str,
    size_bytes: int,
    download_url: str,
    source: str,
    game: str = 'cs2',
) -> dict[str, Any]:
    return {
        'filename': filename,
        'title': title,
        'description': description,
        'size_bytes': int(size_bytes or 0),
        'download_url': download_url,
        'game': game,
        'source': source,
    }


def _normalize_catalog_entry(raw: Any, *, default_source: str) -> dict[str, Any] | None:
    if isinstance(raw, str):
        name = Path(raw.strip()).name
        if not name or Path(name).suffix.lower() not in MODEL_EXTENSIONS:
            return None
        return _model_entry(
            filename=name,
            title=Path(name).stem,
            description='',
            size_bytes=0,
            download_url='',
            source=default_source,
        )
    if not isinstance(raw, dict):
        return None

    filename = str(
        raw.get('filename') or raw.get('name') or raw.get('file') or '',
    ).strip()
    if not filename:
        return None
    filename = Path(filename).name
    if Path(filename).suffix.lower() not in MODEL_EXTENSIONS:
        return None

    download_url = str(raw.get('download_url') or raw.get('url') or '').strip()
    if not download_url:
        download_url = raw_github_url(KRYPTAIM_REPO, KRYPTAIM_REF, f'{KRYPTAIM_MODELS_PATH}/{filename}')

    return _model_entry(
        filename=filename,
        title=str(raw.get('title') or raw.get('label') or Path(filename).stem),
        description=str(raw.get('description') or raw.get('desc') or ''),
        size_bytes=int(raw.get('size_bytes') or raw.get('size') or 0),
        download_url=download_url,
        source=str(raw.get('source') or default_source),
        game=str(raw.get('game') or 'cs2'),
    )


def fetch_aimsync_models() -> tuple[list[dict[str, Any]], str | None]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    errors: list[str] = []

    catalog_url = raw_github_url(KRYPTAIM_REPO, KRYPTAIM_REF, KRYPTAIM_CATALOG_PATH)
    catalog_data, catalog_err = get_json(catalog_url)
    if catalog_err:
        errors.append(f'catalog: {catalog_err}')
    else:
        models_raw: list[Any] = []
        if isinstance(catalog_data, dict):
            models_raw = catalog_data.get('models', []) or []
        elif isinstance(catalog_data, list):
            models_raw = catalog_data
        for raw in models_raw:
            entry = _normalize_catalog_entry(raw, default_source='aimsync')
            if entry and entry['filename'] not in seen:
                seen.add(entry['filename'])
                entries.append(entry)

    dir_items, dir_err = list_repo_contents(KRYPTAIM_REPO, KRYPTAIM_MODELS_PATH, ref=KRYPTAIM_REF)
    if dir_err:
        if dir_err != 'HTTP 404':
            errors.append(f'models/: {dir_err}')
    else:
        for item in dir_items:
            name = str(item.get('name', '')).strip()
            if not name or Path(name).suffix.lower() not in MODEL_EXTENSIONS:
                continue
            if name in seen or name == 'catalog.json':
                continue
            seen.add(name)
            entries.append(
                _model_entry(
                    filename=name,
                    title=Path(name).stem,
                    description='AimSync model',
                    size_bytes=int(item.get('size') or 0),
                    download_url=str(item.get('download_url') or raw_github_url(
                        KRYPTAIM_REPO, KRYPTAIM_REF, f'{KRYPTAIM_MODELS_PATH}/{name}',
                    )),
                    source='aimsync',
                ),
            )

    if entries:
        return entries, None
    if errors:
        return [], '; '.join(errors)
    return [], None


def fetch_aimmy_cs2_models() -> tuple[list[dict[str, Any]], str | None]:
    items, err = list_repo_contents(AIMMY_REPO, AIMMY_MODELS_PATH, ref=AIMMY_REF)
    if err:
        return [], err

    entries: list[dict[str, Any]] = []
    for item in items:
        name = str(item.get('name', '')).strip()
        if not name or Path(name).suffix.lower() not in MODEL_EXTENSIONS:
            continue
        if not is_cs2_model_name(name):
            continue
        entries.append(
            _model_entry(
                filename=name,
                title=Path(name).stem,
                description='Aimmy community model (CS2)',
                size_bytes=int(item.get('size') or 0),
                download_url=str(
                    item.get('download_url')
                    or raw_github_url(AIMMY_REPO, AIMMY_REF, f'{AIMMY_MODELS_PATH}/{name}'),
                ),
                source='aimmy',
            ),
        )
    entries.sort(key=lambda entry: entry['filename'].lower())
    return entries, None


def fetch_all_community_models() -> dict[str, Any]:
    aimsync, aimsync_err = fetch_aimsync_models()
    aimmy, aimmy_err = fetch_aimmy_cs2_models()

    catalog: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in aimsync + aimmy:
        filename = entry['filename']
        if filename in seen:
            continue
        seen.add(filename)
        catalog.append(entry)

    errors: list[str] = []
    if aimsync_err:
        errors.append(f'AimSync: {aimsync_err}')
    if aimmy_err:
        errors.append(f'Aimmy: {aimmy_err}')

    online = aimmy_err is None or aimsync_err is None or bool(catalog)
    error = None
    if not catalog and errors:
        error = '; '.join(errors)
    elif errors and not aimsync:
        error = errors[0]

    return {
        'models': catalog,
        'online': online,
        'error': error,
        'sources': {
            'aimsync': {'count': len(aimsync), 'error': aimsync_err},
            'aimmy': {'count': len(aimmy), 'error': aimmy_err},
        },
    }


def download_model_from_url(url: str) -> tuple[bytes | None, str | None]:
    if not url:
        return None, 'Missing download URL'
    return download_bytes(url)
