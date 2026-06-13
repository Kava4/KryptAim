"""Check cyndilib + NDI finder on the AimSync PC."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _cyndilib_dir() -> Path | None:
    spec = importlib.util.find_spec('cyndilib')
    if spec is None or not spec.origin:
        return None
    return Path(spec.origin).resolve().parent


def main() -> int:
    print('Python:', sys.version)
    print('Executable:', sys.executable)
    print()

    pkg = _cyndilib_dir()
    if pkg is None:
        print('FAIL: cyndilib not found')
        print('Fix: pip install cyndilib opencv-python-headless numpy')
        return 1

    print('Package dir:', pkg)
    try:
        from cyndilib.finder import Finder  # noqa: F401

        print('OK: cyndilib imports')
    except ImportError as exc:
        print(f'FAIL: {exc}')
        print(f'Fix: "{sys.executable}" -m pip install --force-reinstall cyndilib')
        return 1

    try:
        finder = Finder()
        finder.open()
        try:
            import time

            names: list[str] = []
            for attempt in range(12):
                names = list(finder.get_source_names() or [])
                if names:
                    break
                time.sleep(0.5)
            print(f'OK: NDI finder — {len(names)} source(s)')
            for name in names[:10]:
                print('  ', name)
            if not names:
                print('  (none) — OBS Main Output on gaming PC? Same LAN? Firewall?')
        finally:
            finder.close()
    except Exception as exc:
        print(f'WARN: finder failed: {exc}')
        print('Install NDI Runtime on BOTH PCs: https://ndi.link/NDIRedistV6')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
