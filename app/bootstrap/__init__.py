"""First-run / AppData runtime for slim frozen builds."""

from app.bootstrap.runtime import (
    bootstrap_status,
    install_runtime,
    is_ai_available,
    patch_sys_path_for_runtime,
    runtime_dir,
)

__all__ = [
    'bootstrap_status',
    'install_runtime',
    'is_ai_available',
    'patch_sys_path_for_runtime',
    'runtime_dir',
]
