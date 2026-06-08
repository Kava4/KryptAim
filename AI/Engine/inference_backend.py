"""GPU backend selection — Ultralytics + torch.cuda / ONNX Runtime."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Literal

logger = logging.getLogger('AimSync.AI.Backend')

InferenceBackend = Literal['directml', 'cuda_onnx', 'cuda_ultralytics', 'cpu']

VALID_BACKENDS: tuple[str, ...] = ('directml', 'cuda_onnx', 'cuda_ultralytics', 'cpu')
ULTRALYTICS_BACKENDS: frozenset[str] = frozenset({'cuda_ultralytics'})
ONNX_BACKENDS: frozenset[str] = frozenset({'directml', 'cuda_onnx', 'cpu'})
YOLO_MODEL_EXTENSIONS = frozenset({'.onnx', '.pt', '.engine'})


def default_inference_backend() -> InferenceBackend:
    """CUDA Ultralytics when torch.cuda or ONNX Runtime CUDA EP is available."""
    if cuda_inference_available():
        return 'cuda_ultralytics'
    return 'directml'


def normalize_backend(value: str | None) -> InferenceBackend:
    raw = (value or '').strip().lower()
    if not raw:
        return default_inference_backend()
    if raw in VALID_BACKENDS:
        return raw  # type: ignore[return-value]
    return default_inference_backend()


def model_extension(path: Path | str) -> str:
    return Path(path).suffix.lower()


def _nvidia_driver_present() -> bool:
    if sys.platform != 'win32':
        return False
    try:
        import ctypes

        ctypes.WinDLL('nvcuda.dll')
        return True
    except OSError:
        return False


def _torch_cuda_available() -> bool:
    if getattr(sys, 'frozen', False):
        return _nvidia_driver_present()
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def _ort_cuda_available() -> bool:
    return 'CUDAExecutionProvider' in probe_onnx_providers()


def cuda_inference_available() -> bool:
    """True when torch.cuda or ONNX Runtime CUDA EP can run GPU inference."""
    return _torch_cuda_available() or _ort_cuda_available()


def _probe_torch_cuda() -> tuple[bool, str, str]:
    """Returns (available, device_name, torch_version). May import torch — call after rthook stub."""
    try:
        import torch

        version = getattr(torch, '__version__', '')
        if torch.cuda.is_available():
            return True, str(torch.cuda.get_device_name(0)), version
    except Exception:
        pass
    return False, '', ''


def backend_for_model(path: Path | str, preferred: str | None) -> InferenceBackend:
    """
    YOLO(.onnx|.pt|.engine) on CUDA device 0 when GPU inference is available.
    Optional ONNX-only backends (directml / cuda_onnx) only when explicitly configured.
    """
    ext = model_extension(path)
    preferred_backend = normalize_backend(preferred)

    if ext in YOLO_MODEL_EXTENSIONS:
        if preferred_backend == 'cpu':
            return 'cpu'
        if preferred_backend == 'cuda_onnx':
            return 'cuda_onnx'
        if cuda_inference_available():
            if not _torch_cuda_available() and _ort_cuda_available():
                logger.warning(
                    'torch.cuda=False but ONNX Runtime has CUDA — using cuda_ultralytics; '
                    'run scripts\\repair_ai_deps.bat for torch cu126'
                )
            else:
                logger.info('Using cuda_ultralytics for %s (YOLO + CUDA)', Path(path).name)
            return 'cuda_ultralytics'
        if ext == '.onnx':
            logger.warning('CUDA unavailable; falling back to DirectML for %s', Path(path).name)
            return 'directml'
        return 'cpu'

    return preferred_backend


def uses_ultralytics(backend: InferenceBackend) -> bool:
    return backend in ULTRALYTICS_BACKENDS


def probe_onnx_providers() -> list[str]:
    try:
        import onnxruntime as ort

        return list(ort.get_available_providers())
    except ImportError:
        return []


def resolve_onnx_providers(backend: InferenceBackend) -> list[list[str]]:
    try:
        import onnxruntime as ort
    except ImportError:
        return [['CPUExecutionProvider']]

    available = set(ort.get_available_providers())
    cpu = ['CPUExecutionProvider']

    if backend == 'cpu':
        return [cpu]

    if backend == 'cuda_onnx':
        if 'CUDAExecutionProvider' in available:
            return [['CUDAExecutionProvider', 'CPUExecutionProvider'], cpu]
        logger.warning('CUDAExecutionProvider not available; falling back to DirectML/CPU')
        backend = 'directml'

    if backend == 'directml':
        if 'DmlExecutionProvider' in available:
            return [['DmlExecutionProvider', 'CPUExecutionProvider'], cpu]
        return [cpu]

    return [cpu]


def probe_gpu_status(*, import_torch: bool = True) -> dict:
    status = {
        'cuda_available': False,
        'cuda_device_name': '',
        'torch_version': '',
        'onnx_providers': [],
        'tensorrt_available': False,
        'inference_stack': 'ultralytics',
    }
    status['onnx_providers'] = probe_onnx_providers()

    if getattr(sys, 'frozen', False) and not import_torch:
        if _nvidia_driver_present():
            status['cuda_available'] = True
            status['cuda_device_name'] = 'NVIDIA GPU (driver detected)'
        return status

    cuda_ok, device_name, torch_ver = _probe_torch_cuda()
    status['torch_version'] = torch_ver
    if cuda_ok:
        status['cuda_available'] = True
        status['cuda_device_name'] = device_name
    elif _ort_cuda_available():
        status['cuda_available'] = True
        status['cuda_device_name'] = 'ORT CUDA (reinstall torch cu126 for full CUDA)'
    elif getattr(sys, 'frozen', False) and _nvidia_driver_present():
        status['cuda_available'] = True
        status['cuda_device_name'] = 'NVIDIA GPU (driver detected)'

    if not import_torch:
        return status

    try:
        import tensorrt  # noqa: F401

        status['tensorrt_available'] = True
    except ImportError:
        pass

    return status


def create_detector(backend: InferenceBackend):
    """Return a fresh detector instance for the given backend."""
    if uses_ultralytics(backend):
        from AI.Engine.inference_ultralytics import UltralyticsDetector

        return UltralyticsDetector(device_id=0 if backend == 'cuda_ultralytics' else 'cpu')
    from AI.Engine.inference import OnnxDetector

    detector = OnnxDetector()
    detector.set_backend(backend)
    return detector
