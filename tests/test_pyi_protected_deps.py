"""PyInstaller must bundle deps only referenced from sealed modules."""

from __future__ import annotations

from app.protected.pyi_deps import protected_hidden_imports


def test_protected_hidden_imports_includes_cloud():
    imports = protected_hidden_imports()
    assert 'app.core.cloud' in imports


def test_protected_hidden_imports_excludes_sealed_stubs():
    imports = protected_hidden_imports()
    assert 'app.core.licensing' not in imports
    assert 'app.recoil.engine' not in imports
