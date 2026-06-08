"""Debug preview frames (web + optional OpenCV window)."""

from __future__ import annotations

import logging
import queue
import threading
import time
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from AI.Engine.capture import DetectionRegion
    from AI.Engine.settings import AiSettings
    from AI.Engine.target import Prediction, TargetSelector

logger = logging.getLogger('AimSync.AI.DebugPreview')

_WINDOW_NAME = 'AimSync AI Debug'
_cv2_queue: queue.Queue[tuple[bool, np.ndarray | None] | None] | None = None
_cv2_thread: threading.Thread | None = None
_cv2_window_open = False


class DebugFrameStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jpeg: bytes | None = None
        self._updated_at = 0.0

    def set_jpeg(self, data: bytes | None) -> None:
        with self._lock:
            self._jpeg = data
            self._updated_at = time.time()

    def get_jpeg(self) -> bytes | None:
        with self._lock:
            return self._jpeg

    def age_seconds(self) -> float:
        with self._lock:
            if not self._updated_at:
                return 999.0
            return time.time() - self._updated_at


def _cv2():
    try:
        import cv2

        return cv2
    except ImportError:
        return None


def _ensure_cv2_thread() -> None:
    global _cv2_queue, _cv2_thread
    if _cv2_thread is not None and _cv2_thread.is_alive():
        return
    _cv2_queue = queue.Queue(maxsize=1)

    def _worker() -> None:
        global _cv2_window_open
        cv2 = _cv2()
        if cv2 is None:
            return
        while True:
            try:
                item = _cv2_queue.get(timeout=0.25)
            except queue.Empty:
                continue
            if item is None:
                break
            enabled, frame = item
            if not enabled:
                if _cv2_window_open:
                    try:
                        cv2.destroyWindow(_WINDOW_NAME)
                    except Exception:
                        pass
                    _cv2_window_open = False
                continue
            if frame is None:
                continue
            try:
                cv2.imshow(_WINDOW_NAME, frame)
                cv2.waitKey(1)
                _cv2_window_open = True
            except Exception as exc:
                logger.debug('cv2 debug window: %s', exc)

    _cv2_thread = threading.Thread(target=_worker, name='AimSyncCv2Debug', daemon=True)
    _cv2_thread.start()


