"""Cloud supporter license validation."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.core import license_cloud as lc


class LicenseCloudTests(unittest.TestCase):
    def tearDown(self) -> None:
        lc.invalidate_license_cache()
        os.environ.pop('KRYPTAIM_DEV', None)
        os.environ.pop('KRYPTAIM_DEV_KEYS', None)

    def test_dev_key_requires_dev_mode(self) -> None:
        os.environ.pop('KRYPTAIM_DEV', None)
        result = lc.validate_license('DEV-KRYPTAIM', refresh=True)
        self.assertFalse(result['valid'])
        self.assertTrue(result.get('dev_disabled'))

    def test_dev_key_works_in_dev_mode(self) -> None:
        os.environ['KRYPTAIM_DEV'] = '1'
        result = lc.validate_license('DEV-KRYPTAIM', refresh=True)
        self.assertTrue(result['valid'])
        self.assertEqual(result['tier'], 'Dev')

    @patch('app.core.license_cloud._cloud_validate')
    def test_cloud_valid_unlimited_key(self, mock_validate) -> None:
        mock_validate.return_value = ({
            'valid': True,
            'tier': 'Supporter Unlimited',
            'plan': 'unlimited',
            'display_name': 'VIP',
            'unlimited': True,
            'days_left': None,
        }, None)
        result = lc.validate_license('KR-AB-CD-EF', refresh=True)
        self.assertTrue(result['valid'])
        self.assertTrue(result['unlimited'])

    @patch('app.core.license_cloud._cloud_validate')
    def test_cloud_valid_monthly_key(self, mock_validate) -> None:
        mock_validate.return_value = ({
            'valid': True,
            'tier': 'Supporter Monthly',
            'plan': 'monthly',
            'display_name': 'Kava',
            'unlimited': False,
            'days_left': 28,
        }, None)
        result = lc.validate_license('KR-AB-CD-EF', refresh=True)
        self.assertTrue(lc.supporter_unlock_active('KR-AB-CD-EF', refresh=True))
        self.assertFalse(result.get('unlimited'))

    @patch('app.core.license_cloud._cloud_validate')
    def test_cloud_expired_monthly(self, mock_validate) -> None:
        mock_validate.return_value = ({
            'valid': False,
            'plan': 'monthly',
            'message': 'Monthly subscription expired',
        }, None)
        self.assertFalse(lc.supporter_unlock_active('KR-OLD-KEY-01', refresh=True))

    @patch('app.core.license_cloud._cloud_validate')
    def test_cloud_valid_key(self, mock_validate) -> None:
        mock_validate.return_value = ({
            'valid': True,
            'tier': 'Supporter',
            'display_name': 'Kava',
            'message': '',
        }, None)
        result = lc.validate_license('KR-AB-CD-EF', refresh=True)
        self.assertTrue(result['valid'])
        self.assertEqual(result['display_name'], 'Kava')

    @patch('app.core.license_cloud._cloud_validate')
    def test_cloud_revoked_key(self, mock_validate) -> None:
        mock_validate.return_value = ({
            'valid': False,
            'tier': 'Free',
            'display_name': '',
            'message': 'Key revoked',
        }, None)
        result = lc.validate_license('KR-BAD-KEY-01', refresh=True)
        self.assertFalse(result['valid'])

    @patch('app.core.license_cloud._cloud_validate')
    def test_cache_hits_without_second_call(self, mock_validate) -> None:
        mock_validate.return_value = ({
            'valid': True,
            'tier': 'Supporter',
            'display_name': 'Cached',
        }, None)
        lc.validate_license('KR-CACHE-01', refresh=True)
        lc.validate_license('KR-CACHE-01', refresh=False)
        self.assertEqual(mock_validate.call_count, 1)


if __name__ == '__main__':
    unittest.main()
