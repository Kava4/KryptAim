"""Bootstrap install progress reporting."""

from __future__ import annotations

import unittest

from app.bootstrap import progress as prog


class BootstrapProgressTests(unittest.TestCase):
    def test_phase_updates(self) -> None:
        prog.reset_install_progress()
        prog.set_install_phase('pip_requirements', 'Installing packages…')
        payload = prog.install_progress()
        self.assertEqual(payload['phase'], 'pip_requirements')
        self.assertIn('Installing', payload['message'])
        self.assertGreaterEqual(payload['elapsed_sec'], 0)


if __name__ == '__main__':
    unittest.main()
