import sys
from pathlib import Path

from Config.version import APP_VERSION, APP_VERSION_LABEL


def get_app_name() -> str:
    return 'AimSync'


def get_app_storage_dirname() -> str:
    return 'AimSync'


def get_build_name() -> str:
    return 'AimSync'


def get_app_version() -> str:
    return APP_VERSION


def get_app_version_label() -> str:
    return APP_VERSION_LABEL


def resolve_app_data_dir() -> Path:
    """%APPDATA%\\AimSync, with fallback to legacy AimSyncBeta if present."""
    import os

    base = Path(os.environ.get('APPDATA', Path.home()))
    current = base / get_app_storage_dirname()
    legacy = base / 'AimSyncBeta'
    if legacy.is_dir() and not (current / 'config.json').is_file():
        if (legacy / 'config.json').is_file():
            return legacy
    current.mkdir(parents=True, exist_ok=True)
    return current
