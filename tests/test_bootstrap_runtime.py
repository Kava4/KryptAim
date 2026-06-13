"""AppData runtime bootstrap (slim exe)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.bootstrap import runtime as rt


class BootstrapRuntimeTests(unittest.TestCase):
    def test_bootstrap_status_shape(self) -> None:
        status = rt.bootstrap_status()
        for key in (
            'frozen',
            'bundled_ai',
            'runtime_ready',
            'ai_available',
            'needs_bootstrap',
            'install_phase',
            'install_message',
            'install_log',
        ):
            self.assertIn(key, status)

    @patch.object(rt, 'is_frozen', return_value=False)
    def test_dev_mode_bundled_ai(self, _frozen: object) -> None:
        self.assertTrue(rt.bundled_ai_stack())

    @patch.object(rt, 'is_frozen', return_value=True)
    @patch('importlib.util.find_spec', return_value=None)
    def test_lite_frozen_not_bundled(self, _spec: object, _frozen: object) -> None:
        self.assertFalse(rt.bundled_ai_stack())

    @patch.object(rt, 'is_runtime_ready', return_value=False)
    @patch.object(rt, 'bundled_ai_stack', return_value=False)
    def test_needs_bootstrap_when_frozen_lite(self, _b: object, _r: object) -> None:
        with patch.object(rt, 'is_frozen', return_value=True):
            status = rt.bootstrap_status()
        self.assertTrue(status['needs_bootstrap'])


if __name__ == '__main__':
    unittest.main()
