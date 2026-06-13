"""Check and apply GitHub release updates."""

from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from app.core.config import config_dir
from app.core.github import USER_AGENT, download_bytes, get_json
from app.core.identity import APP_VERSION
from app.core.paths import is_frozen

logger = logging.getLogger('AimSync.updates')

DEFAULT_REPO = os.environ.get('AIMSYNC_UPDATES_REPO', 'AimSyncCore/AimSync')
_PREFERRED_ASSETS = (
    'AimSync.exe',
    'aimsync.exe',
    'AimSync.zip',
    'aimsync.zip',
)


def updates_dir() -> Path:
    path = config_dir() / 'updates'
    path.mkdir(parents=True, exist_ok=True)
    return path


def current_version() -> str:
    return APP_VERSION.lstrip('vV')


def parse_version(raw: str) -> tuple[int, ...]:
    text = (raw or '').strip().lstrip('vV')
    parts = [int(part) for part in re.findall(r'\d+', text)]
    return tuple(parts or (0,))


def version_lt(current: str, latest: str) -> bool:
    return parse_version(current) < parse_version(latest)


def _pick_asset(assets: list[dict[str, Any]]) -> dict[str, Any] | None:
    by_name = {str(a.get('name', '')).lower(): a for a in assets if isinstance(a, dict)}
    for name in _PREFERRED_ASSETS:
        asset = by_name.get(name.lower())
        if asset and asset.get('browser_download_url'):
            return asset
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = str(asset.get('name', '')).lower()
        if name.endswith(('.exe', '.zip')) and asset.get('browser_download_url'):
            return asset
    return None


