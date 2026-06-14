"""Download and configure Windows embeddable CPython in AppData."""

from __future__ import annotations

import logging
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

from app.bootstrap.paths import runtime_dir
from app.bootstrap.progress import append_install_log, set_install_phase

logger = logging.getLogger('KryptAim.bootstrap')

PYTHON_EMBED_VERSION = '3.12.10'
GET_PIP_URL = 'https://bootstrap.pypa.io/get-pip.py'
_EMBED_READY = '.embed_ready'


def embed_root() -> Path:
    return runtime_dir() / 'embed'


def embed_python_exe() -> Path:
    return embed_root() / 'python.exe'


def embed_ready_marker() -> Path:
    return embed_root() / _EMBED_READY


def embed_zip_url(version: str = PYTHON_EMBED_VERSION) -> str:
    return f'https://www.python.org/ftp/python/{version}/python-{version}-embed-amd64.zip'


def is_embed_ready() -> bool:
    return (
        embed_ready_marker().is_file()
        and embed_python_exe().is_file()
    )


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(
        cmd,
        check=True,
        cwd=str(cwd) if cwd else None,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    )


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    logger.info('Downloading %s', url)
    append_install_log(f'Downloading {url}')
    urllib.request.urlretrieve(url, dest)


def _configure_embed_pth(root: Path) -> None:
    site_dir = root / 'Lib' / 'site-packages'
    site_dir.mkdir(parents=True, exist_ok=True)
    pth_files = list(root.glob('python*._pth'))
    if not pth_files:
        raise RuntimeError(f'No python*._pth in {root}')
    zip_name = next((p.name for p in root.glob('python*.zip')), 'python312.zip')
    pth_files[0].write_text(
        f'{zip_name}\n.\nLib\\site-packages\nimport site\n',
        encoding='utf-8',
    )


def ensure_embed_python(*, version: str = PYTHON_EMBED_VERSION) -> Path:
    """Download embed zip, enable pip, return python.exe path."""
    if is_embed_ready():
        return embed_python_exe()

    set_install_phase('download_embed', f'Downloading Python {version} embeddable zip…')
    root = embed_root()
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)

    zip_path = runtime_dir() / f'python-{version}-embed-amd64.zip'
    if not zip_path.is_file():
        _download(embed_zip_url(version), zip_path)

    with zipfile.ZipFile(zip_path, 'r') as archive:
        archive.extractall(root)

    set_install_phase('configure_embed', 'Configuring embeddable Python…')
    _configure_embed_pth(root)

    get_pip = runtime_dir() / 'get-pip.py'
    if not get_pip.is_file():
        _download(GET_PIP_URL, get_pip)

    set_install_phase('install_pip', 'Installing pip + virtualenv…')
    _run([str(embed_python_exe()), str(get_pip)])

    _run([str(embed_python_exe()), '-m', 'pip', 'install', '-U', 'pip', 'virtualenv'])

    embed_ready_marker().write_text(f'{version}\n', encoding='utf-8')
    logger.info('Embeddable Python %s ready at %s', version, root)
    return embed_python_exe()


def create_runtime_venv(venv_path: Path) -> Path:
    """Create venv using embeddable Python + virtualenv."""
    set_install_phase('create_venv', 'Creating Python venv in AppData…')
    embed_py = ensure_embed_python()
    if venv_path.exists():
        shutil.rmtree(venv_path, ignore_errors=True)
    _run([str(embed_py), '-m', 'virtualenv', str(venv_path)])
    venv_python = venv_path / 'Scripts' / 'python.exe'
    if not venv_python.is_file():
        raise RuntimeError(f'venv python missing: {venv_python}')
    return venv_python
