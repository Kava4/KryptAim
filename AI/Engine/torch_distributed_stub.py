"""
PyInstaller: stub torch.distributed.rpc only when it is missing from the bundle.

Real torch.distributed.algorithms.join must be bundled (see build_app.py).
"""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import importlib.util
import sys
import types

_RPC = 'torch.distributed.rpc'

_RPC_ATTRS = frozenset(
    {
        'is_available',
        'init_rpc',
        'shutdown',
        'get_worker_info',
        'remote',
        'rpc_sync',
        'rpc_async',
        'RRef',
    }
)


def install() -> None:
    if not getattr(sys, 'frozen', False):
        return
    if getattr(install, '_done', False):
        return
    install._done = True  # type: ignore[attr-defined]

    finder = _RpcFallbackFinder()
    if finder not in sys.meta_path:
        sys.meta_path.append(finder)


def _should_stub_rpc_module(name: str) -> bool:
    if name == _RPC:
        return True
    if not name.startswith(_RPC + '.'):
        return False
    leaf = name.rsplit('.', 1)[-1]
    return leaf not in _RPC_ATTRS


def _make_rpc_stub(name: str) -> types.ModuleType:
    existing = sys.modules.get(name)
    if existing is not None:
        return existing

    mod = types.ModuleType(name)
    mod.__path__ = []  # type: ignore[attr-defined]
    mod.__package__ = name
    if name == _RPC:
        mod.is_available = lambda: False  # type: ignore[attr-defined]
        mod.is_initialized = lambda: False  # type: ignore[attr-defined]

    parent_name, _, child = name.rpartition('.')
    if parent_name and parent_name in sys.modules:
        setattr(sys.modules[parent_name], child, mod)

    sys.modules[name] = mod
    return mod


def _ensure_rpc_chain(name: str) -> types.ModuleType:
    parts = name.split('.')
    for i in range(3, len(parts) + 1):
        full = '.'.join(parts[:i])
        if full.startswith(_RPC):
            _make_rpc_stub(full)
    return sys.modules[name]


class _RpcFallbackFinder(importlib.abc.MetaPathFinder):
    """Last-chance finder: use real rpc if present, else safe stub."""

    def find_spec(self, fullname: str, path, target=None):  # noqa: ANN001
        if not _should_stub_rpc_module(fullname):
            return None

        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is not None:
            return spec

        return importlib.util.spec_from_loader(fullname, _RpcStubLoader(fullname))


class _RpcStubLoader(importlib.abc.Loader):
    def __init__(self, name: str) -> None:
        self._name = name

    def create_module(self, spec):  # noqa: ANN001
        return _ensure_rpc_chain(spec.name)

    def exec_module(self, module: types.ModuleType) -> None:
        return None


def attach_to_torch() -> None:
    """If distributed loaded but rpc is broken, patch a safe rpc stub."""
    dist = sys.modules.get('torch.distributed')
    if dist is None:
        return
    rpc = sys.modules.get(_RPC)
    if rpc is None or not callable(getattr(rpc, 'is_available', None)):
        rpc = _make_rpc_stub(_RPC)
        setattr(dist, 'rpc', rpc)
