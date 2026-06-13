"""GitHub model catalog helpers."""

from __future__ import annotations

import unittest

from app.ai import model_sources as ms


class ModelSourcesTests(unittest.TestCase):
    def test_cs2_name_filter(self) -> None:
        self.assertTrue(ms.is_cs2_model_name('CS2.onnx'))
        self.assertTrue(ms.is_cs2_model_name('Counter-Strike 2 (Upperbody).onnx'))
        self.assertFalse(ms.is_cs2_model_name('Apex Legends.onnx'))

    def test_fetch_aimmy_cs2_models_live(self) -> None:
        models, err = ms.fetch_aimmy_cs2_models()
        if err:
            self.skipTest(err)
        self.assertGreaterEqual(len(models), 1)
        self.assertTrue(all(m['source'] == 'aimmy' for m in models))
        self.assertTrue(all(m['download_url'] for m in models))


if __name__ == '__main__':
    unittest.main()
