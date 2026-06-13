"""Encrypt app/_src modules into app/protected/sealed/*.bin for public distribution."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.protected.crypto import seal_bytes  # noqa: E402

APP = ROOT / 'app'
SRC = APP / '_src'
SEALED = APP / 'protected' / 'sealed'
MANIFEST = APP / 'protected' / 'manifest.json'


def main() -> int:
    modules = json.loads(MANIFEST.read_text(encoding='utf-8')).get('modules', [])
    if not modules:
        print('No modules listed in manifest.json')
        return 1

    SEALED.mkdir(parents=True, exist_ok=True)
    sealed = 0
    for rel in modules:
        rel = str(rel).replace('\\', '/')
        src = SRC / rel
        if not src.is_file():
            fallback = APP / rel
            if fallback.is_file():
                src = fallback
            else:
                print(f'SKIP missing source: {rel}')
                continue
        payload = seal_bytes(src.read_bytes())
        out = SEALED / f"{rel.replace('/', '__')}.bin"
        out.write_bytes(payload)
        sealed += 1
        print(f'Sealed: {rel} -> {out.name} ({len(payload)} bytes)')

    print(f'Done — {sealed} module(s) in {SEALED}')
    return 0 if sealed else 1


if __name__ == '__main__':
    raise SystemExit(main())
