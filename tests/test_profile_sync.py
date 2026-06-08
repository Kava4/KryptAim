import unittest

from AI.Engine.profile_sync import (
    PROFILE_ALIAS_MAP,
    apply_config_globals,
    effective_region_size,
    import_profile_dict,
)
from AI.Engine.settings import AiSettings


class ProfileSyncTests(unittest.TestCase):
    def test_region_size_maps_to_fov(self):
        settings = AiSettings()
        import_profile_dict({'region_size': 200}, settings)
        self.assertEqual(settings.sliders['FOV Size'], 200.0)

    def test_config_region_overrides_cfg(self):
        settings = AiSettings()
        settings.sliders['FOV Size'] = 640.0
        config = {'ai_region_size': 200}
        apply_config_globals(settings, config)
        self.assertEqual(effective_region_size(settings, config), 200.0)

    def test_always_on_aim_flag(self):
        settings = AiSettings()
        apply_config_globals(settings, {'ai_always_on_aim': True})
        self.assertTrue(settings.toggles['Constant AI Tracking'])

    def test_dynamic_fov_shrinks_region(self):
        settings = AiSettings()
        settings.toggles['Dynamic FOV'] = True
        settings.sliders['FOV Size'] = 400.0
        settings.sliders['Dynamic FOV Size'] = 120.0
        self.assertEqual(effective_region_size(settings, {}, use_dynamic=True), 120.0)

    def test_dynamic_fov_off_uses_base(self):
        settings = AiSettings()
        settings.sliders['FOV Size'] = 400.0
        settings.sliders['Dynamic FOV Size'] = 120.0
        self.assertEqual(effective_region_size(settings, {}, use_dynamic=True), 400.0)

    def test_save_cfg_uses_alias_keys(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        settings = AiSettings()
        settings.toggles['Aim Assist'] = True
        settings.sliders['FOV Size'] = 200.0
        with tempfile.TemporaryDirectory() as tmp:
            with patch('AI.Engine.settings.get_ai_configs_dir', return_value=Path(tmp)):
                settings.save_cfg('Test.cfg')
            data = json.loads((Path(tmp) / 'Test.cfg').read_text(encoding='utf-8'))
        self.assertIn('aim_assist', data)
        self.assertIn('region_size', data)
        self.assertNotIn('Aim Assist', data)

    def test_alias_map_covers_core_fields(self):
        self.assertIn('region_size', PROFILE_ALIAS_MAP)
        self.assertIn('dynamic_fov', PROFILE_ALIAS_MAP)
        self.assertIn('always_on_aim', PROFILE_ALIAS_MAP)
        self.assertIn('auto_trigger', PROFILE_ALIAS_MAP)


if __name__ == '__main__':
    unittest.main()
