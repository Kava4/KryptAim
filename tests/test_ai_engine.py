import os
import unittest

from AI.Engine.settings import AiSettings, DEFAULT_TOGGLES
from AI.Engine.target import TargetSelector
import numpy as np


class AiSettingsTests(unittest.TestCase):
    def test_defaults_match_aimmy_keys(self):
        settings = AiSettings()
        self.assertIn('Auto Trigger', settings.toggles)
        self.assertIn('FOV Size', settings.sliders)
        self.assertEqual(settings.toggles['Auto Trigger'], DEFAULT_TOGGLES['Auto Trigger'])

    def test_normalize_aimmy_key(self):
        settings = AiSettings()
        self.assertEqual(settings.normalize_aimmy_key('Right'), 'RMB')
        self.assertEqual(settings.normalize_aimmy_key('LMenu'), 'alt')


class TargetSelectorTests(unittest.TestCase):
    def test_selects_detection_inside_fov(self):
        settings = AiSettings()
        settings.sliders['FOV Size'] = 640
        settings.sliders['AI Minimum Confidence'] = 1
        selector = TargetSelector(settings)
        from AI.Engine.capture import DetectionRegion

        region = DetectionRegion(0, 0, 640, 640)
        output = np.zeros((1, 5, 8400), dtype=np.float32)
        output[0, 0, 0] = 320
        output[0, 1, 0] = 320
        output[0, 2, 0] = 80
        output[0, 3, 0] = 120
        output[0, 4, 0] = 0.95
        pred = selector.select(output, region, 640, 8400, 1)
        self.assertIsNotNone(pred)
        self.assertGreater(pred.confidence, 0.9)


class BetaConfigTests(unittest.TestCase):
    def test_beta_defaults_dict_exists(self):
        from Config.config_manager import BETA_DEFAULTS

        self.assertIn('ai_engine_enabled', BETA_DEFAULTS)
        self.assertIn('ai_active_model', BETA_DEFAULTS)


if __name__ == '__main__':
    unittest.main(verbosity=2)
