"""Check that cyndilib works in the same Python you use for AimSync."""

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
    print('Frozen (PyInstaller exe):', bool(getattr(sys, 'frozen', False)))
    print()

    pkg = _cyndilib_dir()
    if pkg is None:
        print('FAIL: cyndilib package not found on sys.path')
        print('Fix:  python -m pip install cyndilib')
        return 1

    print('Package dir:', pkg)
    wrapper = pkg / 'wrapper'
    if wrapper.is_dir():
        pyds = sorted(wrapper.glob('*.pyd')) + sorted(wrapper.glob('*.so'))
        print(f'Native modules in wrapper/: {len(pyds)}')
        for p in pyds[:12]:
            print('  ', p.name)
        if len(pyds) > 12:
            print('   ...')
        if not pyds:
            print('FAIL: no .pyd/.so in cyndilib/wrapper — reinstall cyndilib for this Python version')
    else:
        print('WARN: cyndilib/wrapper/ missing')

    print()
    try:
        from cyndilib.wrapper.ndi_recv import RecvColorFormat  # noqa: F401
        from cyndilib.finder import Finder  # noqa: F401

        print('OK: cyndilib imports (wrapper.common + finder)')
    except ImportError as exc:
        print(f'FAIL: import error: {exc}')
        print()
        print('If you run AimSync.exe: pip on your PC does NOT fix the exe — rebuild with create_build_venv.bat + build_app.bat.')
        print('If you run python main.py: use THIS executable:')
        print(f'  "{sys.executable}" -m pip install --force-reinstall --no-cache-dir cyndilib')
        print('Or re-run: scripts\\install_aimsync_pc.bat')
        return 1

    try:
        from cyndilib.finder import Finder

        finder = Finder()
        finder.open()
        try:
            names = [s.name for s in finder.get_source_names()]
            print(f'OK: NDI finder ({len(names)} source(s) on LAN)')
            if not names:
                print('WARN: no sources — install NDI Runtime + enable NDI on gaming PC')
        finally:
            finder.close()
    except Exception as exc:
        print(f'WARN: NDI runtime / finder: {exc}')
        print('Install NDI Runtime: https://ndi.link/NDIRedistV6 (both PCs)')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
