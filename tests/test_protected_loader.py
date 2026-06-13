"""Protected module loader loads sealed blobs when app/_src is absent."""

from __future__ import annotations

import importlib
from pathlib import Path


def test_sealed_recoil_engine_exports_run_recoil():
    mod = importlib.import_module('app.recoil.engine')
    assert callable(getattr(mod, 'run_recoil', None))


def test_sealed_weapon_data_has_patterns():
    from app.recoil.weapon_data import WeaponData

    pattern = WeaponData.get_pattern('assault_rifle')
    assert pattern and len(pattern) > 0


def test_sealed_licensing_exports_validate():
    mod = importlib.import_module('app.core.licensing')
    assert callable(getattr(mod, 'validate_license', None))


def test_sealed_blobs_exist_in_repo():
    sealed = Path(__file__).resolve().parents[1] / 'app' / 'protected' / 'sealed'
    assert any(sealed.glob('*.bin'))


def test_manifest_fallback_without_manifest_file(monkeypatch, tmp_path):
    from app.protected import loader as pl

    fake = tmp_path / 'protected'
    (fake / 'sealed').mkdir(parents=True)
    monkeypatch.setattr(pl, '_protected_dir', lambda: fake)
    assert 'recoil/engine.py' in pl._manifest_modules()