def _draw_overlay(
    canvas: np.ndarray,
    output: np.ndarray,
    *,
    image_size: int,
    num_classes: int,
    class_names: dict[int, str],
    settings: 'AiSettings',
    selector: 'TargetSelector',
    player_label: str,
    head_label: str,
    min_confidence: float,
    active_target: 'Prediction | None',
    fps: float,
    fov_size: float | None,
    crosshair_x: int,
    crosshair_y: int,
    exclude_friendly: bool,
    region: 'DetectionRegion',
) -> np.ndarray:
    cv2 = _cv2()
    if cv2 is None:
        return canvas

    h, w = canvas.shape[:2]
    fov = float(fov_size) if fov_size is not None else float(settings.sliders.get('FOV Size', 640))
    fov_min_x = int((image_size - fov) / 2.0 * w / image_size)
    fov_max_x = int((image_size + fov) / 2.0 * w / image_size)
    fov_min_y = int((image_size - fov) / 2.0 * h / image_size)
    fov_max_y = int((image_size + fov) / 2.0 * h / image_size)
    cv2.rectangle(canvas, (fov_min_x, fov_min_y), (fov_max_x, fov_max_y), (255, 180, 0), 1)

    scale_x = w / max(1, image_size)
    scale_y = h / max(1, image_size)
    ch_x = int((crosshair_x - region.left) * scale_x)
    ch_y = int((crosshair_y - region.top) * scale_y)
    ch_x = max(0, min(w - 1, ch_x))
    ch_y = max(0, min(h - 1, ch_y))
    cv2.drawMarker(canvas, (ch_x, ch_y), (0, 255, 255), cv2.MARKER_CROSS, 12, 1)

    num_det = output.shape[2] if output is not None else 0
    for i in range(min(num_det, output.shape[2])):
        x_center = float(output[0, 0, i])
        y_center = float(output[0, 1, i])
        box_w = float(output[0, 2, i])
        box_h = float(output[0, 3, i])
        if num_classes == 1:
            conf = float(output[0, 4, i])
            class_id = 0
        else:
            scores = output[0, 4:4 + num_classes, i]
            class_id = int(np.argmax(scores))
            conf = float(scores[class_id])
        if conf < min_confidence:
            continue

        class_name = class_names.get(class_id, str(class_id))
        is_target, target_type = selector._matches_detection_class(
            class_name, class_id, player_label, head_label,
            exclude_friendly=exclude_friendly,
        )
        x1 = int((x_center - box_w / 2) * scale_x)
        y1 = int((y_center - box_h / 2) * scale_y)
        x2 = int((x_center + box_w / 2) * scale_x)
        y2 = int((y_center + box_h / 2) * scale_y)

        if is_target:
            color = (0, 255, 0) if target_type == 'player' else (0, 0, 255)
            thickness = 2
            label = f'{class_name} {conf:.2f} [{target_type}]'
        else:
            color = (0, 255, 255)
            thickness = 1
            label = f'{class_name} {conf:.2f}'

        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, thickness)
        cv2.putText(canvas, label, (x1, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    if active_target is not None:
        ax = int(active_target.x_min * scale_x)
        ay = int(active_target.y_min * scale_y)
        ax2 = int((active_target.x_min + active_target.width) * scale_x)
        ay2 = int((active_target.y_min + active_target.height) * scale_y)
        cv2.rectangle(canvas, (ax, ay), (ax2, ay2), (255, 255, 255), 2)
        aim_x = int((active_target.screen_center_x - region.left) * scale_x)
        aim_y = int((active_target.screen_center_y - region.top) * scale_y)
        cv2.circle(canvas, (aim_x, aim_y), 4, (255, 0, 255), -1)

    status = f'FPS {fps:.1f}' if fps else 'FPS —'
    if active_target:
        status += f' | target {active_target.confidence:.2f}'
    cv2.putText(canvas, status, (8, h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1)
    return canvas


def render_debug_frame(
    bgr: np.ndarray,
    output: np.ndarray,
    *,
    image_size: int,
    num_classes: int,
    class_names: dict[int, str],
    settings: 'AiSettings',
    selector: 'TargetSelector',
    player_label: str,
    head_label: str,
    player_y_offset: int,
    min_confidence: float,
    active_target: 'Prediction | None',
    fps: float = 0.0,
    fov_size: float | None = None,
    crosshair_x: int = 0,
    crosshair_y: int = 0,
    exclude_friendly: bool = False,
    region: 'DetectionRegion | None' = None,
) -> tuple[bytes | None, np.ndarray | None]:
    cv2 = _cv2()
    if cv2 is None or bgr is None:
        return None, None

    from AI.Engine.capture import DetectionRegion

    reg = region or DetectionRegion(0, 0, bgr.shape[1], bgr.shape[0])
    canvas = _draw_overlay(
        bgr.copy(),
        output,
        image_size=image_size,
        num_classes=num_classes,
        class_names=class_names,
        settings=settings,
        selector=selector,
        player_label=player_label,
        head_label=head_label,
        min_confidence=min_confidence,
        active_target=active_target,
        fps=fps,
        fov_size=fov_size,
        crosshair_x=crosshair_x,
        crosshair_y=crosshair_y,
        exclude_friendly=exclude_friendly,
        region=reg,
    )
    ok, encoded = cv2.imencode('.jpg', canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    jpeg = encoded.tobytes() if ok else None
    return jpeg, canvas


def render_debug_jpeg(
    bgr: np.ndarray,
    output: np.ndarray,
    *,
    image_size: int,
    num_classes: int,
    class_names: dict[int, str],
    settings: 'AiSettings',
    selector: 'TargetSelector',
    player_label: str,
    head_label: str,
    player_y_offset: int,
    min_confidence: float,
    active_target: 'Prediction | None',
    fps: float = 0.0,
    fov_size: float | None = None,
) -> bytes | None:
    """Backward-compatible wrapper for tests."""
    jpeg, _ = render_debug_frame(
        bgr,
        output,
        image_size=image_size,
        num_classes=num_classes,
        class_names=class_names,
        settings=settings,
        selector=selector,
        player_label=player_label,
        head_label=head_label,
        player_y_offset=player_y_offset,
        min_confidence=min_confidence,
        active_target=active_target,
        fps=fps,
        fov_size=fov_size,
    )
    return jpeg


def show_cv2_window(jpeg: bytes | None, enabled: bool, *, bgr: np.ndarray | None = None) -> None:
    """Post frames to a background thread so imshow/waitKey never blocks the AI loop."""
    if _cv2() is None:
        return
    _ensure_cv2_thread()
    if _cv2_queue is None:
        return
    frame = bgr
    if frame is None and jpeg:
        cv2 = _cv2()
        arr = np.frombuffer(jpeg, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    payload: tuple[bool, np.ndarray | None] = (enabled, frame)
    try:
        while True:
            try:
                _cv2_queue.get_nowait()
            except queue.Empty:
                break
        _cv2_queue.put_nowait(payload)
    except queue.Full:
        pass
