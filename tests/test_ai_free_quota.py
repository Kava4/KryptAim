"""Free Vision AI daily quota."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from app.core import ai_free_quota as qmod
from app.core.ai_access import resolve_ai_access


class AiFreeQuotaTests(unittest.TestCase):
    def setUp(self) -> None:
        qmod._MANAGER = None
        os.environ['KRYPTAIM_AI_FREE_QUOTA_CLOUD_OFF'] = '1'
        self._tmpdir = tempfile.TemporaryDirectory()
        self._usage = Path(self._tmpdir.name) / 'ai_free_usage.json'

    def tearDown(self) -> None:
        qmod._MANAGER = None
        self._tmpdir.cleanup()
        os.environ.pop('KRYPTAIM_AI_FREE_QUOTA_OFF', None)
        os.environ.pop('AIMSYNC_AI_FREE_QUOTA_OFF', None)
        os.environ.pop('AI_FREE_DAILY_MINUTES', None)
        os.environ.pop('KRYPTAIM_AI_FREE_DAILY_MINUTES', None)
        os.environ.pop('KRYPTAIM_AI_FREE_QUOTA_CLOUD_OFF', None)
        os.environ.pop('AIMSYNC_AI_FREE_QUOTA_CLOUD_OFF', None)

    def _manager(self, *, limit_minutes: int = 120) -> qmod.AiFreeQuotaManager:
        os.environ['KRYPTAIM_AI_FREE_DAILY_MINUTES'] = str(limit_minutes)
        with patch.object(qmod, '_usage_path', return_value=self._usage):
            qmod._MANAGER = None
            return qmod.get_ai_free_quota_manager()

    def test_persists_usage_across_restarts(self) -> None:
        mgr = self._manager(limit_minutes=120)
        with patch.object(qmod, '_usage_path', return_value=self._usage):
            mgr._used_seconds = 3600.0
            mgr._persist(force=True)
            qmod._MANAGER = None
            reloaded = qmod.get_ai_free_quota_manager()
            self.assertAlmostEqual(reloaded.total_used_seconds(), 3600.0, places=0)

    def test_session_flush_on_stop(self) -> None:
        mgr = self._manager(limit_minutes=120)
        with patch.object(qmod, '_usage_path', return_value=self._usage):
            mgr.sync_engine_state(True)
            mgr._session_started = qmod.time.monotonic() - 45
            mgr.sync_engine_state(False)
            self.assertGreaterEqual(mgr._used_seconds, 40.0)

    def test_exhausted_when_limit_reached(self) -> None:
        mgr = self._manager(limit_minutes=2)
        mgr._limit_seconds = 120
        mgr._used_seconds = 120.0
        status = mgr.public_status()
        self.assertTrue(status['exhausted'])
        self.assertEqual(status['remaining_minutes'], 0)

    def test_day_rollover_resets_usage(self) -> None:
        self._usage.write_text(
            json.dumps({'v': 1, 'date': '2000-01-01', 'used_seconds': 5000, 'updated_at': 1.0, 'sig': 'bad'}),
            encoding='utf-8',
        )
        mgr = self._manager()
        with patch.object(qmod, '_usage_path', return_value=self._usage):
            qmod._MANAGER = None
            mgr = qmod.get_ai_free_quota_manager()
        self.assertEqual(mgr._usage_date, date.today().isoformat())
        self.assertEqual(mgr._used_seconds, 0.0)

    def test_tampered_signature_exhausts_quota(self) -> None:
        mgr = self._manager(limit_minutes=120)
        with patch.object(qmod, '_usage_path', return_value=self._usage):
            mgr._used_seconds = 1800.0
            mgr._persist(force=True)
            data = json.loads(self._usage.read_text(encoding='utf-8'))
            data['used_seconds'] = 0.0
            self._usage.write_text(json.dumps(data, indent=2), encoding='utf-8')
            qmod._MANAGER = None
            reloaded = qmod.get_ai_free_quota_manager()
            self.assertTrue(reloaded.is_exhausted())
            self.assertEqual(reloaded.remaining_seconds(), 0.0)

    def test_legacy_unsigned_file_migrates_with_signature(self) -> None:
        self._usage.write_text(
            json.dumps({'date': date.today().isoformat(), 'used_seconds': 900.0, 'updated_at': 1.0}),
            encoding='utf-8',
        )
        with patch.object(qmod, '_usage_path', return_value=self._usage):
            mgr = self._manager(limit_minutes=120)
            self.assertAlmostEqual(mgr.total_used_seconds(), 900.0, places=0)
            saved = json.loads(self._usage.read_text(encoding='utf-8'))
            self.assertEqual(saved.get('v'), 1)
            self.assertTrue(saved.get('sig'))

    @patch('app.core.ai_access.ai_premium_required', return_value=False)
    @patch('app.core.ai_access.donor_unlock_active', return_value=False)
    @patch('app.core.ai_access.quota_feature_enabled', return_value=True)
    def test_resolve_access_uses_remaining_quota(self, _feat, _donor, _premium) -> None:
        mgr = self._manager(limit_minutes=120)
        mgr._used_seconds = 3600.0
        with patch('app.core.ai_access.get_ai_free_quota_manager', return_value=mgr):
            status = resolve_ai_access(refresh=True)
        self.assertTrue(status['allowed'])
        self.assertEqual(status['free_quota']['remaining_minutes'], 60)

    @patch('app.core.ai_access.ai_premium_required', return_value=False)
    @patch('app.core.ai_access.donor_unlock_active', return_value=True)
    def test_donor_bypasses_quota(self, _donor, _premium) -> None:
        status = resolve_ai_access(refresh=True)
        self.assertTrue(status['allowed'])
        self.assertTrue(status['donor_unlock'])
        self.assertFalse(status['free_quota']['applies'])

    @patch('app.core.cloud.fetch_ai_quota_status')
    @patch('app.core.cloud.post_ai_quota_tick')
    def test_cloud_refresh_overwrites_tampered_local(self, mock_tick, mock_status) -> None:
        os.environ.pop('KRYPTAIM_AI_FREE_QUOTA_CLOUD_OFF', None)
        os.environ.pop('AIMSYNC_AI_FREE_QUOTA_CLOUD_OFF', None)
        mock_status.return_value = ({
            'ok': True,
            'date': date.today().isoformat(),
            'limit_seconds': 7200,
            'used_seconds': 5400,
            'remaining_seconds': 1800,
            'exhausted': False,
        }, None)
        mock_tick.return_value = (None, None)
        self._usage.write_text(
            json.dumps({'v': 1, 'date': date.today().isoformat(), 'used_seconds': 0, 'updated_at': 1.0, 'sig': 'x'}),
            encoding='utf-8',
        )
        with patch.object(qmod, '_usage_path', return_value=self._usage):
            with patch.object(qmod, '_verify_usage', return_value=True):
                mgr = self._manager(limit_minutes=120)
        self.assertAlmostEqual(mgr.total_used_seconds(), 5400.0, places=0)
        self.assertTrue(mgr._cloud_synced)

    @patch('app.core.cloud.post_ai_quota_tick')
    @patch('app.core.cloud.fetch_ai_quota_status')
    def test_cloud_tick_on_flush(self, mock_status, mock_tick) -> None:
        os.environ.pop('KRYPTAIM_AI_FREE_QUOTA_CLOUD_OFF', None)
        os.environ.pop('AIMSYNC_AI_FREE_QUOTA_CLOUD_OFF', None)
        mock_status.return_value = ({
            'ok': True,
            'date': date.today().isoformat(),
            'limit_seconds': 7200,
            'used_seconds': 0,
            'remaining_seconds': 7200,
            'exhausted': False,
        }, None)
        mock_tick.return_value = ({
            'ok': True,
            'date': date.today().isoformat(),
            'limit_seconds': 7200,
            'used_seconds': 45,
            'remaining_seconds': 7155,
            'exhausted': False,
        }, None)
        with patch.object(qmod, '_usage_path', return_value=self._usage):
            mgr = self._manager(limit_minutes=120)
            mgr.sync_engine_state(True)
            mgr._session_started = qmod.time.monotonic() - 45
            mgr.sync_engine_state(False)
        mock_tick.assert_called()
        self.assertAlmostEqual(mgr.total_used_seconds(), 45.0, places=0)


if __name__ == '__main__':
    unittest.main()
