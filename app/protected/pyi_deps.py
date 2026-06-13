"""PyInstaller dependency hooks for modules only referenced inside sealed blobs."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTECTED = ROOT / 'app' / 'protected'
SRC = ROOT / 'app' / '_src'
SEALED = PROTECTED / 'sealed'
MANIFEST = PROTECTED / 'manifest.json'


def _sealed_blob_path(rel: str) -> Path:
    return SEALED / f"{rel.replace('/', '__')}.bin"


def _protected_sources() -> list[str]:
    if not MANIFEST.is_file():
        return []
    rels = [str(item).replace('\\', '/') for item in json.loads(MANIFEST.read_text(encoding='utf-8')).get('modules', [])]
    sources: list[str] = []
    for rel in rels:
        plaintext = SRC / rel
        if plaintext.is_file():
            sources.append(plaintext.read_text(encoding='utf-8'))
            continue
        blob = _sealed_blob_path(rel)
        if blob.is_file():
            from app.protected.crypto import unseal_bytes

            sources.append(unseal_bytes(blob.read_bytes()).decode('utf-8'))
    return sources


def _app_imports(source: str) -> set[str]:
    found: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return found
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('app.'):
            found.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith('app.'):
                    found.add(alias.name)
    return found


def protected_hidden_imports() -> tuple[str, ...]:
    """Return app.* modules PyInstaller must bundle for sealed protected code."""
    modules: set[str] = set()
    for source in _protected_sources():
        modules |= _app_imports(source)

    sealed_stubs: set[str] = set()
    if MANIFEST.is_file():
        for rel in json.loads(MANIFEST.read_text(encoding='utf-8')).get('modules', []):
            rel = str(rel).replace('\\', '/').removesuffix('.py').replace('/', '.')
            sealed_stubs.add(f'app.{rel}')

    # Stubs are imported only from inside other sealed blobs — invisible to static analysis.
    modules |= sealed_stubs
    return tuple(sorted(modules))
