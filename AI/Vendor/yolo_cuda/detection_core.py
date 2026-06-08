"""Ultralytics YOLO load/predict helpers for CUDA inference in AimSync."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import numpy as np

# Never pip-install from inside a running app (locks onnxruntime DLLs on Windows).
os.environ.setdefault('YOLO_AUTOINSTALL', 'false')


def resolve_device() -> int | str:
    import torch

    if torch.cuda.is_available():
        return 0
    try:
        import onnxruntime as ort

        if 'CUDAExecutionProvider' in ort.get_available_providers():
            return 0
    except ImportError:
        pass
    return 'cpu'


def _import_yolo_stack() -> tuple[type[Any] | None, str]:
    if getattr(sys, 'frozen', False):
        from AI.Engine.torch_boot import install_torch_boot

        install_torch_boot()

    try:
        import torch  # noqa: F401
    except ImportError as exc:
        detail = str(exc).strip()
        if 'torch.distributed' in detail:
            return None, (
                'torch distributed stub incomplete — rebuild exe after latest torch_boot fix. '
                f'({detail})'
            )
        if 'unittest' in detail:
            return None, (
                'exe missing unittest (removed by old PyInstaller exclude). '
                'Rebuild with latest build_app.py'
            ) + f' ({detail})'
        return None, (
            'torch missing in exe bundle. Rebuild: scripts\\create_build_venv.bat '
            'then scripts\\build_app.bat'
        ) + f' ({detail})'

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        detail = str(exc).strip()
        hint = (
            'ultralytics missing in exe bundle. Rebuild: scripts\\create_build_venv.bat '
            'then scripts\\build_app.bat'
        )
        if 'matplotlib' in detail:
            hint += ' (include matplotlib — update build_app.py and rebuild)'
        return None, hint + f' ({detail})'

    return YOLO, ''


def load_yolo(model_path: str | Path) -> tuple[Any, dict[int, str], int | str, str]:
    """Load YOLO model — returns (model, class_names, device, error)."""
    YOLO, stack_err = _import_yolo_stack()
    if YOLO is None:
        return None, {}, 'cpu', stack_err or 'ultralytics/torch missing'

    path = Path(model_path)
    if not path.is_file():
        return None, {}, resolve_device(), f'Model file not found: {path}'

    device = resolve_device()
    try:
        model = YOLO(str(path), task='detect')
    except Exception as exc:
        return None, {}, device, f'Failed to load model: {exc}'

    names: dict[int, str] = {}
    if hasattr(model, 'names') and model.names:
        names = dict(model.names)
    elif hasattr(model, 'model') and getattr(model.model, 'names', None):
        names = dict(model.model.names)

    return model, names, device, ''


def perform_detection(
    model: Any,
    image: np.ndarray,
    *,
    imgsz: int = 640,
    conf: float = 0.25,
    max_det: int = 50,
    device: int | str | None = None,
) -> Any:
    """Run YOLO predict with AimSync runtime params."""
    dev = device if device is not None else resolve_device()
    use_half = False
    if dev == 0 or dev == '0':
        try:
            import torch

            use_half = bool(torch.cuda.is_available())
        except ImportError:
            use_half = False
    return model.predict(
        source=image,
        imgsz=imgsz,
        stream=False,
        conf=conf,
        iou=0.5,
        device=dev,
        half=use_half,
        max_det=max_det,
        agnostic_nms=False,
        augment=False,
        vid_stride=False,
        visualize=False,
        verbose=False,
        show_boxes=False,
        show_labels=False,
        show_conf=False,
        save=False,
        show=False,
    )
