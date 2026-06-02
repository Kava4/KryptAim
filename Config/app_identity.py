import os
import sys
from pathlib import Path

from Config.version import APP_VERSION, APP_VERSION_LABEL


STABLE_CHANNEL = 'stable'
BETA_CHANNEL = 'beta'


def get_app_channel() -> str:
    env_channel = os.environ.get('AIMSYNC_CHANNEL', '').strip().lower()
    if env_channel in {STABLE_CHANNEL, BETA_CHANNEL}:
        return env_channel

    executable_name = Path(sys.executable).stem.lower() if getattr(sys, 'frozen', False) else ''
    if 'beta' in executable_name:
        return BETA_CHANNEL
    return STABLE_CHANNEL


def is_beta_channel() -> bool:
    return get_app_channel() == BETA_CHANNEL


def get_app_name() -> str:
    return 'AimSync Beta' if is_beta_channel() else 'AimSync'


def get_app_storage_dirname() -> str:
    return 'AimSyncBeta' if is_beta_channel() else 'AimSync'


def get_build_name() -> str:
    return 'AimSyncBeta' if is_beta_channel() else 'AimSync'


def get_helper_build_name() -> str:
    return 'AimSyncBetaHelper'


def get_app_version() -> str:
    return APP_VERSION


def get_app_version_label() -> str:
    if is_beta_channel():
        return f'{APP_VERSION_LABEL} Beta'
    return APP_VERSION_LABEL
