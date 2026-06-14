"""KryptAim — entry point (web UI + workers)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault('YOLO_AUTOINSTALL', 'false')

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

if getattr(sys, 'frozen', False):
    from app.bootstrap.runtime import patch_sys_path_for_runtime

    patch_sys_path_for_runtime()


def main() -> int:
    from app.core.runtime import dev_mode_enabled
    from app.web.runner import run_web_app

    try:
        return run_web_app(dev_mode=dev_mode_enabled())
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
