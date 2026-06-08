import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import Config.config_manager as config_manager


class ConfigManagerTests(unittest.TestCase):
    def test_load_recovers_from_empty_config_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / 'config.json'
            config_path.write_text('', encoding='utf-8')
            with patch.object(config_manager, 'CONFIG_FILE', config_path):
                with patch.object(config_manager, 'get_base_dir', return_value=Path(tmp)):
                    data = config_manager.load_config()
            self.assertTrue(config_path.is_file())
            self.assertGreater(config_path.stat().st_size, 0)
            self.assertIn('recoil_enabled', data)

    def test_save_is_readable_by_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / 'config.json'
            with patch.object(config_manager, 'CONFIG_FILE', config_path):
                with patch.object(config_manager, 'get_base_dir', return_value=Path(tmp)):
                    payload = config_manager._default_config()
                    payload['recoil_enabled'] = True
                    config_manager.save_config(payload)
                    loaded = config_manager.load_config()
            self.assertTrue(loaded['recoil_enabled'])

    def test_simple_mode_not_forced_to_cs2_for_game_weapon(self):
        payload = config_manager._default_config()
        payload['recoil_mode'] = 'simple'
        payload['recoil_game_settings']['weapon'] = 'famas'
        normalized = config_manager._normalize_loaded_config(payload)
        self.assertEqual(normalized['recoil_mode'], 'simple')
        self.assertEqual(normalized['recoil_game_settings']['weapon'], 'famas')


if __name__ == '__main__':
    unittest.main(verbosity=2)
