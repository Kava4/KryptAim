"""Export AimSync source tree into a single UTF-8 text file (offline backup)."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / 'AimSync_CLEAN_SOURCE.txt'

INCLUDE_SUFFIXES = {
    '.py', '.html', '.md', '.txt', '.bat', '.cfg', '.json', '.yml', '.yaml',
    '.js', '.css', '.toml', '.ini',
}

SKIP_DIR_NAMES = {
    '.git',
    '.cursor',
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    '.ruff_cache',
    '.venv',
    'venv',
    'aimsync-venv',
    'build-venv',
    'build',
    'dist',
    'build-helper',
    'release',
    '.beta-data',
    '.aimsync-data',
    'htmlcov',
    'node_modules',
    'Aimmy-Makcu',
    'vendor-ai-reference',
    'AI/HelperApp',
    'AimSync-PC',
    'AimSync-PC-stage',
    'AimSyncBeta-PC',
    'AimSyncBeta-PC-stage',
}

SKIP_FILE_NAMES = {
    'AimSync_CLEAN_SOURCE.txt',
    'config.json',
}

MAX_FILE_BYTES = 512 * 1024


def should_include(path: Path) -> bool:
    if path.name in SKIP_FILE_NAMES:
        return False
    if path.suffix.lower() not in INCLUDE_SUFFIXES:
        return False
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return False
    except OSError:
        return False
    return True


def iter_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if should_include(path):
            files.append(path)
    return sorted(files, key=lambda p: str(p).lower())


def export_clean_source(out_path: Path) -> tuple[int, int]:
    files = iter_source_files(ROOT)
    lines: list[str] = [
        'AimSync — clean source export',
        f'Generated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}',
        f'Root: {ROOT}',
        'Note: No GitHub remote. Local/offline distribution only.',
        f'Files: {len(files)}',
        '=' * 72,
        '',
    ]
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            text = path.read_text(encoding='utf-8', errors='replace')
        lines.append(f'===== FILE: {rel} =====')
        lines.append(text.rstrip())
        lines.append('')
        lines.append('=' * 72)
        lines.append('')
    out_path.write_text('\n'.join(lines), encoding='utf-8')
    return len(files), out_path.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser(description='Export AimSync source to one .txt file')
    parser.add_argument('-o', '--output', type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    count, size = export_clean_source(args.output)
    print(f'Wrote {count} files -> {args.output} ({size:,} bytes)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
