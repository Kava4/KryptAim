"""PyInstaller build → dist/AimSync/AimSync.exe

Profiles (AIMSYNC_BUILD_PROFILE):
  lite  — ~50–120 MB: Flask + Makcu + recoil. AI deps install to %%APPDATA%%\\AimSync\\runtime
  full  — ~2–4 GB: bundles torch/ultralytics/onnx (offline, no bootstrap)
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENTRY = ROOT / 'main.py'
ICON = ROOT / 'web' / 'static' / 'AimSync_logo.ico'

_LITE_EXCLUDES = (
    'torch',
    'torchvision',
    'torchaudio',
    'ultralytics',
    'matplotlib',
    'onnxruntime',
    'cv2',
    'cyndilib',
    'numpy',
    'pandas',
    'scipy',
    'tensorboard',
)


def build_profile() -> str:
    value = os.environ.get('AIMSYNC_BUILD_PROFILE', 'lite').strip().lower()
    return value if value in {'lite', 'full'} else 'lite'


def _add_data(src: Path, dest: str, out: list[str]) -> None:
    if not src.exists():
        return
    out.extend(['--add-data', f'{src}{os.pathsep}{dest}'])


def dist_exe_path(profile: str | None = None) -> Path:
    profile = profile or build_profile()
    if profile == 'lite':
        return ROOT / 'dist' / 'AimSync.exe'
    return ROOT / 'dist' / 'AimSync' / 'AimSync.exe'


def _maybe_clean() -> None:
    if os.environ.get('AIMSYNC_BUILD_CLEAN', '').strip() != '1':
        return
    profile = build_profile()
    targets: list[Path] = [ROOT / 'build']
    if profile == 'lite':
        targets.extend((ROOT / 'dist' / 'AimSync.exe', ROOT / 'dist' / 'AimSync'))
    else:
        targets.append(ROOT / 'dist' / 'AimSync')
    for path in targets:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            path.unlink(missing_ok=True)


def _remove_stale_dist(profile: str) -> None:
    """Drop leftover output from the other layout (onedir vs onefile)."""
    if profile == 'lite':
        stale = ROOT / 'dist' / 'AimSync'
        if stale.is_dir():
            shutil.rmtree(stale, ignore_errors=True)
    else:
        stale = ROOT / 'dist' / 'AimSync.exe'
        if stale.is_file():
            stale.unlink(missing_ok=True)


def build_args() -> list[str]:
    profile = build_profile()
    _maybe_clean()

    if profile == 'full':
        import pyi_collect  # noqa: F401
    else:
        import pyi_collect_lite  # noqa: F401

    layout = '--onefile' if profile == 'lite' else '--onedir'

    args = [
        str(ENTRY),
        '--name=AimSync',
        layout,
        '--noconfirm',
        f'--distpath={ROOT / "dist"}',
        f'--workpath={ROOT / "build"}',
        f'--specpath={ROOT}',
        '--paths',
        str(ROOT),
    ]

    if os.environ.get('AIMSYNC_BUILD_CONSOLE', '').strip() == '1':
        args.append('--console')
    else:
        args.append('--noconsole')
        args.append('--windowed')

    if ICON.is_file():
        args.extend(['--icon', str(ICON)])

    _add_data(ROOT / 'web' / 'static', 'web/static', args)
    _add_data(ROOT / 'web' / 'templates', 'web/templates', args)
    _add_data(ROOT / 'assets', 'assets', args)
    if profile == 'lite':
        _add_data(ROOT / 'requirements.txt', '.', args)

    if profile == 'lite':
        hidden = (
            'engineio.async_drivers.threading',
            'flask',
            'werkzeug',
            'jinja2',
            'markupsafe',
            'itsdangerous',
            'click',
            'makcu',
            'tkinter',
        )
        for mod in hidden:
            args.extend(['--hidden-import', mod])
        for mod in _LITE_EXCLUDES:
            args.extend(['--exclude-module', mod])
    else:
        hidden = (
            'engineio.async_drivers.threading',
            'flask',
            'werkzeug',
            'jinja2',
            'markupsafe',
            'itsdangerous',
            'click',
            'cv2',
            'numpy',
            'cyndilib',
            'makcu',
            'ultralytics',
            'torch',
            'torchvision',
            'matplotlib',
            'onnxruntime',
            'PIL',
            'tkinter',
        )
        for mod in hidden:
            args.extend(['--hidden-import', mod])
        for pkg in ('ultralytics', 'flask', 'cyndilib', 'matplotlib'):
            args.extend(['--collect-all', pkg])
        for pkg in ('ultralytics', 'torch', 'cyndilib'):
            args.extend(['--copy-metadata', pkg])

    return args


def main() -> int:
    profile = build_profile()
    if not ENTRY.is_file():
        print(f'ERROR: missing entry {ENTRY}')
        return 1

    try:
        import PyInstaller.__main__
    except ImportError:
        print('ERROR: pyinstaller not installed. Run scripts\\create_build_venv.bat')
        return 1

    print(f'[build] profile={profile}')
    if profile == 'lite':
        print('[build] Slim exe — AI stack installs to %APPDATA%\\AimSync\\runtime on first use')
    else:
        print('[build] Full exe — bundles CUDA stack (large download)')
    layout = 'onefile' if profile == 'lite' else 'onedir'
    print(f'[build] PyInstaller {layout} — this can take several minutes…')
    PyInstaller.__main__.run(build_args())

    exe = dist_exe_path(profile)
    if not exe.is_file():
        print('ERROR: build finished but AimSync.exe is missing')
        return 1

    _remove_stale_dist(profile)
    print(f'\nOK: {exe}')
    if profile == 'lite':
        size_mb = exe.stat().st_size / (1024 * 1024)
        print(f'[build] Single exe — no _internal folder ({size_mb:.1f} MB)')
    print('Zip: scripts\\package_release.bat')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