def _latest_via_redirect(repo: str) -> tuple[str, str, str, str, str | None]:
    """Resolve latest release tag via /releases/latest redirect (no API quota)."""
    page = f'https://github.com/{repo}/releases/latest'
    req = urllib.request.Request(page, method='HEAD', headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            final = str(response.geturl() or page).strip()
    except Exception as exc:
        return '', page, '', '', str(exc)

    tag = final.rstrip('/').split('/')[-1]
    latest = tag.lstrip('vV')
    if not latest:
        return '', final, '', '', 'Could not parse release tag'

    for name in _PREFERRED_ASSETS:
        if not name.lower().endswith(('.exe', '.zip')):
            continue
        download = f'https://github.com/{repo}/releases/download/{tag}/{name}'
        head = urllib.request.Request(download, method='HEAD', headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(head, timeout=15) as probe:
                if int(getattr(probe, 'status', 200) or 200) < 400:
                    return latest, final, download, name, None
        except Exception:
            continue
    return latest, final, '', '', 'Release has no .exe or .zip asset'


def check_for_updates(*, repo: str = DEFAULT_REPO) -> dict[str, Any]:
    current = current_version()
    url = f'https://api.github.com/repos/{repo}/releases/latest'
    data, err = get_json(url, timeout=15)

    tag = ''
    latest = ''
    notes = ''
    page = ''
    asset_name = ''
    download_url = ''
    asset_size = 0

    if err or not isinstance(data, dict):
        latest, page, download_url, asset_name, fb_err = _latest_via_redirect(repo)
        if not latest:
            return {
                'success': False,
                'current_version': current,
                'latest_version': '',
                'update_available': False,
                'error': err or fb_err or 'Could not reach GitHub releases',
            }
        tag = f'v{latest}' if latest and not str(latest).startswith('v') else latest
    else:
        tag = str(data.get('tag_name') or data.get('name') or '').strip()
        latest = tag.lstrip('vV')
        assets = data.get('assets') or []
        asset = _pick_asset(assets) if isinstance(assets, list) else None
        notes = str(data.get('body') or '').strip()
        page = str(data.get('html_url') or '').strip()
        if asset:
            asset_name = str(asset.get('name') or '')
            download_url = str(asset.get('browser_download_url') or '')
            asset_size = int(asset.get('size') or 0)

    if not download_url and latest:
        latest, page, download_url, asset_name, fb_err = _latest_via_redirect(repo)
        if not download_url and fb_err:
            return {
                'success': False,
                'current_version': current,
                'latest_version': latest,
                'update_available': False,
                'error': fb_err,
            }

    update_available = bool(latest) and version_lt(current, latest) and bool(download_url)
    return {
        'success': True,
        'current_version': current,
        'latest_version': latest,
        'update_available': update_available,
        'release_notes': notes,
        'release_url': page,
        'download_url': download_url,
        'asset_name': asset_name,
        'asset_size': asset_size,
        'error': None if download_url or not update_available else 'Release has no .exe or .zip asset',
    }


def _extract_exe_from_zip(zip_path: Path) -> Path | None:
    try:
        with zipfile.ZipFile(zip_path, 'r') as archive:
            names = [name for name in archive.namelist() if name.lower().endswith('.exe')]
            if not names:
                return None
            preferred = next((n for n in names if Path(n).name.lower() == 'aimsync.exe'), names[0])
            dest = updates_dir() / 'AimSync-new.exe'
            with archive.open(preferred) as src, dest.open('wb') as out:
                out.write(src.read())
            return dest
    except Exception as exc:
        logger.warning('Zip extract failed: %s', exc)
        return None


def download_update(download_url: str, *, asset_name: str = '') -> tuple[Path | None, str | None]:
    if not download_url:
        return None, 'Missing download URL'

    data, err = download_bytes(download_url, timeout=600)
    if data is None:
        return None, err or 'Download failed'

    name = asset_name or Path(download_url).name or 'AimSync-download'
    dest = updates_dir() / name
    dest.write_bytes(data)

    if dest.suffix.lower() == '.zip':
        extracted = _extract_exe_from_zip(dest)
        if extracted is None:
            return None, 'Zip did not contain AimSync.exe'
        return extracted, None

    if dest.suffix.lower() != '.exe':
        return None, 'Unsupported update asset type'
    return dest, None


def _spawn_updater(new_exe: Path, target_exe: Path) -> tuple[bool, str]:
    bat = updates_dir() / 'apply_update.bat'
    content = (
        '@echo off\r\n'
        'timeout /t 3 /nobreak >nul\r\n'
        f'copy /Y "{new_exe}" "{target_exe}"\r\n'
        f'start "" "{target_exe}"\r\n'
        f'del /F /Q "{bat}"\r\n'
    )
    bat.write_text(content, encoding='utf-8')
    try:
        flags = 0
        if sys.platform == 'win32':
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(['cmd', '/c', str(bat)], creationflags=flags, close_fds=True)
    except Exception as exc:
        return False, str(exc)
    return True, 'Updater scheduled — AimSync will restart'


def install_update(*, repo: str = DEFAULT_REPO) -> dict[str, Any]:
    if not is_frozen():
        return {
            'success': False,
            'message': 'In-app updates apply to the built AimSync.exe only. Download the latest release manually.',
        }

    status = check_for_updates(repo=repo)
    if not status.get('success'):
        return {'success': False, 'message': status.get('error') or 'Update check failed'}
    if not status.get('update_available'):
        return {'success': False, 'message': 'Already on the latest version'}

    new_exe, err = download_update(
        str(status.get('download_url') or ''),
        asset_name=str(status.get('asset_name') or ''),
    )
    if new_exe is None:
        return {'success': False, 'message': err or 'Download failed'}

    target = Path(sys.executable).resolve()
    staged = updates_dir() / f'AimSync-{status.get("latest_version", "new")}.exe'
    if new_exe != staged:
        staged.write_bytes(new_exe.read_bytes())

    ok, message = _spawn_updater(staged, target)
    return {
        'success': ok,
        'message': message,
        'restart_required': ok,
        'latest_version': status.get('latest_version'),
    }
