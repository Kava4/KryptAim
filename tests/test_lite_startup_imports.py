"""Slim exe must start before AppData AI runtime (no numpy in bundle)."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _probe_python() -> str:
    for candidate in (
        ROOT / '.venv' / 'Scripts' / 'python.exe',
        ROOT / 'build-venv' / 'Scripts' / 'python.exe',
    ):
        if candidate.is_file():
            return str(candidate)
    return sys.executable

_IMPORT_PROBE = """
import sys

class _BlockNumpy:
    def find_module(self, name, path=None):
        if name == 'numpy' or name.startswith('numpy.'):
            return self

    def load_module(self, name):
        raise ImportError(f'blocked: {name}')

sys.meta_path.insert(0, _BlockNumpy())
from web.app import create_app
create_app()
print('ok')
"""


class LiteStartupImportTests(unittest.TestCase):
    def test_web_app_imports_without_numpy(self) -> None:
        env = os.environ.copy()
        env['PYTHONPATH'] = str(ROOT)
        result = subprocess.run(
            [_probe_python(), '-c', _IMPORT_PROBE],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=result.stdout + result.stderr,
        )
        self.assertIn('ok', result.stdout)


if __name__ == '__main__':
    unittest.main()
