"""Torch import bootstrap for PyInstaller frozen builds."""

from __future__ import annotations

import sys

from AI.Engine.torch_distributed_stub import attach_to_torch, install as install_distributed_stub


def install_torch_boot() -> None:
    if not getattr(sys, 'frozen', False):
        return
    if getattr(install_torch_boot, '_done', False):
        return
    install_torch_boot._done = True  # type: ignore[attr-defined]

    install_distributed_stub()

    import builtins

    real_import = builtins.__import__

    def hooked_import(name, globals=None, locals=None, fromlist=(), level=0):
        module = real_import(name, globals, locals, fromlist, level)
        if name == 'torch' or (isinstance(name, str) and name.startswith('torch.')):
            attach_to_torch()
        return module

    if not getattr(install_torch_boot, '_hooked', False):
        builtins.__import__ = hooked_import
        install_torch_boot._hooked = True  # type: ignore[attr-defined]
