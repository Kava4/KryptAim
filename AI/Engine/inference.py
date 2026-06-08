"""ONNX YOLOv8 inference for AimSync AI."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger('AimSync.AI.Inference')

try:
    import onnxruntime as ort
except ImportError:  # pragma: no cover
    ort = None


@dataclass
class ModelInfo:
    path: Path
    image_size: int
    num_detections: int
    num_classes: int
    is_dynamic: bool


class OnnxDetector:
    def __init__(self) -> None:
        self._session: Any = None
        self._input_name: str | None = None
        self._output_names: list[str] = []
        self.info: ModelInfo | None = None
        self.last_error: str = ''
        self._backend = 'directml'
        self._active_provider = ''
        self.class_names: dict[int, str] = {}

    def set_backend(self, backend: str) -> None:
        self._backend = (backend or 'directml').strip().lower()

    @staticmethod
    def _num_detections(image_size: int) -> int:
        s8, s16, s32 = image_size // 8, image_size // 16, image_size // 32
        return (s8 * s8) + (s16 * s16) + (s32 * s32)

    def _create_session(self, model_path: Path, providers: list[str]):
        return ort.InferenceSession(str(model_path), providers=providers)

    def load(self, model_path: Path) -> bool:
        self.last_error = ''
        if ort is None:
            self.last_error = 'onnxruntime not installed. Run: scripts\\install_aimsync_pc.bat'
            logger.error(self.last_error)
            return False
        self.unload()

        from AI.Engine.class_names import resolve_class_names
        from AI.Engine.inference_backend import normalize_backend, resolve_onnx_providers

        provider_attempts = resolve_onnx_providers(normalize_backend(self._backend))
        logger.info(
            'Loading ONNX %s backend=%s attempts=%s',
            model_path.name,
            self._backend,
            [p[0] for p in provider_attempts],
        )

        session = None
        errors: list[str] = []
        for providers in provider_attempts:
            try:
                logger.info('ONNX InferenceSession create: %s', providers[0])
                session = self._create_session(model_path, providers)
                logger.info('ONNX session ready: active=%s', session.get_providers()[0] if session.get_providers() else '?')
                break
            except Exception as exc:
                errors.append(f'{providers[0]}: {exc}')
                logger.warning('ONNX load failed (%s): %s', providers[0], exc)

        if session is None:
            self.last_error = '; '.join(errors) or 'Unknown ONNX load error'
            return False

        input_meta = session.get_inputs()[0]
        shape = input_meta.shape
        is_dynamic = isinstance(shape[2], str) or shape[2] is None
        image_size = 640
        if not is_dynamic and len(shape) == 4:
            image_size = int(shape[2])

        self._session = session
        self._input_name = input_meta.name
        self._output_names = [o.name for o in session.get_outputs()]
        self._active_provider = session.get_providers()[0] if session.get_providers() else ''
        num_classes = self._infer_num_classes_from_output(session)
        self.class_names = resolve_class_names(model_path, num_classes)
        self.info = ModelInfo(
            path=model_path,
            image_size=image_size,
            num_detections=self._num_detections(image_size),
            num_classes=num_classes,
            is_dynamic=is_dynamic,
        )
        logger.info(
            'Loaded ONNX model %s (%sx%s, classes=%s)',
            model_path.name,
            image_size,
            image_size,
            num_classes,
        )
        return True

    @staticmethod
    def _infer_num_classes_from_output(session) -> int:
        """YOLOv8 ONNX output channels = 4 + num_classes (community .onnx layout)."""
        try:
            shape = session.get_outputs()[0].shape
            if len(shape) >= 2 and not isinstance(shape[1], str):
                return max(1, int(shape[1]) - 4)
        except Exception:
            pass
        return 1

    def unload(self) -> None:
        self._session = None
        self._input_name = None
        self._output_names = []
        self.info = None
        self._active_provider = ''
        self.class_names = {}

    @property
    def active_provider(self) -> str:
        return self._active_provider

    @property
    def is_loaded(self) -> bool:
        return self._session is not None and self.info is not None

    def preprocess(self, rgb: np.ndarray) -> np.ndarray:
        size = self.info.image_size if self.info else rgb.shape[0]
        chw = rgb.transpose(2, 0, 1).astype(np.float32) / 255.0
        if chw.shape[1] != size or chw.shape[2] != size:
            try:
                import cv2

                resized = cv2.resize(rgb, (size, size), interpolation=cv2.INTER_LINEAR)
                chw = resized.transpose(2, 0, 1).astype(np.float32) / 255.0
            except ImportError:
                from PIL import Image

                img = Image.fromarray(rgb)
                img = img.resize((size, size), Image.Resampling.BILINEAR)
                chw = np.asarray(img).transpose(2, 0, 1).astype(np.float32) / 255.0
        return np.expand_dims(chw, axis=0)

    def run(self, rgb: np.ndarray) -> np.ndarray | None:
        if not self.is_loaded or self._input_name is None:
            return None
        tensor = self.preprocess(rgb)
        outputs = self._session.run(self._output_names, {self._input_name: tensor})
        output = np.asarray(outputs[0])
        # Normalize to [1, channels, num_detections] (standard YOLOv8 ONNX layout).
        if output.ndim == 3 and output.shape[1] > output.shape[2]:
            output = np.transpose(output, (0, 2, 1))
        return output
