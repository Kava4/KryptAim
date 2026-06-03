"""Model and config file management + community store."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import requests

from Config.config_manager import get_ai_configs_dir, get_models_dir

logger = logging.getLogger('AimSync.AI.Models')

GITHUB_MODELS_API = 'https://api.github.com/repos/BabyHamsta/Aimmy/contents/models'
GITHUB_CONFIGS_API = 'https://api.github.com/repos/BabyHamsta/Aimmy/contents/configs'
GITHUB_RAW_BASE = 'https://github.com/BabyHamsta/Aimmy/raw/Aimmy-V2'


def list_local_models() -> list[str]:
    return sorted(path.name for path in get_models_dir().glob('*.onnx'))


def list_local_configs() -> list[str]:
    return sorted(path.name for path in get_ai_configs_dir().glob('*.cfg'))


def resolve_model_path(filename: str) -> Path | None:
    if not filename:
        return None
    path = get_models_dir() / filename
    return path if path.is_file() else None


def save_uploaded_model(filename: str, data: bytes) -> Path:
    if not filename.lower().endswith('.onnx'):
        raise ValueError('Only .onnx models are supported.')
    dest = get_models_dir() / Path(filename).name
    dest.write_bytes(data)
    return dest


def delete_model(filename: str) -> bool:
    path = get_models_dir() / filename
    if path.is_file():
        path.unlink()
        return True
    return False


def fetch_store_listing(api_url: str) -> list[str]:
    headers = {
        'User-Agent': 'AimSync-Beta',
        'Accept': 'application/vnd.github.v3+json',
    }
    response = requests.get(api_url, headers=headers, timeout=30)
    response.raise_for_status()
    payload = response.json()
    names = []
    for item in payload:
        name = item.get('name')
        if name:
            names.append(name)
    return sorted(names)


def download_store_file(folder: str, filename: str) -> Path:
    url = f'{GITHUB_RAW_BASE}/{folder}/{filename}'
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    if folder == 'models':
        dest = get_models_dir() / filename
    else:
        dest = get_ai_configs_dir() / filename
    dest.write_bytes(response.content)
    return dest


def import_external_model(source: Path) -> Path:
    dest = get_models_dir() / source.name
    if source.resolve() == dest.resolve():
        return dest
    shutil.copy2(source, dest)
    return dest
