"""Trigger zone: radius + bbox fallback for NDI center crosshair."""

from AI.Engine.capture import DetectionRegion
from AI.Engine.settings import AiSettings
from AI.Engine.trigger import TriggerController
from AI.Engine.target import Prediction


class _FakeCapture:
    screen_width = 640
    screen_height = 640

    def cursor_position(self):
        return 320, 320


def _target_at(center_x: float, center_y: float, size: float = 80.0) -> Prediction:
    half = size / 2
    region = DetectionRegion(left=0, top=0, width=640, height=640)
    return Prediction(
        x_min=center_x - half,
        y_min=center_y - half,
        width=size,
        height=size,
        confidence=0.9,
        class_id=0,
        screen_center_x=region.left + center_x,
        screen_center_y=region.top + center_y,
        detection_box=(center_x - half, center_y - half, size, size),
    )


def test_trigger_zone_accepts_crosshair_inside_bbox():
    settings = AiSettings()
    settings.toggles['Auto Trigger'] = True
    ctrl = TriggerController(settings, _FakeCapture())
    target = _target_at(340, 320)
    assert ctrl._crosshair_in_trigger_zone(
        target, crosshair_x=320, crosshair_y=320, radius_px=8,
    )
