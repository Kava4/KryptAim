"""YOLO detection via Ultralytics."""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Any

import numpy as np

os.environ.setdefault('YOLO_AUTOINSTALL', 'false')

_load_lock = threading.Lock()


def _onnx_runtime_device() -> int | str:
    try:
        import onnxruntime as ort

        providers = ort.get_available_providers()
        if 'CUDAExecutionProvider' in providers:
            return 0
    except ImportError:
        pass
    return 'cpu'


def _resolve_device(*, onnx: bool = False) -> int | str:
    if onnx:
        return _onnx_runtime_device()
    try:
        import torch

        if torch.cuda.is_available():
            return 0
    except ImportError:
        pass
    return 'cpu'


class YoloDetector:
    def __init__(self) -> None:
        self._model: Any = None
        self._device: int | str = 'cpu'
        self._is_onnx = False
        self.class_names: dict[int, str] = {}
        self.last_error = ''
        self.image_size = 640
        self._conf = 0.25
        self._loaded_path = ''
        self._loading_path = ''

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def model_name(self) -> str:
        return Path(self._loaded_path).name if self._loaded_path else ''

    def load(self, model_path: str, *, conf: float = 0.25) -> bool:
        path = (model_path or '').strip()
        self._conf = float(conf)
        if not path:
            self.unload()
            self.last_error = 'No model path set'
            return False

        with _load_lock:
            if self.is_loaded and self._loaded_path == path:
                return True
            if self._loading_path == path:
                return False

            self._loading_path = path
            file_path = Path(path)
            if not file_path.is_file():
                self._loading_path = ''
                self.last_error = f'Model not found: {file_path}'
                return False

            try:
                from ultralytics import YOLO
            except ImportError as exc:
                self._loading_path = ''
                self.last_error = (
                    f'ultralytics missing ({exc}). '
                    'Run: scripts\\repair_ai_deps.bat'
                )
                return False

            suffix = file_path.suffix.lower()
            self._is_onnx = suffix == '.onnx'
            if self._is_onnx:
                try:
                    import onnxruntime  # noqa: F401
                except ImportError:
                    self._loading_path = ''
                    self.last_error = (
                        'onnxruntime missing for .onnx models. '
                        'Run: scripts\\repair_ai_deps.bat'
                    )
                    return False

            self._device = _resolve_device(onnx=self._is_onnx)
            self._model = None
            self._loaded_path = ''
            self.class_names = {}

            try:
                logging.getLogger('ultralytics').setLevel(logging.ERROR)
                self._model = YOLO(str(file_path), task='detect')
                names: dict[int, str] = {}
                raw_names = getattr(self._model, 'names', None)
                if raw_names:
                    names = dict(raw_names)
                elif hasattr(self._model, 'model') and getattr(self._model.model, 'names', None):
                    names = dict(self._model.model.names)
                if not names:
                    from app.ai.class_names import resolve_class_names

                    names = resolve_class_names(file_path, num_classes=1)
                self.class_names = names
                self._loaded_path = str(file_path)
                self.image_size = _guess_imgsz(file_path.name)
                self.last_error = ''
                self._loading_path = ''
                return True
            except ModuleNotFoundError as exc:
                self._model = None
                self._loading_path = ''
                if 'onnxruntime' in str(exc).lower():
                    self.last_error = (
                        'onnxruntime missing for .onnx models. '
                        'Run: scripts\\repair_ai_deps.bat'
                    )
                else:
                    self.last_error = f'Missing dependency: {exc}'
                return False
            except Exception as exc:
                self.last_error = f'Load failed: {exc}'
                self._model = None
                self._loading_path = ''
                return False

    def unload(self) -> None:
        self._model = None
        self._loaded_path = ''
        self._loading_path = ''
        self.class_names = {}

    def detect(self, bgr: np.ndarray) -> list[dict[str, float | int | str]]:
        if not self.is_loaded or self._model is None:
            return []

        use_half = False
        if not self._is_onnx and self._device == 0:
            try:
                import torch

                use_half = bool(torch.cuda.is_available())
            except ImportError:
                use_half = False

        try:
            results = self._model.predict(
                source=bgr,
                imgsz=self.image_size,
                stream=False,
                conf=self._conf,
                iou=0.5,
                device=self._device,
                half=use_half,
                max_det=50,
                verbose=False,
            )
        except Exception as exc:
            self.last_error = str(exc)
            return []

        detections: list[dict[str, float | int | str]] = []
        for result in results or []:
            boxes = getattr(result, 'boxes', None)
            if boxes is None:
                continue
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0].item())
                cls_id = int(box.cls[0].item())
                name = self.class_names.get(cls_id, str(cls_id))
                detections.append({
                    'x1': float(x1),
                    'y1': float(y1),
                    'x2': float(x2),
                    'y2': float(y2),
                    'confidence': conf,
                    'class_id': cls_id,
                    'class_name': name,
                })
        return detections


def _guess_imgsz(filename: str) -> int:
    for size in (640, 512, 416, 320):
        if str(size) in filename:
            return size
    return 640
