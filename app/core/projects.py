"""GitHub projects showcase for the /projects page."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from app.core.github import get_json

logger = logging.getLogger('AimSync.projects')

_CACHE: dict[str, Any] = {'at': 0.0, 'projects': [], 'error': None}
_CACHE_TTL = 600.0
_CONFIG_PATHS = (
    Path(__file__).resolve().parents[2] / 'release' / 'projects.json',
    Path(__file__).resolve().parents[1] / 'release' / 'projects.json',
)


def _load_config() -> dict[str, Any]:
    for path in _CONFIG_PATHS:
        if not path.is_file():
            continue
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception as exc:
            logger.warning('Could not read %s: %s', path, exc)
    return {
        'sources': [{'type': 'org', 'name': os.environ.get('AIMSYNC_GITHUB_ORG', 'AimSyncCore')}],
        'exclude_repos': ['AimSync'],
        'exclude_forks': True,
        'featured': [],
    }


def _repo_items(source_type: str, name: str) -> list[dict[str, Any]]:
    url = f'https://api.github.com/{source_type}s/{name}/repos?sort=updated&per_page=100'
    data, err = get_json(url)
    if err or not isinstance(data, list):
        logger.warning('GitHub %s list failed for %s: %s', source_type, name, err)
        return []
    return [item for item in data if isinstance(item, dict)]


def _fetch_repo(full_name: str) -> dict[str, Any] | None:
    url = f'https://api.github.com/repos/{full_name}'
    data, err = get_json(url)
    if err or not isinstance(data, dict):
        logger.warning('GitHub repo lookup failed for %s: %s', full_name, err)
        return None
    return data


def _normalize_repo(raw: dict[str, Any], *, featured: dict[str, Any] | None = None) -> dict[str, Any]:
    repo_slug = str(raw.get('full_name') or '')
    short_name = str(raw.get('name') or '')
    api_description = str(raw.get('description') or '').strip()
    featured = featured or {}

    display_name = str(featured.get('name') or short_name).strip()
    description = str(featured.get('description') or api_description).strip() or 'No description yet.'
    demo_url = featured.get('demo_url')
    tags = featured.get('tags')
    if not isinstance(tags, list):
        tags = list(raw.get('topics') or [])

    return {
        'name': display_name,
        'repo_name': short_name,
        'full_name': repo_slug,
        'description': description,
        'url': str(raw.get('html_url') or f'https://github.com/{repo_slug}'),
        'demo_url': str(demo_url).strip() if demo_url else None,
        'stars': int(raw.get('stargazers_count') or 0),
        'language': str(raw.get('language') or '').strip() or None,
        'updated_at': str(raw.get('updated_at') or ''),
        'topics': [str(item) for item in tags if str(item).strip()],
        'fork': bool(raw.get('fork')),
        'featured': bool(featured),
        'order': int(featured.get('order') or 999),
    }


def _featured_entries(config: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for item in config.get('featured', []):
        if not isinstance(item, dict):
            continue
        repo = str(item.get('repo') or '').strip()
        if repo:
            entries.append(item)
    entries.sort(key=lambda row: int(row.get('order') or 999))
    return entries


def _fallback_from_featured(featured: dict[str, Any]) -> dict[str, Any]:
    repo = str(featured.get('repo') or '').strip()
    short_name = repo.split('/')[-1] if repo else 'project'
    return {
        'name': short_name,
        'full_name': repo,
        'description': featured.get('description') or '',
        'html_url': f'https://github.com/{repo}' if repo else '',
        'stargazers_count': 0,
        'language': None,
        'updated_at': '',
        'topics': featured.get('tags') or [],
        'fork': False,
    }


def list_github_projects(*, refresh: bool = False) -> dict[str, Any]:
    now = time.time()
    if not refresh and _CACHE['projects'] and (now - float(_CACHE['at'])) < _CACHE_TTL:
        return {'success': True, 'projects': list(_CACHE['projects']), 'cached': True}

    config = _load_config()
    exclude_names = {str(item).strip().lower() for item in config.get('exclude_repos', [])}
    exclude_forks = bool(config.get('exclude_forks', True))
    seen: set[str] = set()
    projects: list[dict[str, Any]] = []
    api_by_full_name: dict[str, dict[str, Any]] = {}

    for source in config.get('sources', []):
        if not isinstance(source, dict):
            continue
        source_type = str(source.get('type') or 'org').strip().lower()
        name = str(source.get('name') or '').strip()
        if source_type not in {'org', 'user'} or not name:
            continue
        for raw in _repo_items(source_type, name):
            full_name = str(raw.get('full_name') or '')
            if full_name:
                api_by_full_name[full_name] = raw

    for featured in _featured_entries(config):
        full_name = str(featured.get('repo') or '').strip()
        if not full_name or full_name in seen:
            continue
        repo_name = full_name.split('/')[-1].lower()
        if repo_name in exclude_names:
            continue
        raw = api_by_full_name.get(full_name) or _fetch_repo(full_name) or _fallback_from_featured(featured)
        if exclude_forks and raw.get('fork'):
            continue
        seen.add(full_name)
        projects.append(_normalize_repo(raw, featured=featured))

    for full_name, raw in api_by_full_name.items():
        if full_name in seen:
            continue
        repo_name = str(raw.get('name') or '').lower()
        if repo_name in exclude_names:
            continue
        if exclude_forks and raw.get('fork'):
            continue
        seen.add(full_name)
        projects.append(_normalize_repo(raw))

    projects.sort(
        key=lambda item: (
            0 if item.get('featured') else 1,
            int(item.get('order') or 999),
            item.get('stars', 0),
            item.get('updated_at', ''),
        ),
    )
    _CACHE['at'] = now
    _CACHE['projects'] = projects
    _CACHE['error'] = None
    return {'success': True, 'projects': projects, 'cached': False}
