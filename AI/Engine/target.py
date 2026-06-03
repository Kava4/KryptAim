"""Target selection from YOLO output (FOV filter + nearest to center)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from AI.Engine.capture import DetectionRegion
from AI.Engine.settings import AiSettings


@dataclass
class Prediction:
    x_min: float
    y_min: float
    width: float
    height: float
    confidence: float
    class_id: int
    screen_center_x: float
    screen_center_y: float
    detection_box: tuple[float, float, float, float]


class TargetSelector:
    def __init__(self, settings: AiSettings) -> None:
        self._settings = settings
        self._sticky_target: Prediction | None = None
        self._frames_without_target = 0
        self._max_frames_without = 3

    def reset_sticky(self) -> None:
        self._sticky_target = None
        self._frames_without_target = 0

    def select(
        self,
        output: np.ndarray,
        region: DetectionRegion,
        image_size: int,
        num_detections: int,
        num_classes: int = 1,
    ) -> Prediction | None:
        min_conf = float(self._settings.sliders['AI Minimum Confidence']) / 100.0
        fov = float(self._settings.sliders['FOV Size'])
        fov_min_x = (image_size - fov) / 2.0
        fov_max_x = (image_size + fov) / 2.0
        fov_min_y = (image_size - fov) / 2.0
        fov_max_y = (image_size + fov) / 2.0

        candidates: list[Prediction] = []
        center_x = image_size / 2.0
        center_y = image_size / 2.0

        for i in range(min(num_detections, output.shape[2])):
            x_center = float(output[0, 0, i])
            y_center = float(output[0, 1, i])
            width = float(output[0, 2, i])
            height = float(output[0, 3, i])

            if num_classes == 1:
                confidence = float(output[0, 4, i])
                class_id = 0
            else:
                class_scores = output[0, 4:4 + num_classes, i]
                class_id = int(np.argmax(class_scores))
                confidence = float(class_scores[class_id])

            if confidence < min_conf:
                continue

            x_min = x_center - width / 2
            y_min = y_center - height / 2
            x_max = x_center + width / 2
            y_max = y_center + height / 2

            if x_min < fov_min_x or x_max > fov_max_x or y_min < fov_min_y or y_max > fov_max_y:
                continue

            pred = Prediction(
                x_min=x_min,
                y_min=y_min,
                width=width,
                height=height,
                confidence=confidence,
                class_id=class_id,
                screen_center_x=region.left + x_center,
                screen_center_y=region.top + y_center,
                detection_box=(region.left + x_min, region.top + y_min, width, height),
            )
            candidates.append(pred)

        if not candidates:
            self._handle_sticky_loss()
            return self._sticky_target if self._settings.toggles['Sticky Aim'] else None

        def _center_dist(pred: Prediction) -> float:
            cx = pred.x_min + pred.width / 2.0
            cy = pred.y_min + pred.height / 2.0
            return (cx - center_x) ** 2 + (cy - center_y) ** 2

        best = min(candidates, key=_center_dist)
        return self._apply_sticky(best, candidates)

    def _handle_sticky_loss(self) -> None:
        if not self._settings.toggles['Sticky Aim']:
            self._sticky_target = None
            return
        self._frames_without_target += 1
        if self._frames_without_target > self._max_frames_without:
            self._sticky_target = None

    def _apply_sticky(self, best: Prediction, candidates: list[Prediction]) -> Prediction | None:
        if not self._settings.toggles['Sticky Aim']:
            return best

        threshold = float(self._settings.sliders['Sticky Aim Threshold'])
        threshold_sq = threshold * threshold

        if self._sticky_target is not None:
            matched = None
            min_dist = float('inf')
            for candidate in candidates:
                dx = candidate.screen_center_x - self._sticky_target.screen_center_x
                dy = candidate.screen_center_y - self._sticky_target.screen_center_y
                dist_sq = dx * dx + dy * dy
                if dist_sq < min_dist and dist_sq < threshold_sq:
                    min_dist = dist_sq
                    matched = candidate
            if matched is not None:
                self._sticky_target = matched
                self._frames_without_target = 0
                return matched
            self._handle_sticky_loss()
            if self._sticky_target is not None and self._frames_without_target <= self._max_frames_without:
                return self._sticky_target

        self._sticky_target = best
        self._frames_without_target = 0
        return best
