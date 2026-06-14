"""Load protected modules from maintainer source or sealed blobs."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from app.protected.crypto import unseal_bytes

logger = logging.getLogger('KryptAim.protected')

_BUILTIN_MODULES = frozenset({
    'recoil/engine.py',
    'recoil/weapon_data.py',
    'ai/engine.py',
    'ai/inference.py',
    'ai/targets.py',
    'ai/aim.py',
    'ai/trigger.py',
    'core/licensing.py',
})

_CACHE: dict[str, str] = {}


def _protected_dir() -> Path:
    candidates: list[Path] = [Path(__file__).resolve().parent]
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            candidates.append(Path(meipass) / 'app' / 'protected')
    for path in candidates:
        if (path / 'manifest.json').is_file() or (path / 'sealed').is_dir():
            return path
    return candidates[0]


def _app_root() -> Path:
    return _protected_dir().parent


class ProtectedModuleError(ImportError):
    pass


def _manifest_modules() -> set[str]:
    manifest = _protected_dir() / 'manifest.json'
    if manifest.is_file():
        data = json.loads(manifest.read_text(encoding='utf-8'))
        return {str(item).replace('\\', '/') for item in data.get('modules', [])}
    return set(_BUILTIN_MODULES)


def _rel_from_qualified(qualified: str) -> str:
    prefix = 'app.'
    if not qualified.startswith(prefix):
        raise ProtectedModuleError(f'Not an app module: {qualified}')
    return qualified[len(prefix):].replace('.', '/') + '.py'


def _src_path(rel: str) -> Path:
    return _app_root() / '_src' / rel


def _sealed_path(rel: str) -> Path:
    safe = rel.replace('/', '__')
    return _protected_dir() / 'sealed' / f'{safe}.bin'


def _read_source(rel: str) -> str:
    if rel in _CACHE:
        return _CACHE[rel]

    src = _src_path(rel)
    if src.is_file():
        text = src.read_text(encoding='utf-8')
        _CACHE[rel] = text
        return text

    sealed = _sealed_path(rel)
    if sealed.is_file():
        text = unseal_bytes(sealed.read_bytes()).decode('utf-8')
        _CACHE[rel] = text
        return text

    raise ProtectedModuleError(
        f'Protected module missing: {rel}. '
        'Maintainers: keep plaintext in app/_src/ or run scripts\\seal_protected.bat'
    )


def bind_protected_module(qualified: str) -> None:
    rel = _rel_from_qualified(qualified)
    if rel not in _manifest_modules():
        raise ProtectedModuleError(f'Module not in protected manifest: {rel}')

    mod = sys.modules.get(qualified)
    if mod is None:
        raise ProtectedModuleError(f'Module not initialized: {qualified}')

    source = _read_source(rel)
    code = compile(source, str(_src_path(rel) if _src_path(rel).is_file() else sealed_path_display(rel)), 'exec', dont_inherit=True)
    exec(code, mod.__dict__)  # noqa: S102


def sealed_path_display(rel: str) -> str:
    return f'app/protected/sealed/{rel.replace("/", "__")}.bin'
