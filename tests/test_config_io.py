"""Config atomic save / corrupt read."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core import config as cfg


class ConfigIoTests(unittest.TestCase):
    def test_load_empty_file_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.json'
            path.write_text('', encoding='utf-8')
            with patch.object(cfg, 'config_path', return_value=path):
                data = cfg.load_config()
            self.assertTrue(data.get('recoil_mode') == 'CS2')

    def test_save_atomic_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.json'
            with patch.object(cfg, 'config_path', return_value=path):
                cfg.save_config({'ai_enabled': True, 'ai_assist_mode': 'aim'})
                loaded = cfg.load_config()
            self.assertTrue(loaded.get('ai_enabled'))
            self.assertEqual(loaded.get('ai_assist_mode'), 'aim')
            self.assertTrue(loaded.get('ai_aim_enabled'))
            self.assertFalse(loaded.get('ai_trigger_enabled'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
