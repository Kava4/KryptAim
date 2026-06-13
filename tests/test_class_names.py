"""YOLO class name resolution."""

from __future__ import annotations

import unittest
from pathlib import Path

from app.ai.class_names import _names_from_filename, resolve_class_names


class ClassNamesTests(unittest.TestCase):
    def test_cs2_filename_preset(self) -> None:
        names = _names_from_filename(Path('cs2_640.onnx'), 2)
        self.assertEqual(names, {0: 'CT', 1: 'T'})

    def test_resolve_fallback_numeric(self) -> None:
        names = resolve_class_names(Path('unknown_game.onnx'), 2)
        self.assertIn(0, names)
        self.assertIn(1, names)


if __name__ == '__main__':
    unittest.main()
