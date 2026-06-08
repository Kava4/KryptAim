import unittest

from AI.Engine.settings import (
    AiSettings,
    apply_default_ai_profile,
    is_experimental_dropdown,
    is_experimental_slider,
    is_experimental_toggle,
)


class AiBaselineDefaultsTests(unittest.TestCase):
    def test_apply_default_ai_profile(self):
        settings = AiSettings()
        settings.sliders['Mouse Sensitivity (+/-)'] = 0.8
        settings.sliders['Mouse Jitter'] = 4
        settings.toggles['Sticky Aim'] = True
        apply_default_ai_profile(settings)
        self.assertEqual(settings.sliders['Mouse Sensitivity (+/-)'], 0.0)
        self.assertEqual(settings.sliders['Mouse Jitter'], 0.0)
        self.assertFalse(settings.toggles['Sticky Aim'])
        self.assertFalse(settings.toggles['Predictions'])
        self.assertEqual(settings.dropdowns['Movement Path'], 'Linear')

    def test_experimental_detection(self):
        self.assertTrue(is_experimental_slider('Mouse Sensitivity (+/-)', 0.5))
        self.assertFalse(is_experimental_slider('Mouse Sensitivity (+/-)', 0.0))
        self.assertTrue(is_experimental_toggle('Sticky Aim', True))
        self.assertFalse(is_experimental_toggle('Sticky Aim', False))
        self.assertTrue(is_experimental_dropdown('Movement Path', 'Cubic Bezier'))
        self.assertFalse(is_experimental_dropdown('Movement Path', 'Linear'))


if __name__ == '__main__':
    unittest.main()
