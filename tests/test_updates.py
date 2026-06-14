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
                'html_url': 'https://github.com/Kava4/KryptAim/releases/tag/v0.2.0',
                'assets': [
                    {
                        'name': 'KryptAim.exe',
                        'browser_download_url': 'https://example.com/KryptAim.exe',
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

    @patch('app.core.updates._latest_via_redirect')
    @patch('app.core.updates.get_json')
    def test_check_falls_back_on_rate_limit(self, mock_get, mock_redirect) -> None:
        mock_get.return_value = (None, 'HTTP 403')
        mock_redirect.return_value = (
            '0.2.0',
            'https://github.com/AimSyncCore/KryptAim/releases/tag/v0.2.0',
            'https://github.com/AimSyncCore/KryptAim/releases/download/v0.2.0/KryptAim.exe',
            'KryptAim.exe',
            None,
        )
        with patch.object(upd, 'current_version', return_value='0.1.0'):
            status = upd.check_for_updates()
        self.assertTrue(status['success'])
        self.assertTrue(status['update_available'])
        self.assertEqual(status['latest_version'], '0.2.0')
        mock_redirect.assert_called_once()


if __name__ == '__main__':
    unittest.main()
