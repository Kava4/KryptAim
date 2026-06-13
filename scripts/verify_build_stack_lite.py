"""Verify build-venv for slim (lite) PyInstaller builds."""

from __future__ import annotations

import sys


def main() -> int:
    errors: list[str] = []
    for mod in ('PyInstaller', 'flask', 'makcu'):
        try:
            __import__(mod)
            print(f'OK  {mod}')
        except ImportError as exc:
            errors.append(f'{mod}: {exc}')
            print(f'FAIL {mod}: {exc}')

    if errors:
        print('\nLite build needs: pip install pyinstaller flask makcu')
        return 1
    print('\nLite build stack OK — run scripts\\build_app.bat')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
