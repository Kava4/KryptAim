"""AppData Python venv for AI stack (slim exe + first-run install)."""

from __future__ import annotations

import logging
import subprocess
import sys
import threading
from pathlib import Path

from app.bootstrap.embed_python import (
    PYTHON_EMBED_VERSION,
    create_runtime_venv,
    embed_python_exe,
    embed_root,
    is_embed_ready,
)
from app.bootstrap.paths import runtime_dir
from app.bootstrap.progress import (
    append_install_log,
    install_progress,
    mark_install_done,
    mark_install_failed,
    reset_install_progress,
    set_install_phase,
)
from app.core.paths import app_root, is_frozen

logger = logging.getLogger('KryptAim.bootstrap')

_install_lock = threading.Lock()
_install_in_progress = False
_install_error = ''

_READY_FILE = '.ready'
_TORCH_INDEX = 'https://download.pytorch.org/whl/cu126'


def runtime_venv_python() -> Path:
    return runtime_dir() / 'venv' / 'Scripts' / 'python.exe'


def runtime_site_packages() -> Path:
    return runtime_dir() / 'venv' / 'Lib' / 'site-packages'


def _ready_marker() -> Path:
    return runtime_dir() / _READY_FILE


def is_runtime_ready() -> bool:
    return _ready_marker().is_file() and runtime_venv_python().is_file()


def bundled_ai_stack() -> bool:
    """Full PyInstaller build ships torch inside _internal."""
    if not is_frozen():
        return True
    try:
        import importlib.util

        return importlib.util.find_spec('torch') is not None
    except Exception:
        return False


def patch_sys_path_for_runtime() -> bool:
    if bundled_ai_stack():
        return True
    if not is_runtime_ready():
        return False
    site = runtime_site_packages()
    if not site.is_dir():
        return False
    path = str(site)
    if path not in sys.path:
        sys.path.insert(0, path)
    return True


def is_ai_available() -> bool:
    if bundled_ai_stack():
        return True
    if not patch_sys_path_for_runtime():
        return False
    try:
        import cv2  # noqa: F401

        return True
    except ImportError:
        return False


def _requirements_file() -> Path | None:
    for candidate in (
        app_root() / 'requirements.txt',
        Path(getattr(sys, '_MEIPASS', '')) / 'requirements.txt',
    ):
        if candidate.is_file():
            return candidate
    dev = Path(__file__).resolve().parents[2] / 'requirements.txt'
    return dev if dev.is_file() else None


def _python_launchers() -> list[list[str]]:
    return [
        ['py', '-3.12'],
        ['py', '-3.11'],
        ['py', '-3.10'],
        ['py', '-3'],
        ['python'],
    ]


def _find_system_python() -> list[str] | None:
    for cmd in _python_launchers():
        try:
            subprocess.run(
                [*cmd, '-c', 'import sys; assert sys.version_info >= (3, 10)'],
                check=True,
                capture_output=True,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
            )
            return cmd
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            continue
    return None


def _run(cmd: list[str], *, cwd: Path | None = None, log_pip: bool = False) -> None:
    line = ' '.join(cmd)
    logger.info('run: %s', line)
    append_install_log(f'> {line}')
    kwargs: dict = {
        'check': True,
        'cwd': str(cwd) if cwd else None,
        'creationflags': getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    }
    if log_pip:
        from app.bootstrap.progress import install_log_path

        with install_log_path().open('a', encoding='utf-8') as handle:
            subprocess.run(cmd, stdout=handle, stderr=subprocess.STDOUT, **kwargs)
        return
    subprocess.run(cmd, **kwargs)


def _create_venv(venv_root: Path) -> Path:
    """Prefer embeddable Python; fall back to system Python if embed fails."""
    try:
        return create_runtime_venv(venv_root)
    except Exception as exc:
        logger.warning('Embeddable Python setup failed (%s), trying system Python', exc)
        launcher = _find_system_python()
        if launcher is None:
            raise RuntimeError(
                'Could not set up embeddable Python and no system Python 3.10+ found'
            ) from exc
        if venv_root.exists():
            import shutil

            shutil.rmtree(venv_root, ignore_errors=True)
        _run([*launcher, '-m', 'venv', str(venv_root)])
        return runtime_venv_python()


def install_runtime(*, install_cuda_torch: bool = True) -> tuple[bool, str]:
    """Create %APPDATA%\\KryptAim\\runtime\\venv and pip install AI deps."""
    global _install_in_progress, _install_error

    with _install_lock:
        if _install_in_progress:
            return False, 'Install already running'
        if is_runtime_ready() and is_ai_available():
            return True, 'Already installed'
        _install_in_progress = True
        _install_error = ''
        reset_install_progress()

    try:
        req = _requirements_file()
        if req is None:
            msg = 'requirements.txt missing in app bundle'
            _install_error = msg
            mark_install_failed(msg)
            return False, msg

        venv_root = runtime_dir() / 'venv'
        venv_py = _create_venv(venv_root)

        pip = [str(venv_py), '-m', 'pip']
        set_install_phase('pip_upgrade', 'Upgrading pip in venv…')
        _run([*pip, 'install', '-U', 'pip'], log_pip=True)
        set_install_phase('pip_requirements', 'Installing AI packages (may take 10–20 min)…')
        _run([*pip, 'install', '-r', str(req)], log_pip=True)

        if install_cuda_torch:
            set_install_phase('pip_torch', 'Installing CUDA PyTorch wheels…')
            try:
                _run(
                    [
                        *pip,
                        'install',
                        '--force-reinstall',
                        '--no-cache-dir',
                        'torch',
                        'torchvision',
                        'torchaudio',
                        '--index-url',
                        _TORCH_INDEX,
                    ],
                    log_pip=True,
                )
            except subprocess.CalledProcessError:
                logger.warning('CUDA torch install failed — CPU onnx may still work')
                append_install_log('WARN: CUDA torch install failed')

        set_install_phase('verify', 'Verifying imports…')
        _run(
            [
                str(venv_py),
                '-c',
                'import flask, ultralytics, cv2, numpy, cyndilib, onnxruntime',
            ],
        )

        _ready_marker().write_text('ok\n', encoding='utf-8')
        patch_sys_path_for_runtime()
        msg = 'AI runtime installed — restart KryptAim'
        mark_install_done(msg)
        return True, msg
    except subprocess.CalledProcessError as exc:
        msg = f'Install failed (exit {exc.returncode}) — see install.log'
        _install_error = msg
        mark_install_failed(msg)
        return False, msg
    except Exception as exc:
        msg = str(exc) or 'Install failed'
        _install_error = msg
        mark_install_failed(msg)
        return False, msg
    finally:
        with _install_lock:
            _install_in_progress = False


def bootstrap_status() -> dict:
    progress = install_progress()
    return {
        'frozen': is_frozen(),
        'bundled_ai': bundled_ai_stack(),
        'embed_ready': is_embed_ready(),
        'embed_python': str(embed_python_exe()) if embed_python_exe().is_file() else '',
        'embed_version': PYTHON_EMBED_VERSION,
        'runtime_ready': is_runtime_ready(),
        'ai_available': is_ai_available(),
        'install_in_progress': _install_in_progress,
        'install_error': _install_error,
        'install_phase': progress['phase'],
        'install_message': progress['message'],
        'install_elapsed_sec': progress['elapsed_sec'],
        'install_log': progress['install_log'],
        'install_log_tail': progress['log_tail'],
        'runtime_dir': str(runtime_dir()),
        'embed_dir': str(embed_root()),
        'needs_bootstrap': is_frozen() and not bundled_ai_stack() and not is_ai_available(),
    }
