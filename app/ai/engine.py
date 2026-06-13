"""AI loop — NDI capture, async YOLO, trigger (protected — sealed at runtime)."""

from app.protected.loader import bind_protected_module

bind_protected_module(__name__)
