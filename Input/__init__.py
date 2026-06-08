"""Alternative mouse input backends (non-Makcu). Makcu stays in Makcu/."""

from Input.methods import resolve_mouse_input_method, use_alt_input
from Input.router import input_router

__all__ = [
    'input_router',
    'resolve_mouse_input_method',
    'use_alt_input',
]
