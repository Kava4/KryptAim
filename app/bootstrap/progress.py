"""Bootstrap install progress (polled by /api/bootstrap/status)."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from app.bootstrap.paths import runtime_dir

logger = logging.getLogger('AimSync.bootstrap')

_install_phase = 'idle'
_install_message = ''
_install_started_at: float | None = None

PHASES = (
    'idle',
    'starting',
    'download_embed',
    'configure_embed',
    'install_pip',
    'create_venv',
    'pip_upgrade',
    'pip_requirements',
    'pip_torch',
    'verify',
    'done',
    'failed',
)


def install_log_path() -> Path:
    return runtime_dir() / 'install.log'


def reset_install_progress() -> None:
    global _install_phase, _install_message, _install_started_at
    _install_phase = 'starting'
    _install_message = 'Starting AI runtime install…'
    _install_started_at = time.time()
    log = install_log_path()
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(f'=== AimSync AI runtime install {time.strftime("%Y-%m-%d %H:%M:%S")} ===\n', encoding='utf-8')


def set_install_phase(phase: str, message: str = '') -> None:
    global _install_phase, _install_message
    if phase not in PHASES:
        phase = 'starting'
    _install_phase = phase
    _install_message = message or phase.replace('_', ' ').title()
    logger.info('bootstrap [%s] %s', phase, _install_message)
    try:
        with install_log_path().open('a', encoding='utf-8') as handle:
            handle.write(f'[{phase}] {_install_message}\n')
    except OSError:
        pass


def append_install_log(line: str) -> None:
    try:
        with install_log_path().open('a', encoding='utf-8') as handle:
            handle.write(line.rstrip() + '\n')
    except OSError:
        pass


def install_progress() -> dict:
    elapsed = 0.0
    if _install_started_at is not None:
        elapsed = max(0.0, time.time() - _install_started_at)
    log = install_log_path()
    tail: list[str] = []
    if log.is_file():
        try:
            lines = log.read_text(encoding='utf-8', errors='replace').splitlines()
            tail = lines[-8:]
        except OSError:
            pass
    return {
        'phase': _install_phase,
        'message': _install_message,
        'elapsed_sec': round(elapsed, 1),
        'install_log': str(log) if log.parent.exists() else '',
        'log_tail': tail,
    }


def mark_install_done(message: str = 'AI runtime installed — restart AimSync') -> None:
    set_install_phase('done', message)


def mark_install_failed(message: str) -> None:
    set_install_phase('failed', message)
