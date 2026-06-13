"""Aim assist tests."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.ai.aim import AimController, aim_armed
from app.ai.capture.backend import FrameContext
from app.ai.capture.region import DetectionRegion
from app.ai.types import Prediction


def _frame() -> FrameContext:
    return FrameContext(
        bgr=__import__('numpy').zeros((640, 640, 3), dtype='uint8'),
        region=DetectionRegion(left=420, top=0, width=1080, height=1080),
        image_size=640,
        crosshair_x=960,
        crosshair_y=540,
    )


class AimArmedTests(unittest.TestCase):
    @patch('app.ai.aim.makcu_manager')
    def test_trigger_always_on_arms_aim(self, makcu) -> None:
        makcu.get_button_state.return_value = False
        config = {
            'ai_enabled': True,
            'ai_aim_enabled': True,
            'ai_trigger_always_on': True,
        }
        self.assertTrue(aim_armed(config))


class AimControllerTests(unittest.TestCase):
    @patch('app.ai.aim.makcu_manager')
    def test_step_moves_toward_target(self, makcu) -> None:
        ctrl = AimController()
        config = {
            'ai_enabled': True,
            'ai_aim_enabled': True,
            'ai_trigger_min_conf': 0.35,
            'ai_aim_speed': 1.0,
            'ai_aim_max_px': 300,
            'recoil_cs2_settings': {'cs2_sensitivity': 1.25},
        }
        target = Prediction(
            confidence=0.9,
            image_dist=50.0,
            screen_center_x=400.0,
            screen_center_y=320.0,
        )
        ctrl.update_correction(
            config,
            armed=True,
            targets=[target],
            frame=_frame(),
        )
        self.assertEqual(ctrl.last_block_reason, 'tracking')
        ctrl.step(armed=True)
        makcu.move_relative.assert_called_once()
        self.assertNotEqual(makcu.move_relative.call_args[0][0], 0.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
