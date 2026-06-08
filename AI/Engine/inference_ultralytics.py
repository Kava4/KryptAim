"""Ultralytics inference — yolo_cuda detection_core + lazy import (PyInstaller-safe)."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from AI.Engine.inference import ModelInfo

logger = logging.getLogger('AimSync.AI.Ultralytics')


@dataclass
class UltralyticsDetection:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str = ''


@dataclass
class UltralyticsRunResult:
    detections: list[UltralyticsDetection] = field(default_factory=list)
    image_size: int = 640


class UltralyticsDetector:
    def __init__(self, device_id: int | str = 0) -> None:
        self._model: Any = None
        self._device: int | str = device_id
        self.info: ModelInfo | None = None
        self.last_error: str = ''
        self.class_names: dict[int, str] = {}
        self._conf = 0.25
        self._imgsz = 640
        self._max_det = 50
        self._active_provider = ''
        self._resolved_device: int | str = 'cpu'
        self.last_max_detection_conf: float = 0.0

    def configure_runtime(self, *, conf: float, imgsz: int, max_det: int) -> None:
        self._conf = float(conf)
        self._imgsz = max(128, int(imgsz))
        self._max_det = max(1, int(max_det))

    def load(self, model_path: Path) -> bool:
        self.last_error = ''
        self.unload()

        if getattr(sys, 'frozen', False):
            from AI.Engine.torch_boot import install_torch_boot

            install_torch_boot()

        try:
            from AI.Vendor.yolo_cuda import detection_core
        except ImportError as exc:
            self.last_error = f'AI vendor module missing in build: {exc}'
            return False

        try:
            model, names, device, err = detection_core.load_yolo(model_path)
        except Exception as exc:
            self.last_error = f'YOLO import failed: {exc}'
            logger.exception('detection_core.load_yolo failed')
            return False

        if model is None or err:
            self.last_error = err or 'Failed to load model'
            return False

        self._model = model
        self._resolved_device = device
        if not names:
            from AI.Engine.class_names import resolve_class_names

            names = resolve_class_names(model_path, 1)
        self.class_names = names

        imgsz = self._imgsz_from_filename(model_path.name) or self._imgsz
        self.info = ModelInfo(
            path=model_path,
            image_size=imgsz,
            num_detections=0,
            num_classes=max(len(self.class_names), 1),
            is_dynamic=False,
        )
        self._active_provider = self._resolve_runtime_provider(model, device)
        logger.info('Loaded %s provider=%s device=%s', model_path.name, self._active_provider, device)
        return True

    @staticmethod
    def _resolve_runtime_provider(model: Any, device: int | str) -> str:
        """Expose real ONNX Runtime EP when Ultralytics loads .onnx (not just torch device)."""
        try:
            predictor = getattr(model, 'predictor', None)
            inner = getattr(predictor, 'model', None) if predictor is not None else None
            session = getattr(inner, 'session', None)
            if session is not None and hasattr(session, 'get_providers'):
                providers = list(session.get_providers())
                if providers:
                    return providers[0]
        except Exception:
            pass
        if device != 'cpu':
            return f'cuda_ultralytics:{device}'
        return 'cpu (install onnxruntime-gpu + torch cu126)'

    @staticmethod
    def _imgsz_from_filename(filename: str) -> int | None:
        for size in (640, 512, 480, 416, 384, 320, 256, 224, 192, 160, 128):
            if str(size) in filename:
                return size
        return None

    def unload(self) -> None:
        self._model = None
        self.info = None
        self.class_names = {}
        self._active_provider = ''
        self._resolved_device = 'cpu'

    @property
    def is_loaded(self) -> bool:
        return self._model is not None and self.info is not None

    @property
    def active_provider(self) -> str:
        return self._active_provider

    def run(self, bgr: np.ndarray) -> UltralyticsRunResult | None:
        if not self.is_loaded or self._model is None:
            return None

        from AI.Vendor.yolo_cuda import detection_core

        imgsz = self.info.image_size if self.info else self._imgsz
        try:
            results = detection_core.perform_detection(
                self._model,
                bgr,
                imgsz=imgsz,
                conf=self._conf,
                max_det=self._max_det,
                device=self._resolved_device,
            )
        except Exception as exc:
            self.last_error = str(exc)
            logger.warning('predict failed: %s', exc)
            return None

        detections: list[UltralyticsDetection] = []
        self.last_max_detection_conf = 0.0
        for result in results or []:
            boxes = getattr(result, 'boxes', None)
            if boxes is None:
                continue
            for box in boxes:
                coords = box.xyxy[0].tolist()
                x1, y1, x2, y2 = coords
                conf = float(box.conf[0].item())
                self.last_max_detection_conf = max(self.last_max_detection_conf, conf)
                cls = int(box.cls[0].item())
                name = self.class_names.get(cls, f'class_{cls}')
                detections.append(
                    UltralyticsDetection(
                        x1=float(x1),
                        y1=float(y1),
                        x2=float(x2),
                        y2=float(y2),
                        confidence=conf,
                        class_id=cls,
                        class_name=name,
                    )
                )

        return UltralyticsRunResult(detections=detections, image_size=imgsz)

    def to_yolo_tensor(self, result: UltralyticsRunResult) -> np.ndarray | None:
        dets = result.detections
        if not dets:
            return None
        num_classes = max((d.class_id for d in dets), default=0) + 1
        channels = 4 + max(num_classes, 1)
        n = len(dets)
        out = np.zeros((1, channels, n), dtype=np.float32)
        for i, det in enumerate(dets):
            cx = (det.x1 + det.x2) / 2.0
            cy = (det.y1 + det.y2) / 2.0
            w = det.x2 - det.x1
            h = det.y2 - det.y1
            out[0, 0, i] = cx
            out[0, 1, i] = cy
            out[0, 2, i] = w
            out[0, 3, i] = h
            if num_classes == 1:
                out[0, 4, i] = det.confidence
            else:
                out[0, 4 + det.class_id, i] = det.confidence
        return out
