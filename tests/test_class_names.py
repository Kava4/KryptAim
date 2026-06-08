import unittest
from pathlib import Path

from AI.Engine.class_names import _names_from_filename, resolve_class_names


class ClassNamesTests(unittest.TestCase):
    def test_cs2_filename_preset(self):
        path = Path('cs2_640.onnx')
        names = _names_from_filename(path, 2)
        self.assertEqual(names, {0: 'CT', 1: 'T'})

    def test_resolve_fallback_numeric(self):
        names = resolve_class_names(Path('unknown_game.onnx'), 2)
        self.assertIn(0, names)
        self.assertIn(1, names)

    def test_resolve_cs2_bundled_model_if_present(self):
        root = Path(__file__).resolve().parents[1]
        candidates = [
            root / '.beta-data' / 'bin' / 'models' / 'cs2_640.onnx',
            root / 'vendor-ai-reference' / 'src' / 'models' / 'cs2_640.onnx',
        ]
        path = next((p for p in candidates if p.is_file()), None)
        if path is None:
            self.skipTest('cs2_640.onnx not in bin/models or vendor-ai-reference')
        names = resolve_class_names(path, 2)
        self.assertEqual(names.get(0), 'CT')
        self.assertEqual(names.get(1), 'T')


if __name__ == '__main__':
    unittest.main()
