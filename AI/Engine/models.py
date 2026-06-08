"""Model and config file management (local files only)."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from Config.config_manager import get_ai_configs_dir, get_models_dir

logger = logging.getLogger('AimSync.AI.Models')

MODEL_EXTENSIONS = ('.onnx', '.pt', '.engine')
STORE_MODEL_EXTENSIONS = ('.onnx',)

# Remote community catalogs disabled — use local upload / bin/models only.
COMMUNITY_STORE_ENABLED = False
COMMUNITY_STORE_MESSAGE = (
    'Community model download is disabled. Copy .onnx files into bin/models '
    'or upload via the AI panel.'
)


def list_local_models() -> list[str]:
    names: set[str] = set()
    for ext in MODEL_EXTENSIONS:
        names.update(path.name for path in get_models_dir().glob(f'*{ext}'))
    return sorted(names)


def list_local_configs() -> list[str]:
    return sorted(path.name for path in get_ai_configs_dir().glob('*.cfg'))


def resolve_model_path(filename: str) -> Path | None:
    if not filename:
        return None
    path = get_models_dir() / filename
    return path if path.is_file() else None


def save_uploaded_model(filename: str, data: bytes) -> Path:
    if not filename.lower().endswith(MODEL_EXTENSIONS):
        raise ValueError('Supported models: .onnx, .pt, .engine')
    dest = get_models_dir() / Path(filename).name
    dest.write_bytes(data)
    return dest


def delete_model(filename: str) -> bool:
    path = get_models_dir() / filename
    if path.is_file():
        path.unlink()
        return True
    return False


def fetch_store_listing(_api_url: str) -> list[str]:
    if not COMMUNITY_STORE_ENABLED:
        return []
    return []


def download_store_file(folder: str, filename: str) -> Path:
    raise RuntimeError(COMMUNITY_STORE_MESSAGE)


def import_external_model(source: Path) -> Path:
    dest = get_models_dir() / source.name
    if source.resolve() == dest.resolve():
        return dest
    shutil.copy2(source, dest)
    return dest
