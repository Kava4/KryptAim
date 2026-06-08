"""Target class filter and aim crosshair math."""
import unittest

import numpy as np

from AI.Engine.aim import AimController
from AI.Engine.capture import DetectionRegion
from AI.Engine.settings import AiSettings
from AI.Engine.target import Prediction, TargetSelector


class TargetClassFilterTests(unittest.TestCase):
    def setUp(self):
        self.settings = AiSettings()
        self.settings.sliders['FOV Size'] = 640
        self.settings.sliders['AI Minimum Confidence'] = 1
        self.selector = TargetSelector(self.settings)
        self.region = DetectionRegion(640, 220, 640, 640)
        self.class_names = {0: 'CT', 1: 'T'}

    def _output_with_class(self, class_id: int, x: float = 320, y: float = 320):
        output = np.zeros((1, 6, 8400), dtype=np.float32)
        output[0, 0, 0] = x
        output[0, 1, 0] = y
        output[0, 2, 0] = 80
        output[0, 3, 0] = 120
        output[0, 4 + class_id, 0] = 0.95
        return output

    def test_exclude_friendly_skips_my_team(self):
        output = self._output_with_class(0)
        pred = self.selector.select(
            output,
            self.region,
            640,
            8400,
            num_classes=2,
            class_names=self.class_names,
            player_label='CT',
            head_label='',
            exclude_friendly=True,
        )
        self.assertIsNone(pred)

    def test_exclude_friendly_targets_enemy(self):
        output = self._output_with_class(1)
        pred = self.selector.select(
            output,
            self.region,
            640,
            8400,
            num_classes=2,
            class_names=self.class_names,
            player_label='CT',
            head_label='',
            exclude_friendly=True,
        )
        self.assertIsNotNone(pred)
        self.assertEqual(pred.class_id, 1)

    def test_target_label_mode_keeps_legacy_behavior(self):
        output = self._output_with_class(0)
        pred = self.selector.select(
            output,
            self.region,
            640,
            8400,
            num_classes=2,
            class_names=self.class_names,
            player_label='CT',
            head_label='',
            exclude_friendly=False,
        )
        self.assertIsNotNone(pred)
        self.assertEqual(pred.class_id, 0)


class AimCrosshairTests(unittest.TestCase):
    def test_compute_move_uses_stream_crosshair(self):
        settings = AiSettings()
        settings.sliders['Mouse Sensitivity (+/-)'] = 0.0
        aim = AimController(settings, 1920, 1080)
        target = Prediction(
            x_min=920,
            y_min=480,
            width=80,
            height=120,
            confidence=0.9,
            class_id=1,
            screen_center_x=960,
            screen_center_y=540,
            detection_box=(920, 480, 80, 120),
        )
        move_x, move_y = aim.compute_move(target, crosshair_x=960, crosshair_y=540)
        self.assertEqual(move_x, 0)
        self.assertEqual(move_y, 0)

    def test_compute_move_offsets_from_crosshair(self):
        settings = AiSettings()
        settings.sliders['Mouse Sensitivity (+/-)'] = 0.0
        settings.sliders['X Offset (Left/Right)'] = 0.0
        settings.sliders['Y Offset (Up/Down)'] = 0.0
        aim = AimController(settings, 1920, 1080)
        target = Prediction(
            x_min=960,
            y_min=500,
            width=80,
            height=120,
            confidence=0.9,
            class_id=1,
            screen_center_x=1000,
            screen_center_y=560,
            detection_box=(960, 500, 80, 120),
        )
        move_x, move_y = aim.compute_move(target, crosshair_x=960, crosshair_y=540)
        self.assertEqual(move_x, 40)
        self.assertEqual(move_y, 20)


if __name__ == '__main__':
    unittest.main()
