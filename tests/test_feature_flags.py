"""Feature flag resolution."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.core import feature_flags as ff


class FeatureFlagsTests(unittest.TestCase):
    def tearDown(self) -> None:
        ff.invalidate_remote_config_cache()
        os.environ.pop('AIMSYNC_AI_PREMIUM_ONLY', None)
        os.environ.pop('AIMSYNC_AI_FREE', None)

    def test_default_ai_is_free(self) -> None:
        with patch.object(ff, 'fetch_remote_config', return_value={}):
            self.assertFalse(ff.ai_premium_required(refresh=True))

    def test_env_forces_premium(self) -> None:
        os.environ['AIMSYNC_AI_PREMIUM_ONLY'] = '1'
        self.assertTrue(ff.ai_premium_required())

    def test_remote_config_locks_ai(self) -> None:
        with patch.object(ff, 'fetch_remote_config', return_value={'ai_premium_only': True}):
            self.assertTrue(ff.ai_premium_required(refresh=True))


if __name__ == '__main__':
    unittest.main()
