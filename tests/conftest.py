"""Test bootstrap — makcu SDK optional on CI/dev machines."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

if 'makcu' not in sys.modules:
    stub = ModuleType('makcu')
    stub.MouseButton = MagicMock()
    stub.create_controller = MagicMock(return_value=None)
    sys.modules['makcu'] = stub
