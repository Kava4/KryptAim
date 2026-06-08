"""Create alternative mouse input backends (non-Makcu)."""

from __future__ import annotations

from Input.backends.arduino import ArduinoInput
from Input.backends.ghub import GhubInput
from Input.backends.kmbox_net import KmboxNetInput
from Input.backends.razer import RazerInput
from Input.backends.win32 import Win32Input
from Input.protocol import MouseInputBackend


def create_backend(method: str, config: dict) -> MouseInputBackend:
    key = (method or 'win32').strip().lower()

    if key == 'win32':
        backend = Win32Input()
        backend.connect()
        return backend

    if key == 'ghub':
        backend = GhubInput(dll_path=str(config.get('ghub_dll_path') or ''))
        backend.connect()
        return backend

    if key == 'arduino':
        backend = ArduinoInput(
            port=str(config.get('arduino_port') or 'COM0'),
            baudrate=int(config.get('arduino_baudrate') or 115200),
            protocol='legacy',
            enable_keys=bool(config.get('arduino_enable_keys')),
        )
        backend.connect()
        return backend

    if key == 'rp2350':
        backend = ArduinoInput(
            port=str(config.get('rp2350_port') or config.get('arduino_port') or 'COM0'),
            baudrate=int(config.get('rp2350_baudrate') or 115200),
            protocol='legacy',
        )
        backend.name = 'rp2350'
        backend.connect()
        return backend

    if key == 'teensy41':
        backend = ArduinoInput(
            port=str(config.get('arduino_port') or 'COM0'),
            baudrate=int(config.get('arduino_baudrate') or 115200),
            protocol='teensy41',
        )
        backend.name = 'teensy41'
        backend.connect()
        return backend

    if key == 'kmbox_net':
        backend = KmboxNetInput(
            ip=str(config.get('kmbox_net_ip') or '10.42.42.42'),
            port=str(config.get('kmbox_net_port') or '1984'),
            uuid=str(config.get('kmbox_net_uuid') or 'DEADC0DE'),
        )
        backend.connect()
        return backend

    if key == 'kmbox_a':
        # KMBOX A uses HID — fallback to Win32 until dedicated HID backend is added.
        backend = Win32Input()
        backend.name = 'kmbox_a'
        backend.connect()
        return backend

    if key == 'razer':
        backend = RazerInput(dll_path=str(config.get('razer_dll_path') or ''))
        backend.connect()
        return backend

    backend = Win32Input()
    backend.connect()
    return backend
