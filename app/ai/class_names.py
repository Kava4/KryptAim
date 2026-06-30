"""Resolve YOLO class names from model files (CT/T for CS2, etc.)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger('AimSync.ai.class_names')

_FILENAME_PRESETS: list[tuple[str, dict[int, str]]] = (
    ('cs2', {0: 'CT', 1: 'T'}),
    ('counter', {0: 'CT', 1: 'T'}),
    ('valo', {0: 'Enemy', 1: 'Friendly'}),
    ('valorant', {0: 'Enemy', 1: 'Friendly'}),
)


def _normalize_names(raw: dict | list | None, num_classes: int) -> dict[int, str]:
    if not raw:
        return {i: str(i) for i in range(max(1, num_classes))}
    if isinstance(raw, list):
        return {i: str(raw[i]) if i < len(raw) else str(i) for i in range(max(len(raw), num_classes))}
    if isinstance(raw, dict):
        out: dict[int, str] = {}
        for key, value in raw.items():
            try:
                idx = int(key)
            except (TypeError, ValueError):
                continue
            out[idx] = str(value)
        if out:
            for i in range(max(num_classes, max(out.keys()) + 1)):
                out.setdefault(i, str(i))
            return out
    return {i: str(i) for i in range(max(1, num_classes))}


def _names_from_ultralytics(model_path: Path) -> dict[int, str] | None:
    try:
        from ultralytics import YOLO
    except ImportError:
        return None
    try:
        model = YOLO(str(model_path), task='detect')
        names = getattr(model, 'names', None) or getattr(getattr(model, 'model', None), 'names', None)
        if names:
            size = len(names) if isinstance(names, (dict, list)) else 1
            return _normalize_names(names, size)
    except Exception as exc:
        logger.debug('Ultralytics class names probe failed for %s: %s', model_path.name, exc)
    return None


def _names_from_onnx_metadata(model_path: Path) -> dict[int, str] | None:
    try:
        import onnx
    except ImportError:
        return None
    try:
        model = onnx.load(str(model_path), load_external_data=False)
        for prop in model.metadata_props:
            key = (prop.key or '').lower()
            if key not in {'names', 'class_names', 'labels'}:
                continue
            raw = prop.value
            if not isinstance(raw, str):
                continue
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                if ',' in raw and '{' not in raw:
                    parts = [part.strip().strip("'\"") for part in raw.split(',')]
                    return {i: parts[i] for i in range(len(parts))}
                continue
            size = len(parsed) if isinstance(parsed, list) else len(parsed)
            return _normalize_names(parsed, size)
    except Exception as exc:
        logger.debug('ONNX metadata class names failed for %s: %s', model_path.name, exc)
    return None


def _names_from_filename(model_path: Path, num_classes: int) -> dict[int, str] | None:
    stem = model_path.stem.lower()
    for token, preset in _FILENAME_PRESETS:
        if token in stem and num_classes >= len(preset):
            return dict(preset)
    return None


def resolve_class_names(model_path: Path, num_classes: int = 1) -> dict[int, str]:
    path = Path(model_path)
    if not path.is_file():
        return {i: str(i) for i in range(max(1, num_classes))}

    for resolver in (_names_from_ultralytics, _names_from_onnx_metadata):
        names = resolver(path)
        if names:
            logger.info('Class names for %s: %s', path.name, names)
            return names

    preset = _names_from_filename(path, num_classes)
    if preset:
        logger.info('Class names (preset) for %s: %s', path.name, preset)
        return preset

    return {i: str(i) for i in range(max(1, num_classes))}


def class_details(names: dict[int, str]) -> list[dict[str, str | int]]:
    return [{'id': i, 'name': names[i]} for i in sorted(names.keys())]


def class_name_list(names: dict[int, str]) -> list[str]:
    return [names[i] for i in sorted(names.keys())]
