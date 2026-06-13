"""Sealed core modules (recoil + AI logic)."""

from app.protected.loader import ProtectedModuleError, bind_protected_module

__all__ = ['ProtectedModuleError', 'bind_protected_module']
