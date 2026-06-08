"""Verify build venv has torch+ultralytics before PyInstaller (run from repo root)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    errors: list[str] = []
    for mod in (
        'torch',
        'torchvision',
        'ultralytics',
        'matplotlib',
        'cv2',
        'numpy',
        'cyndilib',
        'onnx',
        'onnxruntime',
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
        print(f'FAIL YOLO: {exc}')

    torch_cuda = False
    try:
        import torch

        version = getattr(torch, '__version__', '')
        torch_cuda = bool(torch.cuda.is_available())
        print(f'OK  torch {version} cuda={torch_cuda}')
        if '+cu' not in version and 'cuda' not in version.lower():
            print('WARN torch wheel looks CPU-only — run scripts\\repair_ai_deps.bat')
        if not torch_cuda:
            print('WARN torch.cuda=False — run: pip uninstall torch torchvision torchaudio')
            print('      then: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126')
    except Exception as exc:
        errors.append(f'torch.cuda: {exc}')

    ort_cuda = False
    try:
        import onnxruntime as ort

        providers = ort.get_available_providers()
        ort_cuda = 'CUDAExecutionProvider' in providers
        print(f'OK  onnxruntime providers={providers}')
        if not ort_cuda:
            print('WARN CUDAExecutionProvider missing — reinstall onnxruntime-gpu')
    except Exception as exc:
        errors.append(f'onnxruntime: {exc}')
        print(f'FAIL onnxruntime: {exc}')

    if ort_cuda and not torch_cuda:
        print('NOTE ORT has CUDA but torch does not — AimSync can use GPU via ONNX; still run repair for torch cu126.')
    elif not ort_cuda and not torch_cuda:
        errors.append('no CUDA path (torch or onnxruntime)')
        print('FAIL no GPU inference path detected')

    try:
        import AI.Vendor.yolo_cuda.detection_core  # noqa: F401

        print('OK  AI.Vendor.yolo_cuda.detection_core')
    except Exception as exc:
        errors.append(f'detection_core: {exc}')
        print(f'FAIL detection_core: {exc}')

    try:
        import makcu  # noqa: F401

        print('OK  makcu')
    except Exception as exc:
        errors.append(f'makcu: {exc}')
        print(f'FAIL makcu: {exc}')

    if ort_cuda and not torch_cuda:
        venv_hint = 'scripts\\repair_build_venv.bat' if 'build-venv' in sys.executable.replace('/', '\\') else 'scripts\\repair_ai_deps.bat'
        print(f'\nRepair required: {venv_hint} (close AimSync first)')
        return 1

    if errors:
        print('\nRun: scripts\\install_aimsync_pc.bat  (AimSync PC)')
        print('  or: scripts\\create_build_venv.bat   (build machine / exe)')
        return 1
    print('\nAI stack OK (venv deploy or build_app.bat)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
