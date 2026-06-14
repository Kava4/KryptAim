"""Donor-only AI access rules."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.core import licensing as lic


class LicensingTests(unittest.TestCase):
    def tearDown(self) -> None:
        lic.invalidate_license_cache()
        os.environ.pop('KRYPTAIM_AI_UNLOCK', None)
        os.environ.pop('KRYPTAIM_AI_PREMIUM_ONLY', None)

    def test_ai_free_when_premium_not_required(self) -> None:
        with patch('app.core.licensing.ai_premium_required', return_value=False):
            status = lic.ai_access_status(refresh=True)
        self.assertTrue(status['allowed'])
        self.assertFalse(status['premium_required'])

    def test_trial_key_blocks_ai(self) -> None:
        with patch('app.core.licensing.ai_premium_required', return_value=True):
            data = {'valid': True, 'tier': 'Donator', 'display_name': 'Free Trial: 10m left'}
            self.assertFalse(lic.ai_access_allowed(data, ''))
            self.assertTrue(lic.is_trial_license('', data))

    def test_donator_key_allows_ai(self) -> None:
        with patch('app.core.licensing.ai_premium_required', return_value=True):
            data = {'valid': True, 'tier': 'Donator', 'display_name': 'Kava'}
            self.assertTrue(lic.ai_access_allowed(data, 'KOFI-ABC123'))

    def test_dev_unlock_env(self) -> None:
        os.environ['KRYPTAIM_AI_UNLOCK'] = '1'
        status = lic.ai_access_status(refresh=True)
        self.assertTrue(status['allowed'])

    @patch('app.core.licensing.ai_premium_required', return_value=True)
    @patch.object(lic, 'validate_license', return_value={'valid': True, 'tier': 'Donator', 'display_name': 'Supporter'})
    @patch.object(lic, 'load_config', return_value={'license_key': 'REAL-KEY-1'})
    def test_access_status_allowed(self, _cfg, _validate, _premium) -> None:
        status = lic.ai_access_status(refresh=True)
        self.assertTrue(status['allowed'])

    def test_dev_key_validates_locally(self) -> None:
        with patch.object(lic, 'dev_keys_enabled', return_value=True):
            result = lic.validate_license('DEV-KRYPTAIM')
        self.assertTrue(result['valid'])
        self.assertEqual(result['tier'], 'Dev')
        self.assertTrue(lic.ai_access_allowed(result, 'DEV-KRYPTAIM'))

    def test_dev_key_blocked_when_disabled(self) -> None:
        with patch('app.core.licensing.ai_premium_required', return_value=True):
            with patch.object(lic, 'load_config', return_value={'license_key': 'DEV-KRYPTAIM'}):
                with patch.object(lic, 'dev_keys_enabled', return_value=False):
                    with patch.object(lic, '_refresh_if_stale', return_value=lic._dev_license_result('DEV-KRYPTAIM')):
                        status = lic.ai_access_status(refresh=False)
        self.assertFalse(status['allowed'])
        self.assertIn('disabled', status['message'].lower())

    def test_custom_dev_key_from_env(self) -> None:
        os.environ['AIMSYNC_DEV_KEYS'] = 'MYTEST-KEY'
        self.assertTrue(lic.is_dev_license_key('mytest-key'))
        os.environ.pop('AIMSYNC_DEV_KEYS', None)


if __name__ == '__main__':
    unittest.main()
