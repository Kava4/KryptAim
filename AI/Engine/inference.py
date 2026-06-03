"""ONNX YOLOv8 inference (Aimmy-compatible shapes)."""

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

    @staticmethod
    def _num_detections(image_size: int) -> int:
        s8, s16, s32 = image_size // 8, image_size // 16, image_size // 32
        return (s8 * s8) + (s16 * s16) + (s32 * s32)

    def _create_session(self, model_path: Path, providers: list[str]):
        return ort.InferenceSession(str(model_path), providers=providers)

    def load(self, model_path: Path) -> bool:
        self.last_error = ''
        if ort is None:
            self.last_error = 'onnxruntime not installed. Run: pip install -r requirements-beta.txt'
            logger.error(self.last_error)
            return False
        self.unload()

        available = ort.get_available_providers()
        provider_attempts: list[list[str]] = []
        if 'DmlExecutionProvider' in available:
            provider_attempts.append(['DmlExecutionProvider', 'CPUExecutionProvider'])
        provider_attempts.append(['CPUExecutionProvider'])

        session = None
        errors: list[str] = []
        for providers in provider_attempts:
            try:
                session = self._create_session(model_path, providers)
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
        self.info = ModelInfo(
            path=model_path,
            image_size=image_size,
            num_detections=self._num_detections(image_size),
            num_classes=1,
            is_dynamic=is_dynamic,
        )
        logger.info('Loaded ONNX model %s (%sx%s)', model_path.name, image_size, image_size)
        return True

    def unload(self) -> None:
        self._session = None
        self._input_name = None
        self._output_names = []
        self.info = None

    @property
    def is_loaded(self) -> bool:
        return self._session is not None and self.info is not None

    def preprocess(self, rgb: np.ndarray) -> np.ndarray:
        size = self.info.image_size if self.info else rgb.shape[0]
        chw = rgb.transpose(2, 0, 1).astype(np.float32) / 255.0
        if chw.shape[1] != size or chw.shape[2] != size:
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
        # Normalize to [1, channels, num_detections] (Aimmy layout).
        if output.ndim == 3 and output.shape[1] > output.shape[2]:
            output = np.transpose(output, (0, 2, 1))
        return output
