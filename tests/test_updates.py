"""GitHub release update checks."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.core import updates as upd


class UpdatesTests(unittest.TestCase):
    def test_version_compare(self) -> None:
        self.assertTrue(upd.version_lt('0.1.0', '0.2.0'))
        self.assertFalse(upd.version_lt('0.2.0', '0.2.0'))
        self.assertFalse(upd.version_lt('0.3.0', '0.2.0'))

    @patch('app.core.updates.get_json')
    def test_check_parses_release(self, mock_get) -> None:
        mock_get.return_value = (
            {
                'tag_name': 'v0.2.0',
                'body': 'Bug fixes',
                'html_url': 'https://github.com/Kava4/AimSync/releases/tag/v0.2.0',
                'assets': [
                    {
                        'name': 'AimSync.exe',
                        'browser_download_url': 'https://example.com/AimSync.exe',
                        'size': 12345,
                    },
                ],
            },
            None,
        )
        with patch.object(upd, 'current_version', return_value='0.1.0'):
            status = upd.check_for_updates()
        self.assertTrue(status['success'])
        self.assertTrue(status['update_available'])
        self.assertEqual(status['latest_version'], '0.2.0')


if __name__ == '__main__':
    unittest.main()
