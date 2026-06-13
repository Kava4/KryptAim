"""Verify build-venv before PyInstaller (run from repo root)."""

from __future__ import annotations

import sys


def main() -> int:
    errors: list[str] = []
    for mod in (
        'PyInstaller',
        'torch',
        'ultralytics',
        'matplotlib',
        'cv2',
        'numpy',
        'cyndilib',
        'onnxruntime',
        'flask',
        'makcu',
    ):
        try:
            __import__(mod)
            print(f'OK  {mod}')
        except ImportError as exc:
            errors.append(f'{mod}: {exc}')
            print(f'FAIL {mod}: {exc}')

    try:
        from ultralytics import YOLO  # noqa: F401

        print('OK  ultralytics.YOLO')
    except Exception as exc:
        errors.append(f'YOLO: {exc}')

    try:
        import torch

        version = torch.__version__
        cuda = torch.cuda.is_available()
        print(f'OK  torch {version} cuda={cuda}')
        if '+cu' not in version and 'cuda' not in version.lower():
            print('WARN torch looks CPU-only — install cu126 wheels in create_build_venv.bat')
    except Exception as exc:
        errors.append(f'torch: {exc}')

    if errors:
        print('\nFix: scripts\\create_build_venv.bat')
        return 1
    print('\nBuild stack OK — run scripts\\build_app.bat')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
