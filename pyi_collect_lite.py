"""PyInstaller — slim bundle (recoil + UI; AI via AppData runtime)."""

import flask  # noqa: F401
import makcu  # noqa: F401
import makcu.errors  # noqa: F401

import app.recoil.engine  # noqa: F401
import app.protected.pyi_deps  # noqa: F401 — sealed-module deps for PyInstaller
import web.app  # noqa: F401
