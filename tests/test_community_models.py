"""Community model catalog + download helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.ai import community_models as cm


class CommunityModelsTests(unittest.TestCase):
    def test_normalize_string_entry(self) -> None:
        entry = cm._normalize_entry('cs2_640.onnx')
        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertEqual(entry['filename'], 'cs2_640.onnx')

    def test_normalize_rejects_bad_ext(self) -> None:
        self.assertIsNone(cm._normalize_entry('readme.txt'))

    def test_status_marks_installed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            models = Path(tmp) / 'models'
            models.mkdir(parents=True)
            (models / 'local.onnx').write_bytes(b'x' * 2048)
            with patch.object(cm, 'models_dir', return_value=models):
                with patch.object(
                    cm,
                    'fetch_all_community_models',
                    return_value={
                        'online': True,
                        'error': None,
                        'models': [
                            {'filename': 'local.onnx', 'title': 'Local', 'source': 'aimsync'},
                            {'filename': 'remote.onnx', 'title': 'Remote', 'source': 'aimmy'},
                        ],
                    },
                ):
                    status = cm.community_models_status()
            self.assertTrue(status['online'])
            self.assertEqual(len(status['installed']), 1)
            self.assertEqual(len(status['available']), 1)
            self.assertFalse(status['all_installed'])

    def test_download_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            models = Path(tmp) / 'models'
            models.mkdir(parents=True)
            payload = b'\x00' * 5000
            with patch.object(cm, 'models_dir', return_value=models):
                with patch.object(
                    cm,
                    'community_models_status',
                    return_value={'catalog': [{'filename': 'new.onnx', 'download_url': 'https://example.com/new.onnx'}]},
                ):
                    with patch.object(cm, 'download_model_from_url', return_value=(payload, None)):
                        path, msg = cm.download_community_model('new.onnx')
            self.assertIsNotNone(path)
            assert path is not None
            self.assertTrue(path.is_file())
            self.assertEqual(msg, 'Downloaded')


if __name__ == '__main__':
    unittest.main()
