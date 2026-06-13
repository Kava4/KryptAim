"""Embeddable Python bootstrap helpers."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from app.bootstrap import embed_python as ep


class EmbedPythonTests(unittest.TestCase):
    def test_embed_zip_url(self) -> None:
        url = ep.embed_zip_url('3.12.10')
        self.assertIn('python-3.12.10-embed-amd64.zip', url)
        self.assertTrue(url.startswith('https://www.python.org/ftp/python/'))

    def test_configure_embed_pth(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            embed = Path(tmp)
            (embed / 'python312.zip').write_bytes(b'')
            (embed / 'python312._pth').write_text('python312.zip\n.\n', encoding='utf-8')
            ep._configure_embed_pth(embed)
            text = (embed / 'python312._pth').read_text(encoding='utf-8')
            self.assertIn('Lib\\site-packages', text)
            self.assertIn('import site', text)
            self.assertTrue((embed / 'Lib' / 'site-packages').is_dir())

    @patch.object(ep, 'is_embed_ready', return_value=True)
    @patch.object(ep, 'embed_python_exe')
    def test_ensure_skips_when_ready(self, mock_exe: object, _ready: object) -> None:
        expected = Path('C:/fake/python.exe')
        mock_exe.return_value = expected
        self.assertEqual(ep.ensure_embed_python(), expected)


if __name__ == '__main__':
    unittest.main()
