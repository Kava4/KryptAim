"""Seal/unseal protected source blobs (stdlib only)."""

from __future__ import annotations

import hashlib
import os
import zlib

# Project seal material — not the plaintext sources, only the encryption salt input.
_MATERIAL = bytes([
    0x41, 0x53, 0x2d, 0x50, 0x52, 0x4f, 0x54, 0x2d,
    0x56, 0x31, 0x2d, 0x43, 0x4f, 0x52, 0x45, 0x2d,
    0x39, 0x38, 0x32, 0x31, 0x37, 0x34, 0x36, 0x33,
])


def _key(extra: bytes = b'') -> bytes:
    env = os.environ.get('AIMSYNC_SEAL_KEY', '').strip().encode('utf-8')
    seed = _MATERIAL + env + extra
    return hashlib.pbkdf2_hmac('sha256', seed, b'aimsync-seal', 120_000, dklen=32)


def seal_bytes(data: bytes) -> bytes:
    compressed = zlib.compress(data, level=9)
    key = _key()
    out = bytearray(compressed)
    for i, byte in enumerate(out):
        out[i] = byte ^ key[i % len(key)]
    return bytes(out)


def unseal_bytes(payload: bytes) -> bytes:
    key = _key()
    raw = bytearray(payload)
    for i, byte in enumerate(raw):
        raw[i] = byte ^ key[i % len(key)]
    return zlib.decompress(bytes(raw))
