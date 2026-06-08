import unittest

from AI.Engine.readiness import build_readiness
from AI.Engine.settings import AiSettings, apply_default_ai_profile


class AiReadinessTests(unittest.TestCase):
    def test_starter_profile_enables_aim_assist(self):
        settings = AiSettings()
        apply_default_ai_profile(settings)
        self.assertTrue(settings.toggles['Aim Assist'])
        self.assertEqual(settings.sliders['Mouse Sensitivity (+/-)'], 0.0)
        self.assertEqual(settings.sliders['Mouse Jitter'], 0.0)
        self.assertFalse(settings.toggles['Sticky Aim'])
        self.assertFalse(settings.toggles['Predictions'])

    def test_readiness_not_ready_without_engine(self):
        settings = AiSettings()
        apply_default_ai_profile(settings)
        result = build_readiness(
            status={
                'makcu_connected': False,
                'model_loaded': False,
                'model_classes': ['0', '1'],
                'onnx_ready': True,
                'inference_backend': 'directml',
            },
            settings=settings,
        )
        self.assertFalse(result['ready'])
        ids = {i['id'] for i in result['items'] if not i['ok']}
        self.assertIn('engine', ids)


if __name__ == '__main__':
    unittest.main()
